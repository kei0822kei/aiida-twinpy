import numpy as np
from aiida.engine import calcfunction
from aiida.plugins import DataFactory
from aiida.orm import Int, Float
from aiida.orm.nodes.data import StructureData
from pymatgen.core.structure import Structure
# from twinpy.crystalmaker import is_hexagonal_metal, HexagonalTwin
# from twinpy.utils import get_nearest_neighbor_distance
from twinpy.structure import get_structure, HexagonalClosePacked

ArrayData = DataFactory('array')

@calcfunction
def get_sheared_structures(structure, twinmode, grids):
    pmgstructure = structure.get_pymatgen_structure()
    a = pmgstructure.lattice.a
    c = pmgstructure.lattice.c
    specie = pmgstructure.species[0].symbol
    parent = HexagonalClosePacked(a, c, specie)
    parent.set_parent(twinmode=twinmode.value)
    ratios = [ i / (int(grids)-1) for i in range(int(grids)) ]
    shears = [ get_structure(parent.get_sheared_structure(ratio=ratio))
                   for ratio in ratios ]

    return_vals = {}
    for i in range(len(ratios)):
        return_vals['gp_%02d' % (i+1) ] = \
            {
               'ratio':Float(ratios[i]),
               'structure':StructureData(pymatgen_structure=shears[i])
            }
    return return_vals

def get_hexagonal_twin_boudary_structure(structure,
                                         twinmode,
                                         twintype,
                                         dim,
                                         translation):
    a = structure.lattice.a
    c = structure.lattice.c
    symbol = structure.species[0].value
    hexagonal = HexagonalTwin(a=a, c=c, twinmode=twinmode, symbol=symbol)
    twinboundary = hexagonal.get_dichromatic(twintype=twintype,
                                             dim=dim,
                                             translation=translation,
                                             is_complex=True)
    return twinboundary

def create_grid_from_zero_to_one(grid_num):
    """
    array = np.array([grid1, grid2, grid3]) all int
    """
    print(type(grid_num))
    grids = []
    l = grid_num[0]
    m = grid_num[1]
    n = grid_num[2]
    for i in range(grid_num[0]):
        for j in range(grid_num[1]):
            for k in range(grid_num[2]):
                grids.append([i/l,j/m,k/n])
    return np.array(grids)
