#!usr/bin/env python

import numpy as np
from typing import Union
from aiida.engine import calcfunction
from aiida.orm import Dict
from aiida.orm.nodes.data import StructureData
from aiida_twinpy.common.interfaces import get_phonon_from_aiida
from aiida_phonopy.common.utils import phonopy_atoms_to_structure
from twinpy.api_twinpy import get_twinpy_from_cell
from twinpy.structure.base import get_atom_positions_from_lattice_points
from twinpy.interfaces.aiida.base import get_aiida_structure, get_cell_from_aiida
from twinpy.common.kpoints import get_mesh_offset_from_direct_lattice


@calcfunction
def fix_kpoints(calculator_settings,
                structure,
                interval,
                is_phonon):
    """
    Fix kpoints using kpoints interval.
    """
    lattice = get_cell_from_aiida(structure)[0]
    if is_phonon:
        run_mode = 'phonon'
        dim = calculator_settings[run_mode]['phonon_conf']['supercell_matrix']
        input_lattice = (lattice.T * dim).T
    else:
        run_mode = 'relax'
        input_lattice = lattice
    kpt_dic = get_mesh_offset_from_direct_lattice(
                  lattice=input_lattice,
                  interval=interval.value)
    kpoints = {'mesh': kpt_dic['mesh'], 'offset': kpt_dic['offset']}
    calc_settings = calculator_settings.get_dict()
    calc_settings[run_mode]['kpoints'] = kpoints
    return_vals = {}
    return_vals['calculator_settings'] = Dict(dict=calc_settings)
    return return_vals
