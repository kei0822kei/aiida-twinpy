#!/usr/bin/env python

from aiida.engine import WorkChain, while_
from aiida.orm import Bool, Float, Int, Str, Dict, load_node
from aiida_twinpy.common.structure import get_twinboundary_shear_structure
from aiida_twinpy.common.utils import store_shear_ratios
from aiida_twinpy.common.kpoints import (get_kpoints_interval,
                                         get_kpoints_from_interval)
from aiida_twinpy.common.builder import (
        get_calcjob_builder_for_twinboundary_shear)


class TwinBoundaryShearWorkChain(WorkChain):
    """
    WorkChain for add shear toward relaxed twinboundary structure

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

        >>> twinboundary_conf = Dict(dict={
        >>>     'twinboundary_relax_pk': 11111,
        >>>     'additional_relax_pks': [11112, 11113],
        >>>     'shear_strain_ratios': [0.01, 0.02],
        >>>     })
        >>> kpoints_interval = Float(0.15)
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
        super(TwinBoundaryShearWorkChain, cls).define(spec)
        spec.input('computer', valid_type=Str, required=True)
        spec.input('twinboundary_shear_conf', valid_type=Dict, required=True)
        # spec.input('kpoints_interval', valid_type=Float, required=False,
        #            default=lambda: Float(-1.))

        spec.outline(
            cls.initialize,
            while_(cls.is_run_next_step)(
                cls.create_twinboundary_shear_structure,
                # cls.create_kpoints,
                cls.run_relax,
                cls.update_vals,
                ),
            cls.terminate
        )

        spec.output('relax_results', valid_type=Dict, required=False)

    # def extract_kpoints_interval_from_twinboudnary_relax(self):
    #     rlx = load_node(
    #         self.inputs.twinboundary_shear_conf['additional_relax_pks'][-1])
    #     structure = rlx.outputs.relax__structure
    #     kpoints = rlx.inputs.kpoints
    #     return_vals = get_kpoints_interval(structure=structure,
    #                                        kpoints=kpoints)
    #     return return_vals['interval']

    def initialize(self):
        # if self.inputs.kpoints_interval.value == -1.:
        #     self.ctx.interval = \
        #             self.extract_kpoints_interval_from_twinboudnary_relax()
        # else:
        #     self.ctx.interval = self.inputs.kpoints_interval

        return_vals = store_shear_ratios(self.inputs.twinboundary_shear_conf)
        num = len(self.inputs.twinboundary_shear_conf['shear_strain_ratios'])
        self.ctx.ratios = []
        for i in range(num):
            label = 'ratio_%03d' % (i+1)
            self.ctx.ratios.append(return_vals[label])
        self.ctx.previous_relax_pk = Int(
            self.inputs.twinboundary_shear_conf['additional_relax_pks'][-1])
        self.ctx.previous_shear_strain_ratio = None
        self.ctx.original_structure = None
        self.ctx.structure = None
        self.ctx.count = 0

    def update_vals(self):
        self.ctx.previous_shear_strain_ratio = self.ctx.ratios[self.ctx.count]
        self.ctx.count += 1

    def is_run_next_step(self):
        return self.ctx.count < len(self.ctx.ratios)

    def terminate(self):
        self.report('#-----------------------------------------------------')
        self.report('# TwinBoundaryShearWorkChain has finished successfully')
        self.report('#-----------------------------------------------------')
        self.report('all jobs have finished')
        self.report('terminate ShearWorkChain')

    def create_twinboundary_shear_structure(self):
        self.report('#-------------------------------------')
        self.report('# create twinboundary sheare structure')
        self.report('#-------------------------------------')

        if self.ctx.previous_shear_strain_ratio is None:
            return_vals = get_twinboundary_shear_structure(
                twinboundary_shear_conf=self.inputs.twinboundary_shear_conf,
                shear_strain_ratio=self.ctx.ratios[self.ctx.count],
                previous_relax_pk=self.ctx.previous_relax_pk)
        else:
            p_ratio = self.ctx.previous_shear_strain_ratio
            return_vals = get_twinboundary_shear_structure(
                twinboundary_shear_conf=self.inputs.twinboundary_shear_conf,
                shear_strain_ratio=self.ctx.ratios[self.ctx.count],
                previous_relax_pk=self.ctx.previous_relax_pk,
                previous_shear_strain_ratio=p_ratio,
                previous_original_structure=self.ctx.original_structure)

        self.ctx.original_structure = \
                return_vals['twinboundary_shear_structure_orig']
        self.ctx.structure = \
                return_vals['twinboundary_shear_structure']
        self.ctx.kpoints = \
                return_vals['kpoints']

    # def create_kpoints(self):
    #     self.report('#---------------')
    #     self.report('# create kpoints')
    #     self.report('#---------------')
    #     self.ctx.kpoints = get_kpoints_from_interval(
    #             structure=self.ctx.structure,
    #             interval=self.ctx.interval)

    def run_relax(self):
        self.report('#------------------------------')
        self.report('# run relax calculations')
        self.report('#------------------------------')
        label = 'twinboundary_shear_%03d' % (self.ctx.count+1)
        relax_label = 'rlx_' + label
        relax_description = relax_label + ", ratio: %f" \
                % self.ctx.ratios[self.ctx.count]
        builder = get_calcjob_builder_for_twinboundary_shear(
                label=relax_label,
                description=relax_description,
                computer=self.inputs.computer,
                structure=self.ctx.structure,
                kpoints=self.ctx.kpoints,
                twinboundary_shear_conf=self.inputs.twinboundary_shear_conf,
                )
        future = self.submit(builder)
        self.report('{} relax workflow has submitted, pk: {}'.format(
            relax_label, future.pk))
        self.to_context(**{relax_label: future})
        self.ctx.previous_relax_pk = Int(future.pk)

    # def create_energies(self):
    #     self.report('#----------------')
    #     self.report('# collect results')
    #     self.report('#----------------')
    #     rlx_results = {}
    #     for i in range(len(self.ctx.ratios)):
    #         label = 'twinboundaryshear_%03d' % i
    #         relax_label = 'rlx_' + label
    #         rlx_results[relax_label] = self.ctx[relax_label].outputs.misc
    #     return_vals = collect_twinboundary_shear_results(**rlx_results)
    #     self.out('relax_results', return_vals['relax_results'])

    # def run_phonon(self):
    #     self.report('#-----------')
    #     self.report('# run phonon')
    #     self.report('#-----------')
    #     for i, ratio in enumerate(self.ctx.ratios):
    #         label = 'twinboundaryshear_%03d' % i
    #         relax_label = 'rlx_' + label
    #         phonon_label = 'ph_' + label
    #         phonon_description = phonon_label + ", ratio: %f" % ratio
    #         structure = self.ctx[relax_label].outputs.relax__structure
    #         builder = get_calcjob_builder(
    #                 label=phonon_label,
    #                 description=phonon_description,
    #                 calc_type='phonon',
    #                 computer=self.inputs.computer,
    #                 structure=structure,
    #                 calculator_settings=self.inputs.calculator_settings
    #                 )
    #         future = self.submit(builder)
    #         self.report('{} phonopy workflow has submitted, pk: {}'
    #                 .format(phonon_label, future.pk))
    #         self.to_context(**{phonon_label: future})
