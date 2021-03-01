#!/usr/bin/env python

"""
This module provides TwinBoundaryRelaxWorkChain.
"""

from aiida.engine import WorkChain
from aiida.orm import Bool, Dict, Str, StructureData
from aiida_twinpy.common.structure import get_twinboundary_structure
from aiida_twinpy.common.builder import get_calcjob_builder
from aiida_twinpy.common.kpoints import fix_kpoints


class TwinBoundaryRelaxWorkChain(WorkChain):
    """
    WorkChain for twin boundary relax of hexagonal metal.

    Examples:
        Workflow is as follows,

        >>> # outline
        >>> spec.outline(
        >>>     cls.initialize,
        >>>     cls.check_initial_isif_is_two,
        >>>     cls.create_twinboudnary_structure,
        >>>     cls.run_relax,
        >>>     cls.extract_final_structure,
        >>>     cls.terminate,
        >>>     )

    Todo:
        Use Error Code, not raise ValueError.
    """

    @classmethod
    def define(cls, spec):
        """
        Define.
        """
        super(TwinBoundaryRelaxWorkChain, cls).define(spec)
        spec.input('calculator_settings',
                   valid_type=Dict,
                   required=True,
                   help="""
            Calculator settings.
            For more detail, see common.builder.get_calcjob_builder.
            It is enough to include 'relax' key and 'phonon' key is ignored.
            """)
        spec.input('computer',
                   valid_type=Str,
                   required=True,
                   help="""
            Computer.
            """)
        spec.input('twinboundary_relax_conf',
                   valid_type=Dict,
                   required=True,
                   help="""
            Relax config. For more detail,
            see aiida_twinpy.common.structure.get_twinboundary_structure.
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
            cls.check_initial_isif_is_two,
            cls.create_twinboudnary_structure,
            cls.run_relax,
            cls.extract_final_structure,
            cls.terminate,
            )

        spec.output('final_structure', valid_type=StructureData, required=True)
        spec.output('twinboundary_parameters', valid_type=Dict, required=True)

    def initialize(self):
        """
        Initialize.
        """
        self.report("# ---------------------------------")
        self.report("# Start TwinBoundaryRelaxWorkChain.")
        self.report("# ---------------------------------")
        self.ctx.calculator_settings = self.inputs.calculator_settings
        self.ctx.structure = None

    def terminate(self):
        """
        Terminate workflow.
        """
        self.report("# -----------------------------------------------------")
        self.report("# TwinBoundaryRelaxWorkChain has finished successfully.")
        self.report("# -----------------------------------------------------")
        self.report("All jobs have finished.")
        self.report("Terminate ShearWorkChain.")

    def check_initial_isif_is_two(self):
        """
        Check initial ISIF setting is 2, which allows to move only
        atom positions.
        """
        self.report("# ------------------------")
        self.report("# Check initial ISIF is 2.")
        self.report("# ------------------------")
        rlx_settings = \
            self.inputs.calculator_settings.get_dict()['relax']['relax_conf']
        run_mode = [rlx_settings['positions'],
                    rlx_settings['volume'],
                    rlx_settings['shape']]
        if run_mode == [True, False, False]:
            self.report("OK.")
        else:
            self.report("+++++++++++++++++++++++++")
            self.report("(WARNING): ISIF IS NOT 2.")
            self.report("+++++++++++++++++++++++++")

    def create_twinboudnary_structure(self):
        """
        Create twinboundary structure for relax.
        """
        self.report("# ------------------------------")
        self.report("# Create twinboundary structure.")
        self.report("# ------------------------------")
        return_vals = get_twinboundary_structure(
                self.inputs.structure,
                self.inputs.twinboundary_relax_conf)
        self.ctx.structure = return_vals['twinboundary']
        self.out('twinboundary_parameters',
                 return_vals['twinboundary_parameters'])
        self.report("# Finish create twinboundary structure.")

    def run_relax(self):
        self.report("# -----------------------")
        self.report("# Run relax calculations.")
        self.report("# -----------------------")
        relax_label = 'relax_twinboundary'
        relax_description = 'relax_twinboundary'
        if self.inputs.use_kpoints_interval:
            return_vals = fix_kpoints(
                    calculator_settings=self.ctx.calculator_settings,
                    structure=self.ctx.structure,
                    kpoints_conf=self.inputs.kpoints_conf,
                    is_phonon=Bool(False))
            self.ctx.calculator_settings = \
                    return_vals['calculator_settings']
        builder = get_calcjob_builder(
                label=relax_label,
                description=relax_description,
                calc_type='relax',
                computer=self.inputs.computer,
                structure=self.ctx.structure,
                calculator_settings=self.ctx.calculator_settings
                )
        future = self.submit(builder)
        self.report("{} relax workflow has submitted, pk: {}".format(
            relax_label, future.pk))
        self.to_context(**{relax_label: future})
        self.ctx.relax = future

    def extract_final_structure(self):
        self.report("# ------------------------")
        self.report("# Extract final structure.")
        self.report("# ------------------------")
        self.out('final_structure',
                 self.ctx.relax.outputs.relax__structure)
        self.report("Finish extract final structure.")
