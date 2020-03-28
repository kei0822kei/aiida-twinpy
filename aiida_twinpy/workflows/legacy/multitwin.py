from aiida.engine import WorkChain, if_
from aiida.plugins import DataFactory
from aiida.orm import Float, Bool, Str, Int
from aiida_twinpy.common.generate_inputs import get_vasp_builder
from aiida_twinpy.common.utils import get_hexagonal_twin_boudary_structures

Dict = DataFactory('dict')
ArrayData = DataFactory('array')
StructureData = DataFactory('structure')


class MultiTwinWorkChain(WorkChain):
    """
    Workchain to construct many twin boundaries and run static vasp calculation
    """

    @classmethod
    def define(cls, spec):
        super(MultiTwinWorkChain, cls).define(spec)
        spec.input('structure', valid_type=StructureData, required=True)
        spec.input('twinmode', valid_type=Str, required=True)
        spec.input('twintype', valid_type=Int, required=True)
        spec.input('dim', valid_type=ArrayData, required=True)
        spec.input('translation_grids', valid_type=ArrayData, required=True)
        spec.input('vasp_settings', valid_type=Dict, required=True)
        spec.input('dry_run', valid_type=Bool, required=True)
        spec.input('distance_threshold', valid_type=Float, required=True)

        spec.outline(
            cls.create_hexagonal_twin_boudary_structures,
            if_(cls.dry_run)(
            cls.postprocess_of_dry_run,
            ).else_(
                cls.run_vasp,
                cls.collect_results
                )
        )
        spec.output('grid_points', valid_type=ArrayData, required=True)
        spec.output('total_structures', valid_type=Int, required=True)
        spec.output('neighbor_distances', valid_type=Dict, required=True)
        spec.output('results', valid_type=Dict, required=True)

    def create_hexagonal_twin_boudary_structures(self):
        """
        Set default settings and create twin boundaries
        """
        self.report('create twin boundary structures')

        return_vals = get_hexagonal_twin_boudary_structures(
                self.inputs.structure,
                self.inputs.twinmode,
                self.inputs.twintype,
                self.inputs.dim,
                self.inputs.translation_grids
                )
        self.ctx.twinboundaries = {}
        self.ctx.neighbor_distances = {}
        for i in range(return_vals['total_structures'].value):
            twin_label = 'twinboundary_%03d' % (i+1)
            self.ctx.twinboundaries[twin_label] = return_vals[twin_label]
            neighbor_label = 'neighbor_distance_%03d' % (i+1)
            self.ctx.neighbor_distances[neighbor_label] = \
                    return_vals[neighbor_label]
        neighbor = Dict(dict=self.ctx.neighbor_distances)
        neighbor.store()
        self.out('grid_points', return_vals['grid_points'])
        self.out('total_structures', return_vals['total_structures'])
        self.out('neighbor_distances', neighbor)

    def run_vasp(self):
        self.report("run translations calculations")
        for i in range(len(self.ctx.twinboundaries)):
            label = 'twinboundary_%03d' % (i+1)
            if self.ctx.neighbor_distances['neighbor_distance_%03d' % (i+1)] \
                    < self.inputs.distance_threshold.value:
                self.report("%s : the distance of atoms are less \
                             than distance_threshold, skip vasp calculation"
                            % label)
            else:
                builder = get_vasp_builder(self.ctx.twinboundaries[label],
                                           self.inputs.vasp_settings)
                builder.metadata.label = label
                future = self.submit(builder)
                self.report('twinpy calculation {} pk {}'.format(label, future.pk))
                self.to_context(**{label: future})

    def collect_results(self):
        results = {}
        for i in range(len(self.ctx.twinboundaries)):
            label = 'twinboundary_%03d' % (i+1)
            if label in list(self.ctx.keys()):
                results[label] = dict(self.ctx[label].outputs.misc)
            else:
                results[label] = None
        return_val = Dict(dict=results)
        return_val.store()
        self.out('results', return_val)
        self.report('finish twinboundary calculation')

    def dry_run(self):
        return self.inputs.dry_run

    def postprocess_of_dry_run(self):
        self.report('Finish here because of dry-run setting')
