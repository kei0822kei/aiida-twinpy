import numpy as np
from aiida.engine import calcfunction
from aiida.plugins import DataFactory
from aiida.orm import Bool, Str, Int, load_node
from twinpy.crystalmaker import get_pymatgen_structure, is_hexagonal_metal, Hexagonal


@calcfunction
def get_hexagonal_twin_boudary_structure(structure,
                                         twinmode,
                                         twintype,
                                         dim,
                                         translation):
    return_vals = {}

    pmgstructure = structure.get_pymatgen()
    lattice = pmgstructure.lattice.matrix
    positions = pmgstructure.frac_coords
    elements = [ element.Z for element in pmgstructure.species ]
    hexagonal = (lattice, positions, elements)
    if not is_hexagonal_metal(hexagonal):
        raise ValueError("input sturucture is not hexagonal metal")
    a = lattice[0,0]
    c = lattice[2,2]
    element = elements[0]
    dimension = dim.get_array(dim.get_arraynames()[0])
    trans = translation.get_array(translation.get_arraynames()[0])
    hexagonal = Hexagonal(a, c, element, twinmode.value)
    parent = hexagonal.get_parent_structure(dimension,
                                            trans)
    twin = hexagonal.get_twin_structure(twintype.value,
                                        dimension,
                                        trans)
    twinboundary = hexagonal.get_twin_boundary(twintype.value,
                                               dimension,
                                               trans)
    return_vals['parent_structure'] = get_aiida_structure(parent)
    return_vals['twin_structure'] = get_aiida_structure(twin)
    return_vals['twinboundary_structure'] = get_aiida_structure(twinboundary)
    return return_vals


def get_aiida_structure(structure):
    pmgstructure = get_pymatgen_structure(structure)
    elements = [ element.value for element in pmgstructure.species ]
    aiidastructure = DataFactory('structure')(structure[0])
    for symbol, position in zip(elements, structure[1]):
        aiidastructure.append_atom(position=position, symbols=symbol)
    return aiidastructure

# @calcfunction
# def get_hexagonal_twin_boudary_structure(structure,
#                                          twinmode,
#                                          dim,
#                                          translation):
#     if not is_hexagonal_metal(structure):
#         raise ValueError("input sturucture is not hexagonal metal")
#     a = structure[0][0,0]
#     c = structure[0][2,2]
#     element = structure[2][0]
#     hexagonal = Hexagonal(a, c, element, twinmode)
# 
# 
# @calcfunction
# def check_imported_supercell_structure(supercell_ref,
#                                        supercell_calc,
#                                        symmetry_tolerance):
#     symprec = symmetry_tolerance.value
#     cell_diff = np.subtract(supercell_ref.cell, supercell_calc.cell)
#     if (np.abs(cell_diff) > symprec).any():
#         succeeded = Bool(False)
#         succeeded.label = "False"
#         return succeeded
# 
#     positions_ref = [site.position for site in supercell_ref.sites]
#     positions_calc = [site.position for site in supercell_calc.sites]
#     diff = np.subtract(positions_ref, positions_calc)
#     diff -= np.rint(diff)
#     dist = np.sqrt(np.sum(np.dot(diff, supercell_ref.cell) ** 2, axis=1))
#     if (dist > symprec).any():
#         succeeded = Bool(False)
#         succeeded.label = "False"
#         return succeeded
# 
#     succeeded = Bool(True)
#     succeeded.label = "True"
#     return succeeded
# 
# 
# @calcfunction
# def get_force_sets(**forces_dict):
#     forces = []
#     energies = []
#     for i in range(len(forces_dict)):
#         label = "forces_%03d" % (i + 1)
#         if label in forces_dict:
#             forces.append(forces_dict[label].get_array('final'))
#         label = "misc_%03d" % (i + 1)
#         if label in forces_dict:
#             energies.append(
#                 forces_dict[label]['total_energies']['energy_no_entropy'])
# 
#     assert len(forces) == sum(['forces' in k for k in forces_dict])
# 
#     force_sets = DataFactory('array')()
#     force_sets.set_array('force_sets', np.array(forces))
#     if energies:
#         force_sets.set_array('energies', np.array(energies))
#     force_sets.label = 'force_sets'
#     return force_sets
# 
# 
# @calcfunction
# def get_nac_params(born_charges, epsilon, nac_structure, **params):
#     """Obtain Born effective charges and dielectric constants in primitive cell
# 
#     When Born effective charges and dielectric constants are calculated within
#     phonopy workchain, those values are calculated in the primitive cell.
#     However using immigrant, the cell may not be primitive cell and can be
#     unit cell. In this case, conversion of data is necessary. This conversion
#     needs information of the structure where those values were calcualted and
#     the target primitive cell structure.
# 
#     Two kargs parameters
#     primitive : StructureData
#     symmetry_tolerance : Float
# 
#     """
#     from phonopy.structure.symmetry import symmetrize_borns_and_epsilon
# 
#     borns = born_charges.get_array('born_charges')
#     eps = epsilon.get_array('epsilon')
# 
#     nac_cell = phonopy_atoms_from_structure(nac_structure)
#     kargs = {}
#     if 'symmetry_tolerance' in params:
#         kargs['symprec'] = params['symmetry_tolerance'].value
#     if 'primitive' in params:
#         pcell = phonopy_atoms_from_structure(params['primitive'])
#         kargs['primitive'] = pcell
#     borns_, epsilon_ = symmetrize_borns_and_epsilon(
#         borns, eps, nac_cell, **kargs)
# 
#     nac_params = DataFactory('array')()
#     nac_params.set_array('born_charges', borns_)
#     nac_params.set_array('epsilon', epsilon_)
#     nac_params.label = 'born_charges & epsilon'
# 
#     return nac_params
# 
# 
# @calcfunction
# def get_force_constants(structure, phonon_settings, force_sets):
#     params = {}
#     phonon = get_phonopy_instance(structure, phonon_settings, params)
#     phonon.dataset = phonon_settings['displacement_dataset']
#     phonon.forces = force_sets.get_array('force_sets')
#     phonon.produce_force_constants()
#     force_constants = DataFactory('array')()
#     force_constants.set_array('force_constants', phonon.force_constants)
#     force_constants.set_array('p2s_map', phonon.primitive.p2s_map)
#     force_constants.label = 'force_constants'
# 
#     return force_constants
# 
# 
# @calcfunction
# def get_phonon(structure, phonon_settings, force_constants, **params):
#     phonon_settings_dict = phonon_settings.get_dict()
#     ph = get_phonopy_instance(structure, phonon_settings_dict, params)
#     ph.force_constants = force_constants.get_array('force_constants')
#     mesh = phonon_settings_dict['mesh']
# 
#     # Mesh
#     total_dos, pdos, thermal_properties = get_mesh_property_data(ph, mesh)
# 
#     # Band structure
#     bs = get_bands_data(ph)
# 
#     return {'dos': total_dos,
#             'pdos': pdos,
#             'thermal_properties': thermal_properties,
#             'band_structure': bs}
# 
# 
# @calcfunction
# def get_data_from_node_id(node_id):
#     n = load_node(node_id.value)
#     if 'structure' in n.inputs:
#         cell = phonopy_atoms_from_structure(n.inputs.structure)
#         structure = phonopy_atoms_to_structure(cell)
#     else:
#         raise RuntimeError("Crystal structure could not be found.")
# 
#     if 'born_charges' in n.outputs and 'dielectrics' in n.outputs:
#         born = DataFactory('array')()
#         born.set_array(
#             'born_charges', n.outputs.born_charges.get_array('born_charges'))
#         born.label = 'born_charges'
#         epsilon = DataFactory('array')()
#         epsilon.set_array(
#             'epsilon', n.outputs.dielectrics.get_array('epsilon'))
#         epsilon.label = 'epsilon'
#         return {'born_charges': born, 'dielectrics': epsilon,
#                 'structure': structure}
#     elif 'forces' in n.outputs:
#         forces = DataFactory('array')()
#         forces.set_array('final', n.outputs.forces.get_array('final'))
#         forces.label = 'forces'
#         return {'forces': forces, 'structure': structure}
#     else:
#         raise RuntimeError("Forces or NAC params were not found.")
# 
# 
# def get_mesh_property_data(ph, mesh):
#     ph.set_mesh(mesh)
#     ph.run_total_dos()
# 
#     dos = get_total_dos(ph.get_total_dos_dict())
# 
#     ph.run_thermal_properties()
#     tprops = get_thermal_properties(ph.get_thermal_properties_dict())
# 
#     ph.set_mesh(mesh, is_eigenvectors=True, is_mesh_symmetry=False)
#     ph.run_projected_dos()
#     pdos = get_projected_dos(ph.get_projected_dos_dict())
# 
#     return dos, pdos, tprops
# 
# 
# def get_total_dos(total_dos):
#     dos = DataFactory('array.xy')()
#     dos.set_x(total_dos['frequency_points'], 'Frequency', 'THz')
#     dos.set_y(total_dos['total_dos'], 'Total DOS', '1/THz')
#     dos.label = 'Total DOS'
#     return dos
# 
# 
# def get_projected_dos(projected_dos):
#     pdos = DataFactory('array.xy')()
#     pdos_list = [pd for pd in projected_dos['projected_dos']]
#     pdos.set_x(projected_dos['frequency_points'], 'Frequency', 'THz')
#     pdos.set_y(pdos_list,
#                ['Projected DOS', ] * len(pdos_list),
#                ['1/THz', ] * len(pdos_list))
#     pdos.label = 'Projected DOS'
#     return pdos
# 
# 
# def get_thermal_properties(thermal_properties):
#     tprops = DataFactory('array.xy')()
#     tprops.set_x(thermal_properties['temperatures'], 'Temperature', 'K')
#     tprops.set_y([thermal_properties['free_energy'],
#                   thermal_properties['entropy'],
#                   thermal_properties['heat_capacity']],
#                  ['Helmholtz free energy', 'Entropy', 'Cv'],
#                  ['kJ/mol', 'J/K/mol', 'J/K/mol'])
#     tprops.label = 'Thermal properties'
#     return tprops
# 
# 
# def get_bands_data(ph):
#     ph.auto_band_structure()
#     labels = [x.replace('$', '').replace('\\', '').replace('mathrm{', '').replace('}', '').upper()
#               for x in ph.band_structure.labels]
#     frequencies = ph.band_structure.frequencies
#     qpoints = ph.band_structure.qpoints
#     path_connections = ph.band_structure.path_connections
#     label = "%s (%d)" % (ph.symmetry.dataset['international'],
#                          ph.symmetry.dataset['number'])
# 
#     return get_bands(qpoints, frequencies, labels, path_connections,
#                      label=label)
# 
# 
# def get_bands(qpoints, frequencies, labels, path_connections, label=None):
#     qpoints_list = list(qpoints[0])
#     frequencies_list = list(frequencies[0])
#     labels_list = [(0, labels[0]), ]
#     label_index = 1
# 
#     for pc, qs, fs in zip(path_connections[:-1], qpoints[1:], frequencies[1:]):
#         if labels[label_index] == 'GAMMA' and pc:
#             labels_list.append((len(qpoints_list) - 1, labels[label_index]))
#             if label_index < len(labels):
#                 labels_list.append((len(qpoints_list), labels[label_index]))
#             label_index += 1
#             qpoints_list += list(qs)
#             frequencies_list += list(fs)
#         elif pc:
#             labels_list.append((len(qpoints_list) - 1, labels[label_index]))
#             label_index += 1
#             qpoints_list += list(qs[1:])
#             frequencies_list += list(fs[1:])
#         else:
#             labels_list.append((len(qpoints_list) - 1, labels[label_index]))
#             label_index += 1
#             if label_index < len(labels):
#                 labels_list.append((len(qpoints_list), labels[label_index]))
#                 label_index += 1
#             qpoints_list += list(qs)
#             frequencies_list += list(fs)
#     labels_list.append((len(qpoints_list) - 1, labels[-1]))
# 
#     bs = DataFactory('array.bands')()
#     bs.set_kpoints(np.array(qpoints_list))
#     bs.set_bands(np.array(frequencies_list), units='THz')
#     bs.labels = labels_list
#     if label is not None:
#         bs.label = label
# 
#     return bs
# 
# 
# def get_phonopy_instance(structure, phonon_settings_dict, params):
#     from phonopy import Phonopy
#     phonon = Phonopy(
#         phonopy_atoms_from_structure(structure),
#         phonon_settings_dict['supercell_matrix'],
#         primitive_matrix='auto',
#         symprec=phonon_settings_dict['symmetry_tolerance'])
#     if 'nac_params' in params:
#         from phonopy.interface import get_default_physical_units
#         units = get_default_physical_units('vasp')
#         factor = units['nac_factor']
#         nac_params = {'born': params['nac_params'].get_array('born_charges'),
#                       'dielectric': params['nac_params'].get_array('epsilon'),
#                       'factor': factor}
#         phonon.set_nac_params(nac_params)
# 
#     return phonon
# 
# 
# def get_primitive(structure, ph_settings):
#     from phonopy import Phonopy
# 
#     phonon = Phonopy(
#         phonopy_atoms_from_structure(structure),
#         supercell_matrix=ph_settings.get_dict()['supercell_matrix'],
#         primitive_matrix=ph_settings.get_dict()['primitive_matrix'],
#         symprec=ph_settings.get_dict()['symmetry_tolerance'])
#     primitive_phonopy = phonon.get_primitive()
# 
#     primitive_cell = primitive_phonopy.get_cell()
#     symbols = primitive_phonopy.get_chemical_symbols()
#     positions = primitive_phonopy.get_positions()
# 
#     primitive_structure = DataFactory('structure')(cell=primitive_cell)
#     for symbol, position in zip(symbols, positions):
#         primitive_structure.append_atom(position=position, symbols=symbol)
# 
#     return {'primitive_structure': primitive_structure}
# 
# 
# def phonopy_atoms_to_structure(cell):
#     symbols = cell.get_chemical_symbols()
#     positions = cell.get_positions()
#     structure = DataFactory('structure')(cell=cell.get_cell())
#     for symbol, position in zip(symbols, positions):
#         structure.append_atom(position=position, symbols=symbol)
#     return structure
# 
# 
# def phonopy_atoms_from_structure(structure):
#     cell = PhonopyAtoms(symbols=[site.kind_name for site in structure.sites],
#                         positions=[site.position for site in structure.sites],
#                         cell=structure.cell)
#     return cell
# 
# 
# def from_node_id_to_aiida_node_id(node_id):
#     if type(node_id) is int:
#         return Int(node_id)
#     elif type(node_id) is str:
#         return Str(node_id)
#     else:
#         raise RuntimeError("%s is not supported in load_node."
#                            % type(node_id))
