#!/usr/bin/env python

import unittest
from pprint import pprint
import numpy as np
from copy import deepcopy
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from aiida.engine import submit
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm.nodes.data import Dict, Str, StructureData, KpointsData
from twinpy.structure.base import get_hexagonal_cell
from aiida_twinpy.common.structure import (get_aiida_structure,
                                           get_cell_from_aiida,
                                           get_twinboundary_structure)
# from aiida_twinpy.common.utils import get_sheared_structures
# from twinpy.structure import get_pymatgen_structure, HexagonalClosePacked

def unpack_aiida_objects(node):
    if type(node) == Dict:
        return node.get_dict()
    elif type(node) == StructureData:
        cell = get_cell_from_aiida(node)
        return "Future edited."
    else:
        return node.value


@with_dbenv()
class TestGetTwinBoundaryStructure(unittest.TestCase):

    def setUp(self):
        twinboundary_conf = Dict(dict={
            'twinmode': '10-12',
            'twintype': 1,
            'layers': 9,
            'delta': 0.06,
            'xshift': 0.,
            'yshift': 0.,
            'shear_strain_ratio': 0.,
            })
        cell = get_hexagonal_cell(a=2.93, c=4.65, symbol='Ti', wyckoff='c')
        self.hexagonal = get_aiida_structure(cell=cell)
        self.twinboundary_conf = twinboundary_conf

    def tearDown(self):
        pass

    def test_builder_twinboundary_structure(self):
        print("")
        print("# -------------------------------------")
        print("# check: def get_twinboundary_structure")
        print("# -------------------------------------")
        return_vals = get_twinboundary_structure(
                structure=self.hexagonal,
                twinboundary_conf=self.twinboundary_conf)
        print("return_vals:")
        for key in return_vals.keys():
            print("# %s" % key)
            pprint(unpack_aiida_objects(return_vals[key]))
        print("# --------------------------------------")
        print("# finish: def get_twinboundary_structure")
        print("# --------------------------------------")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGetTwinBoundaryStructure)
    unittest.TextTestRunner(verbosity=2).run(suite)

# @with_dbenv()
# class TestGetShearedStructure(unittest.TestCase):
# 
#     def setUp(self):
#         self.shear_conf = {
#                 'twinmode': '10-12',
#                 # 'grids': 2,
#                 'grids': 7,
#                 'structure_type': 'primitive', # or 'conventional' or ''
#                 }
#         hexagonal = HexagonalClosePacked(a=2.93,
#                                          c=4.65,
#                                          specie='Ti',
#                                          wyckoff='c')
#         self.hexaognal = get_structuredata(get_pymatgen_structure(hexagonal))
#         self.return_vals = get_sheared_structures(
#                                structure=self.hexaognal,
#                                shear_conf=Dict(dict=self.shear_conf),
#                                )
# 
#     def tearDown(self):
#         pass
# 
#     def test_check_wyckoff(self):
#         print("")
#         print("-----------------------------")
#         print("ckech wyckoff has not changed")
#         print("-----------------------------")
#         names = ['parent', 'shear_000']
#         # names = ['shear_000']
#         for name in names:
#             print("test %s " % name)
#             analyzer = SpacegroupAnalyzer(self.return_vals[name].get_pymatgen())
#             self.assertEqual(analyzer.get_symmetry_dataset()['wyckoffs'][0], 'c')
# 
# if __name__ == '__main__':
#     suite = unittest.TestLoader().loadTestsFromTestCase(TestGetShearedStructure)
#     unittest.TextTestRunner(verbosity=2).run(suite)
# 
# @with_dbenv()
# class TestGetShearedStructure(unittest.TestCase):
# 
#     def setUp(self):
#         self.shear_conf = {
#                 'twinmode': '10-12',
#                 # 'grids': 2,
#                 'grids': 7,
#                 'structure_type': 'primitive', # or 'conventional' or ''
#                 }
#         hexagonal = HexagonalClosePacked(a=2.93,
#                                          c=4.65,
#                                          specie='Ti',
#                                          wyckoff='c')
#         self.hexaognal = get_structuredata(get_pymatgen_structure(hexagonal))
#         self.return_vals = get_sheared_structures(
#                                structure=self.hexaognal,
#                                shear_conf=Dict(dict=self.shear_conf),
#                                )
# 
#     def tearDown(self):
#         pass
# 
#     def test_check_wyckoff(self):
#         print("")
#         print("-----------------------------")
#         print("ckech wyckoff has not changed")
#         print("-----------------------------")
#         names = ['parent', 'shear_000']
#         # names = ['shear_000']
#         for name in names:
#             print("test %s " % name)
#             analyzer = SpacegroupAnalyzer(self.return_vals[name].get_pymatgen())
#             self.assertEqual(analyzer.get_symmetry_dataset()['wyckoffs'][0], 'c')
# 
# if __name__ == '__main__':
#     suite = unittest.TestLoader().loadTestsFromTestCase(TestGetShearedStructure)
#     unittest.TextTestRunner(verbosity=2).run(suite)
# 
# @with_dbenv()
# class TestGetShearedStructure(unittest.TestCase):
# 
#     def setUp(self):
#         self.shear_conf = {
#                 'twinmode': '10-12',
#                 # 'grids': 2,
#                 'grids': 7,
#                 'structure_type': 'primitive', # or 'conventional' or ''
#                 }
#         hexagonal = HexagonalClosePacked(a=2.93,
#                                          c=4.65,
#                                          specie='Ti',
#                                          wyckoff='c')
#         self.hexaognal = get_structuredata(get_pymatgen_structure(hexagonal))
#         self.return_vals = get_sheared_structures(
#                                structure=self.hexaognal,
#                                shear_conf=Dict(dict=self.shear_conf),
#                                )
# 
#     def tearDown(self):
#         pass
# 
#     def test_check_wyckoff(self):
#         print("")
#         print("-----------------------------")
#         print("ckech wyckoff has not changed")
#         print("-----------------------------")
#         names = ['parent', 'shear_000']
#         # names = ['shear_000']
#         for name in names:
#             print("test %s " % name)
#             analyzer = SpacegroupAnalyzer(self.return_vals[name].get_pymatgen())
#             self.assertEqual(analyzer.get_symmetry_dataset()['wyckoffs'][0], 'c')

# if __name__ == '__main__':
#     suite = unittest.TestLoader().loadTestsFromTestCase(TestGetShearedStructure)
#     unittest.TextTestRunner(verbosity=2).run(suite)
