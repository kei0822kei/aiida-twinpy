#!/usr/bin/env python

from aiida.engine import WorkChain, if_
from aiida.orm import Bool, Float, Str, Int, Dict, StructureData, KpointsData
from aiida_twinpy.common.utils import (get_sheared_structures,
                                       collect_relax_results)
from aiida_twinpy.common.builder import get_relax_builder

class ShearWorkChain(WorkChain):
    """
    WorkChain for add shear from the original hexagonal twin mode
    """

    @classmethod
    def define(cls, spec):
        super(ShearWorkChain, cls).define(spec)
        spec.input('clean_workdir', valid_type=Bool, required=True)
        spec.input('computer', valid_type=Str, required=True)
        spec.input('dry_run', valid_type=Bool, required=True)
        spec.input('grids', valid_type=Int, required=True)
        spec.input('incar_settings', valid_type=Dict, required=True)
        spec.input('kpoints', valid_type=KpointsData, required=True)
        spec.input('potential_family', valid_type=Str, required=True)
        spec.input('potential_mapping', valid_type=Dict, required=True)
        spec.input('queue', valid_type=Str, required=True)
        spec.input('relax_conf', valid_type=Dict, required=True)
        spec.input('structure', valid_type=StructureData, required=True)
        spec.input('twinmode', valid_type=Str, required=True)
        spec.input('vaspcode', valid_type=Str, required=True)

        spec.outline(
            cls.create_sheared_structures,
            if_(cls.dry_run)(
            cls.postprocess_of_dry_run,
            ).else_(
                cls.run_relax,
                cls.create_energies,
                cls.postprocess
                )
        )

        spec.output('parent', valid_type=StructureData, required=True)
        spec.output('strain', valid_type=Float, required=True)
        spec.output('shear_ratios', valid_type=Dict, required=True)
        spec.output('relax_results', valid_type=Dict, required=True)

    def dry_run(self):
        return self.inputs.dry_run

    def postprocess_of_dry_run(self):
        self.report('#----------------------')
        self.report('# dry run has activated')
        self.report('#----------------------')
        self.report('terminate ShearWorkChain')

    def postprocess(self):
        self.report('#-----------------------------------------')
        self.report('# ShearWorkChain has finished successfully')
        self.report('#-----------------------------------------')
        self.report('all jobs have finished')
        self.report('terminate ShearWorkChain')

    def create_sheared_structures(self):
        self.report('#--------------------------')
        self.report('# create sheared structures')
        self.report('#--------------------------')
        return_vals = get_sheared_structures(
                self.inputs.structure,
                self.inputs.twinmode,
                self.inputs.grids,
                )
        self.out('parent', return_vals['parent'])
        self.out('strain', return_vals['strain'])
        self.out('shear_ratios', return_vals['shear_settings'])
        self.ctx.ratios = return_vals['shear_settings']['shear_ratios']
        self.ctx.shears = {}
        for i in range(len(self.ctx.ratios)):
            label = "shear_%03d" % (i+1)
            self.ctx.shears[label] = return_vals[label]

    def run_relax(self):
        self.report('#------------------------------')
        self.report('# run relax calculations')
        self.report('#------------------------------')
        for i, ratio in enumerate(self.ctx.ratios):
            label = 'shear_%03d' % (i+1)
            relax_label = 'rlx_' + label
            relax_description = relax_label + ", ratio: %f" % ratio
            builder = get_relax_builder(
                       computer=self.inputs.computer,
                          label=relax_label,
                    description=relax_description,
                      structure=self.ctx.shears[label],
                 incar_settings=self.inputs.incar_settings,
                     relax_conf=self.inputs.relax_conf,
                        kpoints=self.inputs.kpoints,
               potential_family=self.inputs.potential_family,
              potential_mapping=self.inputs.potential_mapping,
                          queue=self.inputs.queue,
                  clean_workdir=self.inputs.clean_workdir,
                        verbose=Bool(True)
                    )
            future = self.submit(builder)
            self.report('{} relax workflow has submitted, pk: {}'
                    .format(label, future.pk))
            self.to_context(**{relax_label: future})

    def create_energies(self):
        self.report('#----------------')
        self.report('# collect results')
        self.report('#----------------')
        rlx_results = {}
        for i in range(len(self.ctx.ratios)):
            label = 'shear_%03d' % (i+1)
            relax_label = 'rlx_' + label
            rlx_results[relax_label] = self.ctx[relax_label].outputs['misc']
        return_vals = collect_relax_results(**rlx_results)
        self.out('relax_results', return_vals['relax_results'])
