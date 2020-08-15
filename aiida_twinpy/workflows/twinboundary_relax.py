#!/usr/bin/env python

from aiida.engine import WorkChain, while_
from aiida.orm import load_node, Str, Int, Dict, StructureData
from aiida_twinpy.common.structure import get_twinboundary_structure
from aiida_twinpy.common.utils import reset_isif
from aiida_twinpy.common.builder import get_calcjob_builder


class TwinBoundaryRelaxWorkChain(WorkChain):
    """
    WorkChain for twin boundary of hexagonal metal

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

        >>> shear_conf = Dict(dict={
        >>>     'twinmode': '10-12',
        >>>     'grids': 5,
        >>>     'is_primitive': True,
        >>>     })
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
    """

    @classmethod
    def define(cls, spec):
        """
        Define.
        """
        super(TwinBoundaryRelaxWorkChain, cls).define(spec)
        spec.input('calculator_settings', valid_type=Dict, required=True)
        spec.input('relax_times', valid_type=Int, required=True)
        spec.input('computer', valid_type=Str, required=True)
        spec.input('twinboundary_relax_conf', valid_type=Dict, required=True)
        spec.input('structure', valid_type=StructureData, required=True)

        spec.outline(
            cls.check_initial_isif_is_two,
            cls.setup,
            cls.create_twinboudnary_structure,
            while_(cls.run_next_relax)(
                cls.run_relax_isif2,
                cls.run_relax_isif7,
                ),
            cls.extract_final_structure,
            cls.terminate,
        )

        spec.output('final_structure', valid_type=StructureData, required=True)
        spec.output('final_relax_pk', valid_type=Int, required=True)

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
            raise ValueError("isif is not 2")

    def setup(self):
        """
        Set initial values.
        """
        self.ctx.relax_step = 0
        self.ctx.calculator_settings = self.inputs.calculator_settings
        self.ctx.relax_pk = None

    def create_twinboudnary_structure(self):
        """
        Create twinboundary structure for relax.
        """
        return_vals = get_twinboundary_structure(
                self.inputs.structure,
                self.inputs.twinboundary_relax_conf)
        self.ctx.structure = return_vals['twinboundary']

    def run_next_relax(self):
        """
        Run relax until relax_times reached.
        """
        return self.ctx.relax_step < self.inputs.relax_times.value

    def run_relax_isif2(self):
        """
        Run relax with ISIF = 2.
        """
        self.report('#----------------------')
        self.report('# run relax with isif 2')
        self.report('#----------------------')
        if self.ctx.relax_step != 0:
            self.ctx.structure = \
                    load_node(self.ctx.relax_pk).outputs.relax__structure
            self.ctx.calculator_settings = \
                    reset_isif(self.ctx.calculator_settings,
                               Int(2))['calculator_settings']
            self.report('# previous relax pk is {}'.format(self.ctx.relax_pk))
            self.report('# structure pk is {}'.format(self.ctx.structure.pk))
            self.report(self.ctx.calculator_settings.get_dict())
        tb_relax_label = 'rlx_isif2_%03d' % (self.ctx.relax_step + 1)
        tb_relax_description = tb_relax_label
        builder = get_calcjob_builder(
                label=tb_relax_label,
                description=tb_relax_description,
                calc_type='relax',
                computer=self.inputs.computer,
                structure=self.ctx.structure,
                calculator_settings=self.ctx.calculator_settings
                )
        future = self.submit(builder)
        self.report('{} relax workflow has submitted, pk: {}'.format(
            tb_relax_label, future.pk))
        self.to_context(**{tb_relax_label: future})
        self.ctx.relax_pk = future.pk

    def run_relax_isif7(self):
        """
        Run relax with ISIF = 7.
        """
        self.report('#----------------------')
        self.report('# run relax with isif 7')
        self.report('#----------------------')
        self.ctx.structure = \
                load_node(self.ctx.relax_pk).outputs.relax__structure
        self.report('# previous relax pk is {}'.format(self.ctx.relax_pk))
        self.report('# structure pk is {}'.format(self.ctx.structure.pk))
        self.ctx.calculator_settings = \
                reset_isif(self.ctx.calculator_settings,
                           Int(7))['calculator_settings']
        tb_relax_label = 'rlx_isif7_%03d' % (self.ctx.relax_step + 1)
        tb_relax_description = tb_relax_label
        builder = get_calcjob_builder(
                label=tb_relax_label,
                description=tb_relax_description,
                calc_type='relax',
                computer=self.inputs.computer,
                structure=self.ctx.structure,
                calculator_settings=self.ctx.calculator_settings
                )
        future = self.submit(builder)
        self.report('{} relax workflow has submitted, pk: {}'.format(
            tb_relax_label, future.pk))
        self.to_context(**{tb_relax_label: future})
        self.ctx.relax_pk = future.pk
        self.ctx.relax_step += 1

    def extract_final_structure(self):
        self.report('#------------------------')
        self.report('# extract final structure')
        self.report('#------------------------')
        self.out('final_structure',
                 load_node(self.ctx.relax_pk).relax__structure)
        self.out('final_relax_pk', self.ctx.relax_pk)
