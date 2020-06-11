#!/usr/bin/env python

from aiida.engine import WorkChain, if_, while_
from aiida.orm import load_node, Bool, Float, Str, Int, Dict, StructureData, KpointsData
from aiida_twinpy.common.structure import get_twinboundary_structure
from aiida_twinpy.common.utils import collect_vasp_results, reset_isif
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
        >>>     cls.create_sheared_structures,
        >>>     if_(cls.dry_run)(
        >>>         cls.terminate_dry_run,
        >>>         ).else_(
        >>>         cls.run_relax,
        >>>         cls.create_energies,
        >>>         ),
        >>>     if_(cls.is_phonon)(
        >>>         cls.run_phonon,
        >>>         ),
        >>>     cls.terminate
        >>> )
    """

    @classmethod
    def define(cls, spec):
        super(TwinBoundaryRelaxWorkChain, cls).define(spec)
        spec.input('calculator_settings', valid_type=Dict, required=True)
        spec.input('relax_times', valid_type=Int, required=True)
        spec.input('computer', valid_type=Str, required=True)
        spec.input('twinboundary_relax_conf', valid_type=Dict, required=True)
        spec.input('structure', valid_type=StructureData, required=True)

        spec.outline(
            cls.check_initial_isif_is_two,
            cls.setup,
            while_(cls.run_next_relax)(
                cls.run_relax_isif2,
                cls.run_relax_isif7,
                ),
            cls.terminate,
        )

        spec.output('strain', valid_type=Float, required=True)
        spec.output('twinboundary_summary', valid_type=Dict, required=True)
        spec.output('vasp_results', valid_type=Dict, required=False)
        # spec.exit_code(100, 'ERROR_ISIF_IS_NOT_TWO',
        #                message='initial isif settings is not two')

    def terminate(self):
        self.report('#-----------------------------------------------------')
        self.report('# TwinBoundaryRelaxWorkChain has finished successfully')
        self.report('#-----------------------------------------------------')
        self.report('all jobs have finished')
        self.report('terminate ShearWorkChain')

    def check_initial_isif_is_two(self):
        rlx_settings = self.inputs.calculator_settings.get_dict()['relax']['relax_conf']
        run_mode = [rlx_settings['positions'],
                    rlx_settings['volume'],
                    rlx_settings['shape']]
        if run_mode != [True, False, False]:
            raise ValueError("isif is not 2")
            # self.exit_codes.ERROR_ISIF_IS_NOT_TWO

    def setup(self):
        structure = get_twinboundary_structure(self.inputs.structure,
                                               self.inputs.twinboundary_relax_conf)
        self.ctx.relax_step = 0
        self.ctx.structure = structure
        self.ctx.calculator_settings = self.inputs.calculator_settings
        self.ctx.relax_pk = None

    def run_next_relax(self):
        return self.ctx.relax_step < self.inputs.relax_times.value

    def run_relax_isif2(self):
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
        self.report('{} relax workflow has submitted, pk: {}'
                .format(tb_relax_label, future.pk))
        self.to_context(**{tb_relax_label: future})
        self.ctx.relax_pk = future.pk

    def run_relax_isif7(self):
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
        self.report(self.ctx.calculator_settings.get_dict())
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
        self.report('{} relax workflow has submitted, pk: {}'
                .format(tb_relax_label, future.pk))
        self.to_context(**{tb_relax_label: future})
        self.ctx.relax_pk = future.pk
        self.ctx.relax_step += 1

    # def create_energies(self):
    #     self.report('#----------------')
    #     self.report('# collect results')
    #     self.report('#----------------')
    #     vasp_results = {}
    #     for i in range(self.ctx.total_structures):
    #         label = 'twinboundary_%03d' % i
    #         vasp_label = 'vasp_' + label
    #         vasp_results[vasp_label] = self.ctx[vasp_label].outputs.misc
    #     return_vals = collect_vasp_results(**vasp_results)
    #     self.out('vasp_results', return_vals['vasp_results'])
