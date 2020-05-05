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
