#!/usr/bin/env python

from aiida.engine import WorkChain, if_
from aiida.orm import Bool, Float, Str, Int, Dict, StructureData, KpointsData
from aiida_twinpy.common.structure import get_twinboundary_structures
from aiida_twinpy.common.utils import collect_vasp_results
from aiida_twinpy.common.builder import get_calcjob_builder

class TwinBoundaryWorkChain(WorkChain):
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
        super(TwinBoundaryWorkChain, cls).define(spec)
        spec.input('calculator_settings', valid_type=Dict, required=True)
        spec.input('computer', valid_type=Str, required=True)
        spec.input('dry_run', valid_type=Bool, required=False,
                   default=lambda: Bool(False))
        spec.input('is_phonon', valid_type=Bool, required=True)
        spec.input('phonon_conf', valid_type=Dict, required=False)
        spec.input('twinboundary_conf', valid_type=Dict, required=True)
        spec.input('structure', valid_type=StructureData, required=True)

        spec.outline(
            cls.create_twinboundary_structures,
            if_(cls.dry_run)(
                cls.terminate_dry_run,
                ).else_(
                cls.run_vasp,
                cls.create_energies,
                if_(cls.is_phonon)(
                    cls.run_phonon,
                    ),
                cls.terminate
                )
        )

        spec.output('strain', valid_type=Float, required=True)
        spec.output('twinboundary_summary', valid_type=Dict, required=True)
        spec.output('vasp_results', valid_type=Dict, required=False)

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

    def create_twinboundary_structures(self):
        self.report('#-------------------------------')
        self.report('# create twinboundary structures')
        self.report('#-------------------------------')
        return_vals = get_twinboundary_structures(
                self.inputs.structure,
                self.inputs.twinboundary_conf)
        self.out('strain', return_vals['strain'])
        self.out('twinboundary_summary', return_vals['twinboundary_summary'])
        self.ctx.total_structures = return_vals['total_structures'].value
        self.ctx.twinboundaries = {}
        for i in range(self.ctx.total_structures):
            label = 'twinboundary_%03d' % i
            self.ctx.twinboundaries[label] = return_vals[label]

    def run_vasp(self):
        self.report('#------------------------------')
        self.report('# run vasp calculations')
        self.report('#------------------------------')
        for i in range(self.ctx.total_structures):
            label = 'twinboundary_%03d' % i
            vasp_label = 'vasp_' + label
            vasp_description = 'vasp_' + label
            builder = get_calcjob_builder(
                    label=vasp_label,
                    description=vasp_description,
                    calc_type='vasp',
                    computer=self.inputs.computer,
                    structure=self.ctx.twinboundaries[label],
                    calculator_settings=self.inputs.calculator_settings
                    )
            future = self.submit(builder)
            self.report('{} vasp calcfunction has submitted, pk: {}'
                    .format(vasp_label, future.pk))
            self.to_context(**{vasp_label: future})

    def create_energies(self):
        self.report('#----------------')
        self.report('# collect results')
        self.report('#----------------')
        vasp_results = {}
        for i in range(self.ctx.total_structures):
            label = 'twinboundary_%03d' % i
            vasp_label = 'vasp_' + label
            vasp_results[vasp_label] = self.ctx[vasp_label].outputs.misc
        return_vals = collect_vasp_results(**vasp_results)
        self.out('vasp_results', return_vals['vasp_results'])

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
