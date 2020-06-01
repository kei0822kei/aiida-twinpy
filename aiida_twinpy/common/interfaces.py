#!usr/bin/env python

from aiida.orm import load_node
from aiida_phonopy.common.utils import phonopy_atoms_from_structure
from phonopy import Phonopy

def get_phonon_from_aiida(phonon_pk):
    node = load_node(phonon_pk)
    unitcell = phonopy_atoms_from_structure(node.inputs.structure)
    phonon_settings = node.outputs.phonon_setting_info.get_dict()
    phonon = Phonopy(unitcell,
                     supercell_matrix=phonon_settings['supercell_matrix'],
                     primitive_matrix=phonon_settings['primitive_matrix'])
    phonon.set_displacement_dataset(phonon_settings['displacement_dataset'])
    phonon.set_forces(node.outputs.force_sets.get_array('force_sets'))
    phonon.produce_force_constants()
    return phonon

def get_vasp_settings_for_from_phonopy(phonon_pk,
                                       incar_update_settings,
                                       clean_workdir,
                                       parser_settings,
                                       queue,
                                       kpoints):
    node = load_node(phonon_pk)
    calc = node.inputs.calculator_settings.get_dict()['forces']
    incar_settings = calc['parameters']
    incar_settings.update(incar_update_settings)
    vasp_settings = {
            'vasp_code': calc['code_string'].split('@')[0],
            'incar_settings': incar_settings,
            'potential_family': calc['potential_family'],
            'potential_mapping': calc['potential_mapping'],
            'kpoints': {
                'mesh': kpoints['mesh'],
                'offset': kpoints['offset'],
                },
            'options': {'queue_name': queue,
                        'max_wallclock_seconds': calc['options']['max_wallclock_seconds']},
            'clean_workdir': clean_workdir,
            'parser_settings': parser_settings,
            }
    return vasp_settings
