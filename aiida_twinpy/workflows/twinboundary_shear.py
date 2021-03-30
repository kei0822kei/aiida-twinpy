#!/usr/bin/env python

"""
This module provides TwinBoundaryShearWorkChain.
"""

from aiida.engine import WorkChain, while_
from aiida.orm import load_node, Float, Int, Str, StructureData, Dict
from aiida_twinpy.common.structure import get_twinboundary_shear_structure
from aiida_twinpy.common.builder import (
        get_calcjob_builder_for_twinboundary_shear)


class TwinBoundaryShearWorkChain(WorkChain):
    """
    WorkChain for add shear toward relaxed twinboundary structure.

    Examples:
        workflow is as follows

        >>> twinboundary_shear_conf = Dict(dict={
        >>>     'shear_strain_ratios': [0.01, 0.02],
        >>>     'options': {'queue_name': 'vega-a',
        >>>                 'max_wallclock_sseconds': 100 * 3600},
    """

    @classmethod
    def define(cls, spec):
        super(TwinBoundaryShearWorkChain, cls).define(spec)
        spec.input('computer',
                   valid_type=Str,
                   required=True,
                   help="""
            Computer.
            """)
        spec.input('twinboundary_relax_structure',
                   valid_type=StructureData,
                   required=True,
                   help="""
            TwinBoundaryRelaxWorkChain.
            """)
        spec.input('twinboundary_shear_conf',
                   valid_type=Dict,
                   required=True,
                   help="""
            Twinboundary shear config. You can find sample in the docstring of
            this class.
            """)
        for i in range(20):
            spec.input('additional_relax.structure_%02d' % (i+1),
                       valid_type=StructureData,
                       required=False,
                       help="""
                Additional relax strcutures. Input starts from
                'additional_relax.structure_01', 'additional.relax_02' ... .
                """)

        spec.outline(
            cls.initialize,
            while_(cls.is_run_next_step)(
                cls.create_twinboundary_shear_structure,
                cls.run_relax,
                cls.update_vals,
                ),
            cls.terminate
        )

    def initialize(self):
        """
        Initialize.
        """
        self.report("# ---------------------------------")
        self.report("# Start TwinBoundaryShearWorkChain.")
        self.report("# ---------------------------------")
        additional_relax_structures = {}
        for i in range(20):
            try:
                label = 'structure_%02d' % (i+1)
                structure = self.inputs.additional_relax.__getattr__(label)
                new_label = 'additional_' + label
                additional_relax_structures[new_label] = structure
            except AttributeError:
                self.report("# Read %d additional relax structures." % i)
                break

        conf = self.inputs.twinboundary_shear_conf.get_dict()
        self.ctx.computer = self.inputs.computer
        self.ctx.twinboundary_relax_structure = \
            self.inputs.twinboundary_relax_structure
        self.ctx.conf = self.inputs.twinboundary_shear_conf
        self.ctx.ratios = conf['shear_strain_ratios']
        self.ctx.additional_relax_structures = additional_relax_structures
        self.ctx.structure = None
        self.ctx.count = 0
        self.ctx.previous_relax_pk = None
        self.ctx.previous_relax_structure = None
        self.report("# Shear strain ratios: {}".format(self.ctx.ratios))

    def update_vals(self):
        self.report("# --------------------------")
        self.report("# Update latest calculation.")
        self.report("# --------------------------")
        self.report("# Update count.")
        self.ctx.count += 1
        self.report("# Update previous relax structure.")
        self.ctx.previous_relax_structure = \
                load_node(self.ctx.previous_relax_pk).outputs.relax__structure

    def is_run_next_step(self):
        self.report("# -------------------------------------------")
        self.report("# Check all relax calculations have finished.")
        self.report("# -------------------------------------------")
        bl = self.ctx.count < len(self.ctx.ratios)
        if bl:
            self.report("# Not have finished.")
            self.report("# Start relax (count: %d)." % (self.ctx.count+1))
        else:
            self.report("# All relax calculations have finished.")
        return bl

    def terminate(self):
        self.report("# -----------------------------------------------------")
        self.report("# TwinBoundaryShearWorkChain has finished successfully.")
        self.report("# -----------------------------------------------------")
        self.report("# Terminate TwinBoundaryShearWorkChain.")

    def create_twinboundary_shear_structure(self):
        self.report("# ------------------------------------")
        self.report("# Create twinboundary shear structure.")
        self.report("# ------------------------------------")

        kwargs = {
            'twinboundary_relax_structure': self.ctx.twinboundary_relax_structure,
            'shear_strain_ratio': Float(self.ctx.ratios[self.ctx.count]),
            }
        kwargs.update(self.ctx.additional_relax_structures)
        if self.ctx.count > 0:
            kwargs.update({
                'previous_relax_structure': self.ctx.previous_relax_structure,
                })

        return_vals = get_twinboundary_shear_structure(**kwargs)

        # self.ctx.original_structure = \
        #         return_vals['twinboundary_shear_structure_orig']
        self.ctx.structure = \
                return_vals['twinboundary_shear_structure']
        self.ctx.kpoints = \
                return_vals['kpoints']
        self.report("# Kpoints fixed from:")
        self.report(
                "# {}".format(return_vals['kpoints_orig'].get_kpoints_mesh()))
        self.report("# To:")
        self.report(
                "# {}".format(return_vals['kpoints'].get_kpoints_mesh()))

    def run_relax(self):
        self.report('# ----------')
        self.report('# Run relax.')
        self.report('# ----------')
        label = 'twinboundary_shear_%03d' % (self.ctx.count+1)
        ratio = self.ctx.ratios[self.ctx.count]
        relax_label = 'rlx_' + label
        relax_description = relax_label + ", ratio: %f" % ratio
        builder = get_calcjob_builder_for_twinboundary_shear(
                label=relax_label,
                description=relax_description,
                computer=self.ctx.computer,
                structure=self.ctx.structure,
                kpoints=self.ctx.kpoints,
                twinboundary_shear_conf=self.ctx.conf,
                )
        future = self.submit(builder)
        self.report('{} relax workflow has submitted, pk: {}'.format(
            relax_label, future.pk))
        self.to_context(**{relax_label: future})
        self.ctx.previous_relax_pk = future.pk
