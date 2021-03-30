#!usr/bin/env python

"""
This module deals with kpoints.
"""

from aiida.engine import calcfunction
from aiida.orm import Bool, Dict, StructureData
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
        kpoints_conf: Kpoints configuration. All keys are parsed to
                      twinpy.common.kpoints.Kpoints.
                      For more detailed information,
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
