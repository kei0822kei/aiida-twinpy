#!/usr/bin/env python

"""
This module provides TwinBoundaryShearWorkChain.
"""

from aiida.engine import WorkChain, while_
from aiida.orm import load_node, Int, Str, Dict
from aiida_twinpy.common.structure import get_twinboundary_shear_structure
from aiida_twinpy.common.utils import store_shear_ratios
from aiida_twinpy.common.builder import (
        get_calcjob_builder_for_twinboundary_shear)


class TwinBoundaryShearWorkChain(WorkChain):
    """
    WorkChain for add shear toward relaxed twinboundary structure.

    Examples:
        workflow is as follows

        >>> twinboundary_shear_conf = Dict(dict={
        >>>     'twinboundary_relax_pk': 11111,
        >>>     'additional_relax_pks': [11112, 11113],
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
        spec.input('twinboundary_shear_conf',
                   valid_type=Dict,
                   required=True,
                   help="""
            Twinboundary shear config. For more detail,
            see aiida_twinpy.common.structure.get_twinboundary_shear_structure.
            """)
        spec.outline(
            cls.initialize,
            cls.set_shear_ratios,
            while_(cls.is_run_next_step)(
                cls.create_twinboundary_shear_structure,
                cls.run_relax,
                cls.update_vals,
                ),
            cls.terminate
        )

        spec.output('steps_info', valid_type=Dict, required=False)

    def initialize(self):
        """
        Initialize.
        """
        self.report("# ---------------------------------")
        self.report("# Start TwinBoundaryShearWorkChain.")
        self.report("# ---------------------------------")
        self.ctx.ratios = []
        conf = self.inputs.twinboundary_shear_conf.get_dict()
        if 'additional_relax_pks' in conf and conf['additional_relax_pks']:
            prev_rlx_pk = conf['additional_relax_pks'][-1]
        else:
            self.report("# There is no additional_relax_pks.")
            prev_rlx_pk = load_node(conf['twinboundary_relax_pk']).called[-1].pk

        self.ctx.previous_relax_pk = Int(prev_rlx_pk)
        self.ctx.previous_shear_strain_ratio = None
        self.ctx.original_structure = None
        self.ctx.structure = None
        self.ctx.count = 0
        self.ctx.steps_info = {}

    def set_shear_ratios(self):
        self.report("# -----------------")
        self.report("# Set shear ratios.")
        self.report("# -----------------")
        return_vals = store_shear_ratios(self.inputs.twinboundary_shear_conf)
        num = len(self.inputs.twinboundary_shear_conf['shear_strain_ratios'])
        for i in range(num):
            label = 'ratio_%03d' % (i+1)
            self.ctx.ratios.append(return_vals[label])
        self.report("# Total shear ratios: %d" % num)
        self.report("# Shear ratios: {}".format(
            [ r.value for r in self.ctx.ratios ]))

    def update_vals(self):
        self.report("# --------------------------")
        self.report("# Update latest calculation.")
        self.report("# --------------------------")
        self.ctx.previous_shear_strain_ratio = self.ctx.ratios[self.ctx.count]
        self.ctx.count += 1

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
        self.out('steps_info', Dict(dict=self.ctx.steps_info))
        self.report("# Terminate TwinBoundaryShearWorkChain.")

    def create_twinboundary_shear_structure(self):
        self.report("# ------------------------------------")
        self.report("# Create twinboundary shear structure.")
        self.report("# ------------------------------------")

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
                computer=self.inputs.computer,
                structure=self.ctx.structure,
                kpoints=self.ctx.kpoints,
                twinboundary_shear_conf=self.inputs.twinboundary_shear_conf,
                )
        future = self.submit(builder)
        self.report('{} relax workflow has submitted, pk: {}'.format(
            relax_label, future.pk))
        self.to_context(**{relax_label: future})
        self.ctx.steps_info[label] ={
                'shear_strain_ratio': ratio,
                'relax_pk': future.pk,
                }
        self.ctx.previous_relax_pk = Int(future.pk)
