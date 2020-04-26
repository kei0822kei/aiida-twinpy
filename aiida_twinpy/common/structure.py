#!usr/bin/env python

import numpy as np
from aiida.engine import calcfunction
from aiida.orm import Dict, Float
from aiida.orm.nodes.data import StructureData
from twinpy.structure.hexagonal import (
        is_hcp,
        get_atom_positions_from_lattice_points,
        HexagonalStructure)

def get_twinpy_structure_to_structure(twinpy_structure):
    symbols = twinpy_structure
    scaled_positions = get_atom_positions_from_lattice_points(
            twinpy_structure[1], twinpy_structure[2])
    structure = StructureData(cell=twinpy_structure[0])
    for symbol, scaled_position in zip(twinpy_structure[3], scaled_positions):
        position = np.dot(twinpy_structure[0].T,
                          scaled_position.reshape(3,1)).reshape(3)
        structure.append_atom(position=position, symbols=symbol)
    return structure

def get_twinpy_structure_from_structure(structure):
    lattice = np.array(structure.cell)
    positions = np.array([site.position for site in structure.sites])
    symbols = [site.kind_name for site in structure.sites]
    wyckoff = is_hcp(lattice=lattice,
                     positions=positions,
                     symbols=symbols,
                     get_wyckoff=True)
    return HexagonalStructure(lattice=lattice,
                              symbol=symbols[0],
                              wyckoff=wyckoff)

@calcfunction
def get_sheared_structures(structure, shear_conf):
    conf = dict(shear_conf)
    parent = get_twinpy_structure_from_structure(structure)
    parent.set_parent(twinmode=conf['twinmode'])
    ratios = [ i / (int(conf['grids'])-1) for i in range(int(conf['grids'])) ]
    strain = parent.shear_strain_function
    shears = []
    for ratio in ratios:
        parent.set_shear_ratio(ratio)
        parent.run(is_primitive=conf['is_primitive'])
        shears.append(get_twinpy_structure_to_structure(parent.output_structure))

    return_vals = {}
    shear_settings = {'shear_ratios': ratios}
    return_vals['shear_settings'] = Dict(dict=shear_settings)
    return_vals['strain'] = Float(abs(strain(parent.r)))
    for i in range(len(ratios)):
        shear = shears[i]
        shear.label = 'shear_%03d' % i
        shear.description = 'shear_%03d' % i + ' ratio: {}'.format(ratios[i])
        return_vals[shear.label] = shear
    return return_vals
