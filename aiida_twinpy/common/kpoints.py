#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Deals with kpoints.
"""

import numpy as np
from decimal import Decimal, ROUND_HALF_UP
from twinpy.lattice.lattice import Lattice


def round_off(x:float):
    """
    Round off for input value 'x'.

    Args:
        x (float): some value

    Returns:
        int: rouned off value

    Examples:
        >>> round_off(4.5)
            5
        >>> round_off(-4.5)
            -5
    """
    return int(Decimal(str(x)).quantize(Decimal('0'), rounding=ROUND_HALF_UP))


def get_mesh_from_interval(lattice:np.array,
                           interval:float):
    """
    Get the nunmber of grid from lattice.

    Args:
        lattice (np.array): lattice matrix
        interval (float): grid interval

    Returns:
        dict: containing abc norms, mesh and actual intervals

    Note:
        mesh * interval => abc
        If even becomes zero, fix to one.
    """
    lat = Lattice(lattice=lattice)
    abc = lat.abc
    mesh_float = abc / interval
    mesh = np.int64(np.round(mesh_float))
    fixed_mesh = np.where(mesh==0, 1, mesh)
    intervals = abc / fixed_mesh
    return {'abc': abc, 'mesh': fixed_mesh, 'intervals': intervals}


def get_mesh_offset_from_direct_lattice(lattice:np.array,
                                        interval:float,
                                        include_two_pi:bool=True):
    """
    Get kpoints mesh and offset from input lattice and interval.

    Args:
        lattice (np.array): lattice matrix
        interval (float): grid interval
        include_two_pi (bool): if True, include 2 * pi

    Returns:
        dict: containing abc norms, mesh, offset and actual intervals

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
    is_hexagonal_std = (np.allclose(recip_lat.angles, (90., 90., 60.),
                                    rtol=0., atol=1e-5)
                        and np.allclose(recip_a, recip_b,
                                        rtol=0., atol=1e-5)
                        )

    # fix mesh from get_mesh_from_interval
    if is_hexagonal_std:
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

    kpts['is_hexagonal_standardized'] = is_hexagonal_std

    return kpts
