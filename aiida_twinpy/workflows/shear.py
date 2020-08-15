#!/usr/bin/env python

from aiida.engine import WorkChain, if_
from aiida.orm import Bool, Float, Str, Dict, StructureData, KpointsData
from aiida_twinpy.common.structure import get_shear_structures
from aiida_twinpy.common.utils import collect_relax_results
from aiida_twinpy.common.builder import get_calcjob_builder


class ShearWorkChain(WorkChain):
    """
    WorkChain for add shear from the original hexagonal twin mode

    Args:
        calculator_settings: (Dict) for more detail,
                             see common.builder.get_calcjob_builder
        computer: (Str) required=True
        dry_run: (Bool) required=True, If True,
                 just make shear structure, not run relax
        run_phonon: (Bool) required=True
        shear_conf: (Dict) shear config, for more detail see Examples
        structure: (StructureData) required=True, hexagonal structure

    Note:
        For more detail about shear_conf,
        see aiida_twinpy.common.structure.get_shear_structures.

    Todo:
    """

    @classmethod
    def define(cls, spec):
        super(ShearWorkChain, cls).define(spec)
        spec.input('calculator_settings', valid_type=Dict, required=True)
        spec.input('computer', valid_type=Str, required=True)
        spec.input('dry_run', valid_type=Bool, required=False,
                   default=lambda: Bool(False))
        spec.input('is_phonon', valid_type=Bool, required=True)
        spec.input('phonon_conf', valid_type=Dict, required=False)
        spec.input('shear_conf', valid_type=Dict, required=True)
        spec.input('structure', valid_type=StructureData, required=True)

        spec.outline(
            cls.create_shear_structures,
            if_(cls.dry_run)(
                cls.terminate_dry_run,
                ).else_(
                cls.run_relax,
                cls.create_energies,
                if_(cls.is_phonon)(
                    cls.run_phonon,
                    ),
                cls.terminate
                )
        )

        spec.output('parent', valid_type=StructureData, required=True)
        spec.output('gamma', valid_type=Float, required=True)
        spec.output('shear_ratios', valid_type=Dict, required=True)
        spec.output('relax_results', valid_type=Dict, required=False)

    def dry_run(self):
        return self.inputs.dry_run

    def is_phonon(self):
        return self.inputs.is_phonon

    def terminate_dry_run(self):
        self.report('#----------------------')
        self.report('# dry run has activated')
        self.report('#----------------------')
        self.report('terminate ShearWorkChain')

    def terminate(self):
        self.report('#-----------------------------------------')
        self.report('# ShearWorkChain has finished successfully')
        self.report('#-----------------------------------------')
        self.report('all jobs have finished')
        self.report('terminate ShearWorkChain')

    def create_shear_structures(self):
        """
        Create shear structures.
        """
        self.report('#------------------------')
        self.report('# create shear structures')
        self.report('#------------------------')
        return_vals = get_shear_structures(
                self.inputs.structure,
                self.inputs.shear_conf)
        self.out('gamma', return_vals['gamma'])
        self.out('shear_ratios', return_vals['shear_settings'])
        self.ctx.ratios = return_vals['shear_settings']['shear_ratios']
        self.ctx.shears = {}
        for i in range(len(self.ctx.ratios)):
            if i == 0:
                self.out('parent', return_vals['shear_000'])
            label = "shear_%03d" % i
            self.ctx.shears[label] = return_vals[label]

    def run_relax(self):
        self.report('#-----------------------')
        self.report('# run relax calculations')
        self.report('#-----------------------')
        for i, ratio in enumerate(self.ctx.ratios):
            label = 'shear_%03d' % i
            relax_label = 'rlx_' + label
            relax_description = relax_label + ", ratio: %f" % ratio
            builder = get_calcjob_builder(
                    label=relax_label,
                    description=relax_description,
                    calc_type='relax',
                    computer=self.inputs.computer,
                    structure=self.ctx.shears[label],
                    calculator_settings=self.inputs.calculator_settings
                    )
            future = self.submit(builder)
            self.report('{} relax workflow has submitted, pk: {}'
                    .format(relax_label, future.pk))
            self.to_context(**{relax_label: future})

    def create_energies(self):
        self.report('#----------------')
        self.report('# collect results')
        self.report('#----------------')
        rlx_results = {}
        for i in range(len(self.ctx.ratios)):
            label = 'shear_%03d' % i
            relax_label = 'rlx_' + label
            rlx_results[relax_label] = self.ctx[relax_label].outputs.misc
        return_vals = collect_relax_results(**rlx_results)
        self.out('relax_results', return_vals['relax_results'])

    def run_phonon(self):
        self.report('#-----------')
        self.report('# run phonon')
        self.report('#-----------')
        for i, ratio in enumerate(self.ctx.ratios):
            label = 'shear_%03d' % i
            relax_label = 'rlx_' + label
            phonon_label = 'ph_' + label
            phonon_description = phonon_label + ", ratio: %f" % ratio
            structure = self.ctx[relax_label].outputs.relax__structure
            builder = get_calcjob_builder(
                    label=phonon_label,
                    description=phonon_description,
                    calc_type='phonon',
                    computer=self.inputs.computer,
                    structure=structure,
                    calculator_settings=self.inputs.calculator_settings
                    )
            future = self.submit(builder)
            self.report('{} phonopy workflow has submitted, pk: {}'
                    .format(phonon_label, future.pk))
            self.to_context(**{phonon_label: future})
