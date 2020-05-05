#!usr/bin/env python

import numpy as np
from aiida.engine import calcfunction
from aiida.orm import Dict, Float, Int
from aiida.orm.nodes.data import StructureData
from aiida_twinpy.common.interfaces import get_phonon_from_aiida
from aiida_phonopy.common.utils import phonopy_atoms_to_structure
from twinpy.structure.hexagonal import (
        is_hcp,
        get_atom_positions_from_lattice_points,
        HexagonalStructure)

def get_aiida_structure(cell):
    """
    cell = (lattice, scaled_positions, symbols)
    """
    structure = StructureData(cell=cell[0])
    for symbol, scaled_position in zip(cell[2], cell[1]):
        position = np.dot(cell[0].T,
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
    parent.set_is_primitive(conf['is_primitive'])
    ratios = [ i / (int(conf['grids'])-1) for i in range(int(conf['grids'])) ]
    strain = parent.shear_strain_function
    shears = []
    for ratio in ratios:
        parent.set_shear_ratio(ratio)
        parent.run()
        shears.append(get_aiida_structure(
            parent.get_structure_for_export(get_lattice=False)))

    return_vals = {}
    shear_settings = {'shear_ratios': ratios}
    return_vals['shear_settings'] = Dict(dict=shear_settings)
    return_vals['strain'] = Float(abs(strain(parent.r)))
    for i in range(len(ratios)):
        shear = shears[i]
        shear.label = 'shear_%03d' % i
        shear.description = 'shear_%03d' % i + ' ratio: {}'.format(ratios[i])
        return_vals[shear.label] = shear
    return_vals['total_structures'] = Int(len(ratios))
    return return_vals

@calcfunction
def get_twinboundary_structures(structure, twinboundary_conf):
    conf = dict(twinboundary_conf)
    parent = get_twinpy_structure_from_structure(structure)
    parent.set_parent(twinmode=conf['twinmode'])
    parent.set_twintype(twintype=conf['twintype'])
    parent.set_dimension(dim=conf['dim'])
    xshifts = [ i / int(conf['xgrids']) for i in range(int(conf['xgrids'])) ]
    yshifts = [ i / int(conf['ygrids']) for i in range(int(conf['ygrids'])) ]
    strain = parent.shear_strain_function
    twinboundaries = []
    shifts = []
    for xshift in xshifts:
        tb = []
        for yshift in yshifts:
            parent.set_xshift(xshift)
            parent.set_yshift(yshift)
            parent.run()
            tb.append(get_aiida_structure(
                parent.get_structure_for_export(get_lattice=False)))
            shifts.append([xshift, yshift])
        twinboundaries.append(tb)

    return_vals = {}
    twinboundary_summary = {'shifts': shifts, 'natoms': parent.natoms}
    return_vals['twinboundary_summary'] = Dict(dict=twinboundary_summary)
    return_vals['strain'] = Float(abs(strain(parent.r)))
    count = 0
    for i in range(len(xshifts)):
        for j in range(len(yshifts)):
            twinboundary = twinboundaries[i][j]
            twinboundary.label = 'twinboundary_%03d' % count
            twinboundary.description = 'twinboundary_%03d' % count + \
                    ' xshift: {} yshift: {}'.format(xshifts[i], yshifts[j])
            return_vals[twinboundary.label] = twinboundary
            count += 1
    return_vals['total_structures'] = Int(count)
    return return_vals

@calcfunction
def get_modulation_structures(modulation_conf):
    conf = modulation_conf.get_dict()
    phonon = get_phonon_from_aiida(conf['phonon_pk'])
    phonon.set_modulations(dimension=phonon.supercell_matrix,
                           phonon_modes=conf['phonon_modes'])
    modulations = phonon.get_modulated_supercells()

    return_vals = {}
    for i, supercell in enumerate(modulations):
        modulation = phonopy_atoms_to_structure(supercell)
        modulation.label = 'modulation_%03d' % (i+1)
        modulation.description = 'modulation_%03d' % (i+1)
        return_vals[modulation.label] = modulation
    return return_vals
