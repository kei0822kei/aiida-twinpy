#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Deals with kpoints.
"""

import numpy as np
from aiida.orm import Dict, KpointsData, StructureData
from aiida.engine import calcfunction
from twinpy.lattice.lattice import Lattice
from aiida_twinpy.common.structure import get_cell_from_aiida


def get_mesh_from_interval(lattice:np.array,
                           interval:float) -> dict:
    """
    Get the nunmber of grid from lattice.

    Args:
        lattice (np.array): lattice matrix
        interval (float): grid interval

    Returns:
        dict: containing abc norms, mesh

    Note:
        mesh * interval => abc
        If even becomes zero, fix to one.
    """
    lat = Lattice(lattice=lattice)
    abc = lat.abc
    mesh_float = abc / interval
    mesh = np.int64(np.round(mesh_float))
    fixed_mesh = np.where(mesh==0, 1, mesh)
    return {'abc': abc, 'mesh': fixed_mesh}


def get_mesh_offset_from_direct_lattice(lattice:np.array,
                                        interval:float,
                                        include_two_pi:bool=True) -> dict:
    """
    Get kpoints mesh and offset from input lattice and interval.

    Args:
        lattice (np.array): lattice matrix
        interval (float): grid interval
        include_two_pi (bool): if True, include 2 * pi

    Returns:
        dict: containing abc norms, mesh, offset

    Note:
        If the angles of input lattice is (90., 90., 120.),
        offset is set (0., 0., 0.5) and mesh is set
        (odd, odd, even or 1).
        If even becomes zero, fix to one.
        Otherwise, set (0.5, 0.5, 0.5) and mesh is set
        (even or 1, even or 1, even or 1).
        If you use this function, it is better to input
        CONVENTIONAL STANDARDIZED CELL.
    """
    lat = Lattice(lattice=lattice)

    if include_two_pi:
        recip_lat = Lattice(2*np.pi*lat.reciprocal_lattice)
    else:
        recip_lat = Lattice(lat.reciprocal_lattice)

    kpts = get_mesh_from_interval(lattice=recip_lat.lattice,
                                  interval=interval)

    # is hexagonal standardized cell
    mesh = kpts['mesh']
    recip_a, recip_b, _ = recip_lat.abc
    is_hexagonal = (np.allclose(recip_lat.angles, (90., 90., 60.),
                                rtol=0., atol=1e-5)
                    and np.allclose(recip_a, recip_b,
                                    rtol=0., atol=1e-5)
                    )

    # fix mesh from get_mesh_from_interval
    if is_hexagonal:
        offset = (0., 0., 0.5)
        # If True, get 1, if False get 0.
        condition = lambda x: int(x%2==0)
        arr = [ condition(m) for m in mesh[:2] ]
        if (mesh[2]!=1 and mesh[2]%2==1):
            arr.append(1)
        else:
            arr.append(0)
        arr = np.array(arr)
    else:
        offset = (0.5, 0.5, 0.5)
        condition = lambda x: int(x!=1 and x%2==1)
        arr = np.array([ condition(m) for m in mesh ])
    fixed_mesh = mesh + arr
    kpts['mesh'] = fixed_mesh
    kpts['offset'] = offset

    kpts['is_hexagonal'] = is_hexagonal

    return kpts


@calcfunction
def get_kpoints_data_from_structure(structure:StructureData,
                                    dic:Dict) -> KpointsData:
    """
    Get aiida KpointsData from aiida StructureData.

    Args:
        structure (StructureData): aiida StructureData
        dic (Dict): aiida Dict containing necessary information

    Returns:
        KpointsData: aiida KpointsData

    Note:
    """
    cell = get_cell_from_aiida(structure)
    kpts_info = dic.get_dict()
    kpts = get_mesh_offset_from_direct_lattice(
             lattice=cell[0],
             interval=kptss_info['interval'],
             include_two_pi=kpts_info['include_two_pi'],
             )
    aiida_kpts = KpointsData()
    aiida_kpts.set_kpoints_mesh(mesh=kpts['mesh'],
                                offset=kpts['offset'])

    return_vals = {
            'kpoints': aiida_kpts,
            'kpoints_dict': Dict(dict=kpts),
            }
