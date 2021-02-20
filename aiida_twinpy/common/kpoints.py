#!usr/bin/env python

"""
This module deals with kpoints.
"""

import numpy as np
from aiida.engine import calcfunction
from aiida.orm import Bool, Float, Dict, KpointsData, StructureData
from twinpy.interfaces.aiida.base import get_cell_from_aiida
from twinpy.common.kpoints import Kpoints
from twinpy.structure.lattice import CrystalLattice


@calcfunction
def fix_kpoints(calculator_settings:Dict,
                structure:StructureData,
                kpoints_conf:Dict,
                is_phonon:Bool) -> Dict:
    """
    Fix kpoints using kpoints interval.

    Args:
        calculator_settings: Calculator settings for relax or phonon.
        structure: Original structure.
        kpoints_conf: Kpoints configuration. For more detailed information,
                      see Examples and def get_mesh_offget_auto
                      in twinpy.common.kpoints.Kpoints class.
        is_phonon: Input calculator_settings are for relax or phonon.

    Examples:
        Example of kpoints_conf is as bellow.

        >>> kpoints_conf = Dict(dict={
        >>>     'interval': 0.15,
        >>>     'decimal_handling': 'round',
        >>>     'use_symmetry': True,
        >>>     })

        >>> # following settings are automatically set
        >>> dim = [1, 1, 1]
        >>> xshift = 0.
        >>> yshift = 0.
        >>> is_primitive = True
        >>> to_primitive = True
        >>> get_lattice = False
        >>> move_atoms_into_unitcell = True
        >>> no_idealize = False
        >>> symprec = 1e-5
        >>> no_sort = True
        >>> get_sort_list = False

    Returns:
        Dict: Fixed calculator settings.
    """
    lattice = get_cell_from_aiida(structure)[0]
    if is_phonon:
        run_mode = 'phonon'
        dim = calculator_settings[run_mode]['phonon_conf']['supercell_matrix']
        input_lattice = CrystalLattice(lattice).get_expanded_lattice(dim)
    else:
        run_mode = 'relax'
        input_lattice = lattice

    twinpy_kpt = Kpoints(lattice=input_lattice)
    mesh, offset = twinpy_kpt.get_mesh_offset_auto(**kpoints_conf)
    kpoints = {'mesh': mesh, 'offset': offset}
    calc_settings = calculator_settings.get_dict()
    calc_settings[run_mode]['kpoints'] = kpoints
    return_vals = {}
    return_vals['calculator_settings'] = Dict(dict=calc_settings)

    return return_vals


# @calcfunction
# def get_kpoints_interval(structure, kpoints):
#     """
#     Get kpoints interval.
#     """
#     cell = get_cell_from_aiida(structure)
#     kpoints_info = get_mesh_offset_from_direct_lattice(
#             lattice=cell[0],
#             mesh=kpoints.get_kpoints_mesh()[0],
#             )
#     ave_interval = np.average(kpoints_info['intervals'])
# 
#     return_vals = {}
#     return_vals['interval'] = Float(ave_interval)
#     return return_vals
# 
# 
# @calcfunction
# def get_kpoints_from_interval(structure, interval):
#     """
#     Get kpoints from interval.
#     """
#     cell = get_cell_from_aiida(structure)
#     kpt_info = get_mesh_offset_from_direct_lattice(
#             lattice=cell[0], interval=interval.value)
#     mesh = kpt_info['mesh']
#     offset = kpt_info['offset']
#     kpt = KpointsData()
#     kpt.set_kpoints_mesh(mesh, offset)
#     return kpt
