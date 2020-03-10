from aiida.engine import WorkChain, if_
from aiida.plugins import DataFactory, WorkflowFactory
from aiida.common.extendeddicts import AttributeDict
from aiida.orm import (Float, Bool, Str, Code, List, Int,
                       Dict, StructureData, ArrayData, KpointsData)
from aiida_phonopy.common.generate_inputs import (get_calcjob_builder,
                                                  get_immigrant_builder)
from aiida_phonopy.common.utils import (
    get_force_sets, get_force_constants, get_nac_params, get_phonon,
    get_phonon_setting_info, check_imported_supercell_structure,
    from_node_id_to_aiida_node_id, get_data_from_node_id)
# from aiida_twinpy.common.generate_inputs import get_aiida_structuredata
# from aiida_twinpy.common.utils import get_hexagonal_twin_boudary_structure
# from aiida_twinpy.common.generate_inputs import get_vasp_builder

from twinpy.structure import HexagonalClosePacked
from aiida_twinpy.common.utils import get_sheared_structures
from aiida_twinpy.common.builder import get_relax_builder


# Should be improved by some kind of WorkChainFactory
# For now all workchains should be copied to aiida/workflows


class ShearWorkChain(WorkChain):
    """
    WorkChain for add shear from the original hexagonal twin mode
    """

    @classmethod
    def define(cls, spec):
        super(ShearWorkChain, cls).define(spec)
        spec.input('computer', valid_type=Str, required=True)
        spec.input('queue', valid_type=Str, required=True)
        spec.input('structure', valid_type=StructureData, required=True)
        spec.input('twinmode', valid_type=Str, required=True)
        spec.input('grids', valid_type=Int, required=True)
        spec.input('incar_settings', valid_type=Dict, required=True)
        # spec.input('relax_conf', valid_type=AttributeDict, required=True)
        spec.input('relax_conf', valid_type=Dict, required=True)
        spec.input('kpoints', valid_type=KpointsData, required=True)
        spec.input('potential_family', valid_type=Str, required=True)
        spec.input('potential_mapping', valid_type=Dict, required=True)
        spec.input('clean_workdir', valid_type=Bool, required=True)
        spec.input('vaspcode', valid_type=Str, required=True)
        spec.input('verbose', valid_type=Bool, required=True)
        spec.input('dry_run', valid_type=Bool, required=True)

        spec.outline(
            cls.create_sheared_structures,
            if_(cls.dry_run)(
            cls.postprocess_of_dry_run,
            ).else_(
                cls.run_relax,
                cls.postprocess
                )
        )
        # spec.output('sheared_structures', valid_type=Dict, required=True)

    def dry_run(self):
        return self.inputs.dry_run

    def postprocess_of_dry_run(self):
        self.report('#----------------------')
        self.report('# dry run has activated')
        self.report('#----------------------')
        self.report('terminate ShearWorkChain')

    def postprocess(self):
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
        self.ctx.shears = return_vals
        # hoge = Dict(dict=return_vals)
        # hoge.store()
        # self.out('sheared_structures', hoge)

    def run_relax(self):
        def __get_relax_builder(structure, label):
            workflow = WorkflowFactory('vasp.relax')
            builder = workflow.get_builder()
            builder.metadata.label = label
            builder.metadata.description = label
            builder.code = Code.get_from_string('{}@{}'
                    .format(self.inputs.vaspcode.value, self.inputs.computer.value))
            builder.clean_workdir = self.inputs.clean_workdir
            builder.verbose = self.inputs.verbose
            __add_options(builder, self.inputs.queue)
            builder.structure = structure
            builder.parameters = self.inputs.incar_settings
            __add_relax(builder, self.inputs.relax_conf.get_dict())
            builder.settings = Dict(dict=
                               {
                                  'add_energies': True,
                                  'add_forces': True,
                                  'add_stress': True,
                               })
            builder.kpoints = self.inputs.kpoints
            builder.potential_family = self.inputs.potential_family
            builder.potential_mapping = self.inputs.potential_mapping
            return builder

        def __add_relax(builder, relax_conf):
            relax_attribute = AttributeDict()
            keys = relax_conf.keys()
            if 'perform' in keys:
                relax_attribute.perform = \
                        Bool(relax_conf['perform'])
            if 'positions' in keys:
                relax_attribute.positions = \
                        Bool(relax_conf['positions'])
            if 'volume' in keys:
                relax_attribute.volume = \
                        Bool(relax_conf['volume'])
            if 'shape' in keys:
                relax_attribute.shape = \
                        Bool(relax_conf['shape'])
            if 'steps' in keys:
                relax_attribute.steps = \
                        Int(relax_conf['steps'])
            if 'convergence_absolute' in keys:
                relax_attribute.convergence_absolute = \
                        Bool(relax_conf['convergence_absolute'])
            if 'convergence_max_iterations' in keys:
                relax_attribute.convergence_max_iterations = \
                        Int(relax_conf['convergence_max_iterations'])
            if 'convergence_on' in keys:
                relax_attribute.convergence_on = \
                        Bool(relax_conf['convergence_on'])
            if 'convergence_positions' in keys:
                relax_attribute.convergence_positions = \
                        Float(relax_conf['convergence_positions'])
            if 'convergence_shape_angles' in keys:
                relax_attribute.convergence_shape_angles = \
                        Float(relax_conf['convergence_shape_angles'])
            if 'convergence_shape_lengths' in keys:
                relax_attribute.convergence_shape_lengths = \
                        Float(relax_conf['convergence_shape_lengths'])
            if 'convergence_volume' in keys:
                relax_attribute.convergence_volume = \
                        Float(relax_conf['convergence_volume'])
            if 'force_cutoff' in keys:
                relax_attribute.force_cutoff = \
                        Float(relax_conf['force_cutoff'])
            if 'energy_cutoff' in keys:
                relax_attribute.energy_cutoff = \
                        Float(relax_conf['energy_cutoff'])
            builder.relax = relax_attribute

        def __add_options(builder, queue):
            options = AttributeDict()
            options.account = ''
            options.qos = ''
            options.resources = {'tot_num_mpiprocs': 16,
                                 'parallel_env': 'mpi*'}
            options.queue_name = queue
            options.max_wallclock_seconds = 3600*10
            builder.options = Dict(dict=options)

        self.report('#------------------------------')
        self.report('# run relax calculations')
        self.report('#------------------------------')
        for gp in self.ctx.shears.keys():
            label = 'gp: {}, ratio: {}'.format(gp, self.ctx.shears[gp]['ratio'].value)
            builder = __get_relax_builder(self.ctx.shears[gp]['structure'], label)
            future = self.submit(builder)
            self.report('shear calculation (ratio={}) has submitted, pk: {}'
                    .format(self.ctx.shears[gp]['ratio'], future.pk))
