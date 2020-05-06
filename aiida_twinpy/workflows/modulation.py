#!/usr/bin/env python

from aiida.engine import WorkChain, if_
from aiida.orm import Bool, Float, Str, Int, Dict, StructureData, KpointsData
from aiida_twinpy.common.structure import get_modulation_structures
from aiida_twinpy.common.utils import collect_vasp_results
from aiida_twinpy.common.builder import get_calcjob_builder_for_modulation

class ModulationWorkChain(WorkChain):
    """
    WorkChain for adding modulation and relax

    Args:
        calculator_settings: (Dict) for more detail,
                             see common.builder.get_calcjob_builder
        computer: (Str) required=True
        dry_run: (Bool) required=True, If True,
                 just make sheared structure, not run relax
        shuffle_conf: (Dict) shuffle config, for more detail see Examples
        phonon_pk: (int) required=True, phonon workchain pk

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
        super(ModulationWorkChain, cls).define(spec)
        spec.input('computer', valid_type=Str, required=True)
        spec.input('dry_run', valid_type=Bool, required=False,
                   default=lambda: Bool(False))
        spec.input('modulation_conf', valid_type=Dict, required=True)

        spec.outline(
            cls.create_modulation_structures,
            if_(cls.dry_run)(
                cls.terminate_dry_run,
                ).else_(
                cls.run_vasp,
                cls.create_energies,
                cls.terminate
                )
        )

        spec.output('modulation_summary', valid_type=Dict, required=True)
        spec.output('vasp_results', valid_type=Dict, required=False)

    def dry_run(self):
        return self.inputs.dry_run

    def terminate_dry_run(self):
        self.report('#----------------------')
        self.report('# dry run has activated')
        self.report('#----------------------')
        self.report('terminate ModulationWorkChain')

    def terminate(self):
        self.report('#-------------------------------------------')
        self.report('# ModulationWorkChain has finished successfully')
        self.report('#-------------------------------------------')
        self.report('all jobs have finished')
        self.report('terminate ModulationWorkChain')

    def create_modulation_structures(self):
        self.report('#-----------------------------')
        self.report('# create modulation structures')
        self.report('#-----------------------------')
        return_vals = get_modulation_structures(
                self.inputs.modulation_conf)
        self.ctx.modulations = {}
        for i in range(len(self.inputs.modulation_conf['phonon_modes'])):
            label = 'modulation_%03d' % (i+1)
            self.ctx.modulations[label] = return_vals[label]

    def run_vasp(self):
        self.report('#-----------------------')
        self.report('# run vasp calculations')
        self.report('#-----------------------')
        for i in range(len(self.inputs.modulation_conf['phonon_modes'])):
            label = 'modulation_%03d' % (i+1)
            vasp_label = 'vasp_' + label
            vasp_description = 'vasp_' + label
            builder = get_calcjob_builder_for_modulation(
                    label=vasp_label,
                    description=vasp_description,
                    computer=self.inputs.computer,
                    structure=self.ctx.modulations[label],
                    modulation_conf=self.inputs.modulation_conf,
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
        for i in range(len(self.inputs.shuffle_conf['phonon_modes'])):
            label = 'modulation_%03d' % (i+1)
            vasp_label = 'vasp_' + label
            vasp_results[vasp_label] = self.ctx[vasp_label].outputs.misc
        return_vals = collect_vasp_results(**vasp_results)
        self.out('vasp_results', return_vals['vasp_results'])
