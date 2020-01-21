import numpy as np
from aiida.engine import calcfunction
from aiida.plugins import DataFactory
from aiida.orm import Int, Float
from aiida.orm.nodes.data import StructureData
from pymatgen.core.structure import Structure
from twinpy.crystalmaker import is_hexagonal_metal, Hexagonal
from twinpy.utils import get_nearest_neighbor_distance

ArrayData = DataFactory('array')

@calcfunction
def get_hexagonal_twin_boudary_structures(aiidastructure,
                                          twinmode,
                                          twintype,
                                          dim,
                                          translation_grids):
    return_vals = {}

    grids_array = translation_grids.get_array(
            translation_grids.get_arraynames()[0])
    translations = create_grid_from_zero_to_one(grids_array)
    translations_array = ArrayData()
    translations_array.set_array('grid_points', translations)
    return_vals['grid_points'] = translations_array
    return_vals['total_structures'] = Int(len(translations))

    pmgstructure = aiidastructure.get_pymatgen_structure()
    dimension = dim.get_array(dim.get_arraynames()[0])
    for i, translation in enumerate(translations):
        tb_structure = get_hexagonal_twin_boudary_structure(
                           pmgstructure,
                           twinmode.value,
                           twintype.value,
                           dimension,
                           translation
                       )
        neighbor_distance = get_nearest_neighbor_distance(tb_structure)
        aiida_tbstructure = StructureData(pymatgen_structure=tb_structure)
        return_vals['neighbor_distance_%03d' % (i+1) ] = Float(neighbor_distance)
        return_vals['twinboundary_%03d' % (i+1) ] = aiida_tbstructure

    return return_vals

def get_hexagonal_twin_boudary_structure(structure,
                                         twinmode,
                                         twintype,
                                         dim,
                                         translation):

    hexagonal = Hexagonal(structure, twinmode)
    twinboundary = hexagonal.get_twin_boundary(twintype,
                                               dim,
                                               translation)
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
