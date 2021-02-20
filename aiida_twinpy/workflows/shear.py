#!/usr/bin/env python

"""
This module provides ShearWorkChain.
"""

from aiida.engine import WorkChain, if_
from aiida.orm import Bool, Float, Str, Dict, StructureData
from aiida_twinpy.common.structure import get_shear_structures
from aiida_twinpy.common.utils import collect_relax_results
from aiida_twinpy.common.builder import get_calcjob_builder
from aiida_twinpy.common.kpoints import fix_kpoints


class ShearWorkChain(WorkChain):
    """
    WorkChain for adding twin shear from the original HCP struture.
    """

    @classmethod
    def define(cls, spec):
        super(ShearWorkChain, cls).define(spec)
        spec.input('calculator_settings',
                   valid_type=Dict,
                   required=True,
                   help="""
            Calculator settings.
            For more detail, see common.builder.get_calcjob_builder.
            """)
        spec.input('computer',
                   valid_type=Str,
                   required=True,
                   help="""
            Computer.
            """)
        spec.input('dry_run',
                   valid_type=Bool,
                   required=False,
                   default=lambda: Bool(False),
                   help="""
            If True, just make shear structure, not run relax.
            """)
        spec.input('is_phonon',
                   valid_type=Bool,
                   required=True,
                   help="""
            If True, run phonon calculation.
            """)
        spec.input('shear_conf',
                   valid_type=Dict,
                   required=True,
                   help="""
            Shear config. For more detail,
            see aiida_twinpy.common.structure.get_shear_structures.
            """)
        spec.input('structure',
                   valid_type=StructureData,
                   required=True,
                   help="""
            Input HCP structure.
            """)
        spec.input('use_kpoints_interval',
                   valid_type=Bool,
                   required=False,
                   default=lambda: Bool(False),
                   help="""
            If True, fix kpoints mesh for shear structure based on kpoints_conf
            specified with 'kpoints_conf'.
            """)
        spec.input('kpoints_conf',
                   valid_type=Dict,
                   required=False,
                   help="""
            Kpoints configuration for shear structure. This setting is called
            when 'use_kpoints_interval' is True. For detailed information,
            see aiida_twinpy.common.fix_kpoints.
            """)

        spec.outline(
            cls.initialize,
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

    def initialize(self):
        self.report("# ---------------------")
        self.report("# Start ShearWorkChain.")
        self.report("# ---------------------")

    def terminate_dry_run(self):
        self.report("# ----------------------")
        self.report("# Dry run has activated.")
        self.report("# ----------------------")
        self.report("Terminate ShearWorkChain.")

    def terminate(self):
        self.report("# -----------------------------------------")
        self.report("# ShearWorkChain has finished successfully.")
        self.report("# -----------------------------------------")
        self.report("All jobs have finished.")
        self.report("Terminate ShearWorkChain.")

    def create_shear_structures(self):
        """
        Create shear structures.
        """
        self.report("# ------------------------")
        self.report("# Create shear structures.")
        self.report("# ------------------------")
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
        self.report('# -----------------------')
        self.report('# Run relax calculations.')
        self.report('# -----------------------')
        self.ctx.calculator_settings = self.inputs.calculator_settings
        for i, ratio in enumerate(self.ctx.ratios):
            label = 'shear_%03d' % i
            relax_label = 'rlx_' + label
            relax_description = relax_label + ", ratio: %f" % ratio
            if self.inputs.use_kpoints_interval:
                return_vals = fix_kpoints(
                        calculator_settings=self.ctx.calculator_settings,
                        structure=self.ctx.shears[label],
                        kpoints_conf=self.inputs.kpoints_conf,
                        is_phonon=Bool(False))
                self.ctx.calculator_settings = \
                        return_vals['calculator_settings']
            builder = get_calcjob_builder(
                    label=relax_label,
                    description=relax_description,
                    calc_type='relax',
                    computer=self.inputs.computer,
                    structure=self.ctx.shears[label],
                    calculator_settings=self.ctx.calculator_settings
                    )
            future = self.submit(builder)
            self.report('{} relax workflow has submitted, pk: {}'.format(
                relax_label, future.pk))
            self.to_context(**{relax_label: future})

    def create_energies(self):
        self.report('#-----------------')
        self.report('# Collect results.')
        self.report('#-----------------')
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
        self.ctx.calculator_settings = self.inputs.calculator_settings
        for i, ratio in enumerate(self.ctx.ratios):
            label = 'shear_%03d' % i
            relax_label = 'rlx_' + label
            phonon_label = 'ph_' + label
            phonon_description = phonon_label + ", ratio: %f" % ratio
            structure = self.ctx[relax_label].outputs.relax__structure
            if self.inputs.use_kpoints_interval:
                return_vals = fix_kpoints(
                        calculator_settings=self.ctx.calculator_settings,
                        structure=structure,
                        kpoints_conf=self.inputs.kpoints_conf,
                        is_phonon=Bool(True))
                self.ctx.calculator_settings = \
                        return_vals['calculator_settings']
            builder = get_calcjob_builder(
                    label=phonon_label,
                    description=phonon_description,
                    calc_type='phonon',
                    computer=self.inputs.computer,
                    structure=structure,
                    calculator_settings=self.ctx.calculator_settings
                    )
            future = self.submit(builder)
            self.report('{} phonopy workflow has submitted, pk: {}'.format(
                phonon_label, future.pk))
            self.to_context(**{phonon_label: future})
