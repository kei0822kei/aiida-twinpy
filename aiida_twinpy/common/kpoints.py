#!usr/bin/env python

import numpy as np
from aiida.engine import calcfunction
from aiida.orm import Float, Dict, KpointsData
from twinpy.interfaces.aiida.base import get_cell_from_aiida
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


@calcfunction
def get_kpoints_interval(structure, kpoints):
    """
    Get kpoints interval.
    """
    cell = get_cell_from_aiida(structure)
    kpoints_info = get_mesh_offset_from_direct_lattice(
            lattice=cell[0],
            mesh=kpoints.get_kpoints_mesh()[0],
            )
    ave_interval = np.average(kpoints_info['intervals'])

    return_vals = {}
    return_vals['interval'] = Float(ave_interval)
    return return_vals


@calcfunction
def get_kpoints_from_interval(structure, interval):
    """
    Get kpoints from interval.
    """
    cell = get_cell_from_aiida(structure)
    kpt_info = get_mesh_offset_from_direct_lattice(
            lattice=cell[0], interval=interval.value)
    mesh = kpt_info['mesh']
    offset = kpt_info['offset']
    kpt = KpointsData()
    kpt.set_kpoints_mesh(mesh, offset)
    return kpt
