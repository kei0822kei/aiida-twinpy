#!/usr/bin/env python

import warnings
from aiida.engine import WorkChain, while_
from aiida.orm import load_node, Str, Int, Dict, StructureData
from aiida_twinpy.common.structure import get_twinboundary_structure
from aiida_twinpy.common.utils import reset_isif
from aiida_twinpy.common.builder import get_calcjob_builder


class TwinBoundaryRelaxWorkChain(WorkChain):
    """
    WorkChain for twin boundary relax of hexagonal metal.

    Args:
        calculator_settings: (Dict) for more detail,
                             see common.builder.get_calcjob_builder
        computer: (Str) required=True
        dry_run: (Bool) required=True, If True,
                 just make sheared structure, not run relax
        run_phonon: (Bool) required=True
        shear_conf: (Dict) shear config, for more detail see Examples
        structure: (StructureData) required=True, hexagonal structure

    Examples:
        workflow is as follows

        >>> # outline
        >>> spec.outline(
        >>>     cls.check_initial_isif_is_two,
        >>>     cls.setup,
        >>>     cls.create_twinboudnary_structure,
        >>>     while_(cls.run_next_relax)(
        >>>         cls.run_relax_isif2,
        >>>         cls.run_relax_isif7,
        >>>         ),
        >>>     cls.extract_final_structure,
        >>>     cls.terminate,
        >>> )

    Todo:
        Use Error Code, not raise ValueError.
    """

    @classmethod
    def define(cls, spec):
        """
        Define.
        """
        super(TwinBoundaryRelaxWorkChain, cls).define(spec)
        spec.input('calculator_settings', valid_type=Dict, required=True)
        spec.input('computer', valid_type=Str, required=True)
        spec.input('twinboundary_conf', valid_type=Dict, required=True)
        spec.input('structure', valid_type=StructureData, required=True)

        spec.outline(
            cls.check_initial_isif_is_two,
            cls.create_twinboudnary_structure,
            cls.run_relax,
            cls.extract_final_structure,
            cls.terminate,
        )

        spec.output('final_structure', valid_type=StructureData, required=True)

    def terminate(self):
        """
        Terminate workflow.
        """
        self.report('#-----------------------------------------------------')
        self.report('# TwinBoundaryRelaxWorkChain has finished successfully')
        self.report('#-----------------------------------------------------')
        self.report('all jobs have finished')
        self.report('terminate ShearWorkChain')

    def check_initial_isif_is_two(self):
        """
        Check initial ISIF setting is 2, which allows to move only
        atom positions.
        """
        rlx_settings = \
            self.inputs.calculator_settings.get_dict()['relax']['relax_conf']
        run_mode = [rlx_settings['positions'],
                    rlx_settings['volume'],
                    rlx_settings['shape']]
        if run_mode != [True, False, False]:
            # raise ValueError("isif is not 2")
            warnings.warn("isif is not 2")   # not working, Future edited

    def create_twinboudnary_structure(self):
        """
        Create twinboundary structure for relax.
        """
        return_vals = get_twinboundary_structure(
                self.inputs.structure,
                self.inputs.twinboundary_conf)
        self.ctx.structure = return_vals['twinboundary']

    def run_relax(self):
        self.report('#-----------------------')
        self.report('# run relax calculations')
        self.report('#-----------------------')
        relax_label = 'relax_twinboundary'
        relax_description = 'relax_twinboundary'
        builder = get_calcjob_builder(
                label=relax_label,
                description=relax_description,
                calc_type='relax',
                computer=self.inputs.computer,
                structure=self.ctx.structure,
                calculator_settings=self.inputs.calculator_settings
                )
        future = self.submit(builder)
        self.report('{} relax workflow has submitted, pk: {}'
                .format(relax_label, future.pk))
        self.to_context(**{relax_label: future})
        self.ctx.relax = future

    def extract_final_structure(self):
        self.report('#------------------------')
        self.report('# extract final structure')
        self.report('#------------------------')
        self.out('final_structure',
                 self.ctx.relax.outputs.relax__structure)
