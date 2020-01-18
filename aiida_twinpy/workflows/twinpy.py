from aiida.engine import WorkChain
from aiida.plugins import DataFactory
from aiida.orm import Float, Bool, Str, Code, List, Int
from aiida_phonopy.common.generate_inputs import (get_calcjob_builder,
                                                  get_immigrant_builder)
from aiida_phonopy.common.utils import (
    get_force_sets, get_force_constants, get_nac_params, get_phonon,
    get_phonon_setting_info, check_imported_supercell_structure,
    from_node_id_to_aiida_node_id, get_data_from_node_id)
from twinpy.crystalmaker import is_hexagonal_metal, Hexagonal
# from aiida_twinpy.common.generate_inputs import get_aiida_structuredata
from aiida_twinpy.common.utils import get_hexagonal_twin_boudary_structure


# Should be improved by some kind of WorkChainFactory
# For now all workchains should be copied to aiida/workflows

Dict = DataFactory('dict')
ArrayData = DataFactory('array')
StructureData = DataFactory('structure')


class TwinpyWorkChain(WorkChain):
    """
    Workchain to do a twin calculation using phonopy
    """

    @classmethod
    def define(cls, spec):
        super(TwinpyWorkChain, cls).define(spec)
        spec.input('structure', valid_type=StructureData, required=True)
        spec.input('twinmode', valid_type=Str, required=True)
        spec.input('twintype', valid_type=Int, required=True)
        spec.input('dim', valid_type=ArrayData, required=True)
        spec.input('translation', valid_type=ArrayData, required=True)

        spec.outline(
            cls.create_hexagonal_twin_boudary_structure
        )
        spec.output('parent_structure', valid_type=StructureData, required=True)
        spec.output('twin_structure', valid_type=StructureData, required=True)
        spec.output('twinboundary_structure', valid_type=StructureData, required=True)

    def create_hexagonal_twin_boudary_structure(self):
        return_vals = get_hexagonal_twin_boudary_structure(
                self.inputs.structure,
                self.inputs.twinmode,
                self.inputs.twintype,
                self.inputs.dim,
                self.inputs.translation
                )
        self.ctx.parent = return_vals['parent_structure']
        self.ctx.twin = return_vals['twin_structure']
        self.ctx.twinboundary = return_vals['twinboundary_structure']
        self.out('parent_structure', self.ctx.parent)
        self.out('twin_structure', self.ctx.twin)
        self.out('twinboundary_structure', self.ctx.twinboundary)



    # def run_static_calculations(self):
    #     self.report('run static calculations')

    #     # Forces
    #     for i in range(len(self.ctx.supercells)):
    #         label = "supercell_%03d" % (i + 1)
    #         builder = get_calcjob_builder(self.ctx.supercells[label],
    #                                       self.inputs.calculator_settings,
    #                                       calc_type='forces',
    #                                       label=label)
    #         future = self.submit(builder)
    #         self.report('{} pk = {}'.format(label, future.pk))
    #         self.to_context(**{label: future})

    # def collect_data(self):
    #     self.report('collect data')
    #     self.out('translation_energy_sets',
    #              self.ctx.phonon_properties.outputs.thermal_properties)

    #     self.report('finish phonon')


    # def dry_run(self):
    #     return self.inputs.dry_run

    # def remote_phonopy(self):
    #     return self.inputs.remote_phonopy

    # def run_phonopy(self):
    #     return self.inputs.run_phonopy

    # def is_nac(self):
    #     if 'is_nac' in self.inputs.phonon_settings.attributes:
    #         return self.inputs.phonon_settings['is_nac']
    #     else:
    #         False

    # def import_calculations_from_files(self):
    #     return 'immigrant_calculation_folders' in self.inputs

    # def import_calculations_from_nodes(self):
    #     return 'calculation_nodes' in self.inputs

    # def import_calculations(self):
    #     if 'immigrant_calculation_folders' in self.inputs:
    #         return True
    #     if 'calculation_nodes' in self.inputs:
    #         return True
    #     return False

    # def initialize_supercell_phonon_calculation(self):
    #     """Set default settings and create supercells and primitive cell"""

    #     self.report('initialize_supercell_phonon_calculation')

    #     if self.inputs.run_phonopy and self.inputs.remote_phonopy:
    #         if ('code_string' not in self.inputs or
    #             'options' not in self.inputs):
    #             raise RuntimeError(
    #                 "code_string and options have to be specified.")

    #     if 'supercell_matrix' not in self.inputs.phonon_settings.attributes:
    #         raise RuntimeError(
    #             "supercell_matrix was not found in phonon_settings.")

    #     if 'displacement_dataset' in self.inputs:
    #         return_vals = get_phonon_setting_info(
    #             self.inputs.phonon_settings,
    #             self.inputs.structure,
    #             self.inputs.symmetry_tolerance,
    #             displacement_dataset=self.inputs.displacement_dataset)
    #     else:
    #         return_vals = get_phonon_setting_info(
    #             self.inputs.phonon_settings,
    #             self.inputs.structure,
    #             self.inputs.symmetry_tolerance)
    #     self.ctx.phonon_setting_info = return_vals['phonon_setting_info']
    #     self.out('phonon_setting_info', self.ctx.phonon_setting_info)

    #     self.ctx.supercells = {}
    #     for i in range(len(return_vals) - 3):
    #         label = "supercell_%03d" % (i + 1)
    #         self.ctx.supercells[label] = return_vals[label]
    #     self.ctx.primitive = return_vals['primitive']
    #     self.ctx.supercell = return_vals['supercell']
    #     self.out('primitive', self.ctx.primitive)
    #     self.out('supercell', self.ctx.supercell)

    # def run_force_and_nac_calculations(self):
    #     self.report('run force calculations')

    #     # Forces
    #     for i in range(len(self.ctx.supercells)):
    #         label = "supercell_%03d" % (i + 1)
    #         builder = get_calcjob_builder(self.ctx.supercells[label],
    #                                       self.inputs.calculator_settings,
    #                                       calc_type='forces',
    #                                       label=label)
    #         future = self.submit(builder)
    #         self.report('{} pk = {}'.format(label, future.pk))
    #         self.to_context(**{label: future})

    #     # Born charges and dielectric constant
    #     if self.ctx.phonon_setting_info['is_nac']:
    #         self.report('calculate born charges and dielectric constant')
    #         builder = get_calcjob_builder(self.ctx.primitive,
    #                                       self.inputs.calculator_settings,
    #                                       calc_type='nac',
    #                                       label='born_and_epsilon')
    #         future = self.submit(builder)
    #         self.report('born_and_epsilon: {}'.format(future.pk))
    #         self.to_context(**{'born_and_epsilon': future})

    # def read_force_and_nac_calculations_from_files(self):
    #     self.report('import calculation data in files')

    #     calc_folders_Dict = self.inputs.immigrant_calculation_folders
    #     for i, force_folder in enumerate(calc_folders_Dict['force']):
    #         label = "supercell_%03d" % (i + 1)
    #         builder = get_immigrant_builder(force_folder,
    #                                         self.inputs.calculator_settings,
    #                                         calc_type='forces')
    #         builder.metadata.label = label
    #         future = self.submit(builder)
    #         self.report('{} pk = {}'.format(label, future.pk))
    #         self.to_context(**{label: future})

    #     if self.ctx.phonon_setting_info['is_nac']:  # NAC the last one
    #         label = 'born_and_epsilon'
    #         builder = get_immigrant_builder(calc_folders_Dict['nac'][0],
    #                                         self.inputs.calculator_settings,
    #                                         calc_type='nac')
    #         builder.metadata.label = label
    #         future = self.submit(builder)
    #         self.report('{} pk = {}'.format(label, future.pk))
    #         self.to_context(**{label: future})

    # def read_calculation_data_from_nodes(self):
    #     self.report('import calculation data from nodes')

    #     calc_nodes_Dict = self.inputs.calculation_nodes

    #     for i, node_id in enumerate(calc_nodes_Dict['force']):
    #         label = "supercell_%03d" % (i + 1)
    #         aiida_node_id = from_node_id_to_aiida_node_id(node_id)
    #         # self.ctx[label]['forces'] -> ArrayData()('final')
    #         self.ctx[label] = get_data_from_node_id(aiida_node_id)

    #     if self.ctx.phonon_setting_info['is_nac']:  # NAC the last one
    #         label = 'born_and_epsilon'
    #         node_id = calc_nodes_Dict['nac'][0]
    #         aiida_node_id = from_node_id_to_aiida_node_id(node_id)
    #         # self.ctx[label]['born_charges'] -> ArrayData()('born_charges')
    #         # self.ctx[label]['dielectrics'] -> ArrayData()('epsilon')
    #         self.ctx[label] = get_data_from_node_id(aiida_node_id)

    # def check_imported_supercell_structures(self):
    #     self.report('check imported supercell structures')

    #     msg = ("Immigrant failed because of inconsistency of supercell"
    #            "structure")

    #     for i in range(len(self.ctx.supercells)):
    #         label = "supercell_%03d" % (i + 1)
    #         calc = self.ctx[label]
    #         if type(calc) is dict:
    #             calc_dict = calc
    #         else:
    #             calc_dict = calc.inputs
    #         supercell_ref = self.ctx.supercells[label]
    #         supercell_calc = calc_dict['structure']
    #         if not check_imported_supercell_structure(
    #                 supercell_ref,
    #                 supercell_calc,
    #                 self.inputs.symmetry_tolerance):
    #             raise RuntimeError(msg)

    # def postprocess_of_dry_run(self):
    #     self.report('Finish here because of dry-run setting')

    # def create_force_sets(self):
    #     """Build datasets from forces of supercells with displacments"""

    #     self.report('create force sets')

    #     # VASP specific
    #     forces_dict = {}

    #     for i in range(len(self.ctx.supercells)):
    #         label = "supercell_%03d" % (i + 1)
    #         calc = self.ctx[label]
    #         if type(calc) is dict:
    #             calc_dict = calc
    #         else:
    #             calc_dict = calc.outputs
    #         if ('forces' in calc_dict and
    #             'final' in calc_dict['forces'].get_arraynames()):
    #             label = "forces_%03d" % (i + 1)
    #             forces_dict[label] = calc_dict['forces']
    #         else:
    #             msg = ("Forces could not be found in calculation %03d."
    #                    % (i + 1))
    #             self.report(msg)

    #         if ('misc' in calc_dict and
    #             'total_energies' in calc_dict['misc'].keys()):
    #             label = "misc_%03d" % (i + 1)
    #             forces_dict[label] = calc_dict['misc']

    #     if sum(['forces' in k for k in forces_dict]) != len(self.ctx.supercells):
    #         raise RuntimeError("Forces could not be retrieved.")

    #     self.ctx.force_sets = get_force_sets(**forces_dict)
    #     self.out('force_sets', self.ctx.force_sets)

    # def create_nac_params(self):
    #     self.report('create nac data')

    #     # VASP specific
    #     # Call workfunction to make links
    #     calc = self.ctx.born_and_epsilon
    #     if type(calc) is dict:
    #         calc_dict = calc
    #         structure = calc['structure']
    #     else:
    #         calc_dict = calc.outputs
    #         structure = calc.inputs.structure

    #     if 'born_charges' not in calc_dict:
    #         raise RuntimeError(
    #             "Born effective charges could not be found "
    #             "in the calculation. Please check the calculation setting.")
    #     if 'dielectrics' not in calc_dict:
    #         raise RuntimeError(
    #             "Dielectric constant could not be found "
    #             "in the calculation. Please check the calculation setting.")

    #     params = {'symmetry_tolerance':
    #               Float(self.ctx.phonon_setting_info['symmetry_tolerance'])}
    #     if self.import_calculations():
    #         params['primitive'] = self.ctx.primitive
    #     self.ctx.nac_params = get_nac_params(
    #         calc_dict['born_charges'],
    #         calc_dict['dielectrics'],
    #         structure,
    #         **params)
    #     self.out('nac_params', self.ctx.nac_params)

    # def run_phonopy_remote(self):
    #     """Run phonopy at remote computer"""

    #     self.report('remote phonopy calculation')

    #     code_string = self.inputs.code_string.value
    #     builder = Code.get_from_string(code_string).get_builder()
    #     builder.structure = self.inputs.structure
    #     builder.settings = self.ctx.phonon_setting_info
    #     builder.metadata.options.update(self.inputs.options)
    #     builder.metadata.label = self.inputs.metadata.label
    #     builder.force_sets = self.ctx.force_sets
    #     if 'nac_params' in self.ctx:
    #         builder.nac_params = self.ctx.nac_params
    #         builder.primitive = self.ctx.primitive
    #     future = self.submit(builder)

    #     self.report('phonopy calculation: {}'.format(future.pk))
    #     self.to_context(**{'phonon_properties': future})
    #     # return ToContext(phonon_properties=future)

    # def collect_data(self):
    #     self.report('collect data')
    #     self.out('thermal_properties',
    #              self.ctx.phonon_properties.outputs.thermal_properties)
    #     self.out('dos', self.ctx.phonon_properties.outputs.dos)
    #     self.out('pdos', self.ctx.phonon_properties.outputs.pdos)
    #     self.out('band_structure',
    #              self.ctx.phonon_properties.outputs.band_structure)
    #     self.out('force_constants',
    #              self.ctx.phonon_properties.outputs.force_constants)

    #     self.report('finish phonon')

    # def create_force_constants(self):
    #     self.report('create force constants')

    #     self.ctx.force_constants = get_force_constants(
    #         self.inputs.structure,
    #         self.ctx.phonon_setting_info,
    #         self.ctx.force_sets)
    #     self.out('force_constants', self.ctx.force_constants)

    # def run_phonopy_in_workchain(self):
    #     self.report('phonopy calculation in workchain')

    #     params = {}
    #     if 'nac_params' in self.ctx:
    #         params['nac_params'] = self.ctx.nac_params
    #     result = get_phonon(self.inputs.structure,
    #                         self.ctx.phonon_setting_info,
    #                         self.ctx.force_constants,
    #                         **params)
    #     self.out('thermal_properties', result['thermal_properties'])
    #     self.out('dos', result['dos'])
    #     self.out('band_structure', result['band_structure'])

    #     self.report('finish phonon')
