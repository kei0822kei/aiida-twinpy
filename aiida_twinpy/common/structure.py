#!usr/bin/env python

import numpy as np
from aiida.engine import calcfunction
from aiida.orm import Dict, Float, Int
from aiida.orm.nodes.data import StructureData
from aiida_twinpy.common.interfaces import get_phonon_from_aiida
from aiida_phonopy.common.utils import phonopy_atoms_to_structure
from twinpy.api_twinpy import get_twinpy_from_cell
from twinpy.structure.base import (
        is_hcp,
        get_atom_positions_from_lattice_points,
        )

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

def get_cell_from_aiida(structure, get_scaled_positions=True):
    """
    cell = (lattice, scaled_positions, symbols)
    """
    lattice = np.array(structure.cell)
    positions = np.array([site.position for site in structure.sites])
    if get_scaled_positions:
        positions = np.dot(np.linalg.inv(lattice.T), positions.T).T
    symbols = [site.kind_name for site in structure.sites]
    return (lattice, positions, symbols)

@calcfunction
def get_shear_structures(structure, shear_conf):
    conf = dict(shear_conf)
    cell = get_cell_from_aiida(structure,
                               get_scaled_positions=True)
    ratios = [ i / (int(conf['grids'])-1) for i in range(int(conf['grids'])) ]
    shear_structures = []
    for ratio in ratios:
        twinpy = get_twinpy_from_cell(cell=cell,
                                      twinmode=conf['twinmode'])
        twinpy.set_shear(xshift=conf['xshift'],
                         yshift=conf['yshift'],
                         dim=conf['dim'],
                         shear_strain_ratio=ratio)
        ph_structure = twinpy.get_shear_phonopy_structure(
                structure_type=conf['structure_type'])
        shear_structures.append(phonopy_atoms_to_structure(ph_structure))

    return_vals = {}
    shear_settings = {'shear_ratios': ratios}
    return_vals['shear_settings'] = Dict(dict=shear_settings)
    return_vals['gamma'] = Float(twinpy.get_shear().get_gamma())
    for i in range(len(ratios)):
        shear_structure = shear_structures[i]
        shear_structure.label = 'shear_%03d' % i
        shear_structure.description = 'shear_%03d' % i \
                                          + ' ratio: {}'.format(ratios[i])
        return_vals[shear_structure.label] = shear_structure
    return_vals['total_structures'] = Int(len(ratios))
    return return_vals

@calcfunction
def get_twinboundary_structure(structure, twinboundary_conf):
    conf = dict(twinboundary_conf)
    cell = get_cell_from_aiida(structure,
                               get_scaled_positions=True)
    twinpy = get_twinpy_from_cell(cell=cell,
                                  twinmode=conf['twinmode'])
    twinpy.set_twinboundary(twintype=conf['twintype'],
                            xshift=conf['xshift'],
                            yshift=conf['yshift'],
                            dim=conf['dim'],
                            shear_strain_ratio=conf['shear_strain_ratio'],
                            make_tb_flat=conf['make_tb_flat'],
                            )
    ph_structure = twinpy.get_twinboundary_phonopy_structure(
            structure_type=conf['structure_type'])

    structure = phonopy_atoms_to_structure(ph_structure)

    return structure

# @calcfunction
# def get_twinboundary_shear_structures(structure, twinboundary_shear_conf):
#     conf = dict(twinboundary_shear_conf)
#     cell = get_cell_from_aiida(structure,
#                                get_scaled_positions=True)
#     tb_structures = []
#     for shear_strain_ratio in conf['shear_strain_ratios']:
#         twinpy = get_twinpy_from_cell(cell=cell,
#                                       twinmode=conf['twinmode'])
#         twinpy.set_twinboundaty(twintype=conf['twintype'],
#                                 xshift=conf['xshift'],
#                                 yshift=conf['yshift'],
#                                 dim=conf['dim'],
#                                 )
#         twinpy.set_twinbou(xshift=conf['xshift'],
#                          yshift=conf['yshift'],
#                          dim=conf['dim'],
#                          shear_strain_ratio=shear_strain_ratio,
#                          make_tb_flat=conf['make_tb_flat'])
#         ph_structure = twinpy.get_twinboundary_phonopy_structure(
#                 structure_type=conf['structure_type'])
#         tb_structures.append(phonopy_atoms_to_structure(ph_structure))
# 
#     return_vals = {}
#     twinboundary_settings = {'shear_ratios': conf['shear_strain_ratios']}
#     return_vals['twinboundary_settings'] = Dict(dict=twinboundary_settings)
#     return_vals['gamma'] = Float(twinpy.get_shear().get_gamma())
#     for i, ratio in enumerate(conf['shear_strain_ratios']):
#         tb_structure = tb_structures[i]
#         tb_structure.label = 'twinboundary_%03d' % i
#         tb_structure.description = 'twinboundary_%03d' % i \
#                                           + ' ratio: {}'.format(ratio)
#         return_vals[tb_structure.label] = tb_structure
#     return_vals['total_structures'] = Int(len(conf['shear_strain_ratios']))
#     return return_vals

# @calcfunction
# def get_twinboundary_shear_structures(structure, twinboundary_shear_conf):
#     conf = dict(twinboundary_shear_conf)
#     lattice, positions, symbols = get_structure_from_aiida(structure)
#     ratios = twinboundary_shear_conf['ratios']
#     shears = []
#     for ratio in ratios:
#         shear_mat = np.eye(3)
#         shear_mat[1,2] = ratio
#         shear_lat = np.dot(lattice.T, shear_mat).T
#         scaled_positions = np.dot(np.linalg.inv(lattice.T), positions.T).T
#         shears.append(get_aiida_structure(cell=(shear_lat, scaled_positions, symbols)))
# 
#     return_vals = {}
#     shear_settings = {'shear_ratios': ratios}
#     return_vals['shear_settings'] = Dict(dict=shear_settings)
#     for i in range(len(ratios)):
#         shear = shears[i]
#         shear.label = 'twinboundaryshear_%03d' % i
#         shear.description = 'twinboundaryshear_%03d' % i + ' ratio: {}'.format(ratios[i])
#         return_vals[shear.label] = shear
#     return return_vals
# 
# @calcfunction
# def get_twinboundary_structures(structure, twinboundary_conf):
#     conf = dict(twinboundary_conf)
#     parent = get_twinpy_structure_from_structure(structure)
#     parent.set_parent(twinmode=conf['twinmode'])
#     parent.set_twintype(twintype=conf['twintype'])
#     parent.set_dimension(dim=conf['dim'])
#     xshifts = [ i / int(conf['xgrids']) for i in range(int(conf['xgrids'])) ]
#     yshifts = [ i / int(conf['ygrids']) for i in range(int(conf['ygrids'])) ]
#     strain = parent.shear_strain_function
#     twinboundaries = []
#     shifts = []
#     for xshift in xshifts:
#         tb = []
#         for yshift in yshifts:
#             parent.set_xshift(xshift)
#             parent.set_yshift(yshift)
#             parent.run()
#             tb.append(get_aiida_structure(
#                 parent.get_structure_for_export(get_lattice=False)))
#             shifts.append([xshift, yshift])
#         twinboundaries.append(tb)
# 
#     return_vals = {}
#     twinboundary_summary = {'shifts': shifts, 'natoms': parent.natoms}
#     return_vals['twinboundary_summary'] = Dict(dict=twinboundary_summary)
#     return_vals['strain'] = Float(abs(strain(parent.r)))
#     count = 0
#     for i in range(len(xshifts)):
#         for j in range(len(yshifts)):
#             twinboundary = twinboundaries[i][j]
#             twinboundary.label = 'twinboundary_%03d' % count
#             twinboundary.description = 'twinboundary_%03d' % count + \
#                     ' xshift: {} yshift: {}'.format(xshifts[i], yshifts[j])
#             return_vals[twinboundary.label] = twinboundary
#             count += 1
#     return_vals['total_structures'] = Int(count)
#     return return_vals

@calcfunction
def get_modulation_structures(modulation_conf):
    conf = modulation_conf.get_dict()
    phonon = get_phonon_from_aiida(conf['phonon_pk'])
    freq = []
    for phonon_mode in conf['phonon_modes']:
        freq.append(phonon.get_frequencies(phonon_mode[0]).tolist())

    unitcell = phonon.get_unitcell().cell
    primitive = phonon.get_primitive().cell
    u2p = np.round(np.dot(np.linalg.inv(primitive.T), unitcell.T)).astype(int)
    dimension = np.dot(u2p, conf['dimension'])
    phonon.set_modulations(dimension=dimension,
                           phonon_modes=conf['phonon_modes'])
    modulations = phonon.get_modulated_supercells()

    return_vals = {}
    return_vals['frequencies'] = Dict(dict={'frequencies': freq})
    for i, supercell in enumerate(modulations):
        modulation = phonopy_atoms_to_structure(supercell)
        modulation.label = 'modulation_%03d' % (i+1)
        modulation.description = 'modulation_%03d' % (i+1)
        return_vals[modulation.label] = modulation
    return return_vals
