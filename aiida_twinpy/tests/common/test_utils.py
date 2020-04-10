#!/usr/bin/env python

import unittest
import numpy as np
from copy import deepcopy
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from aiida.engine import submit
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm.nodes.data import Dict, Str, StructureData, KpointsData
from aiida_twinpy.common.utils import get_sheared_structures
from twinpy.structure import get_pymatgen_structure, HexagonalClosePacked

@with_dbenv()
def get_structuredata(pmgstructure):
    structure = StructureData(pymatgen_structure=pmgstructure)
    structure.label = "hexagonal Ti"
    structure.description = "hexagonal Ti, for common/utiles.py test"
    structure.store()
    return structure

@with_dbenv()
class TestGetShearedStructure(unittest.TestCase):

    def setUp(self):
        self.shear_conf = {
                'twinmode': '10-12',
                # 'grids': 2,
                'grids': 7,
                'structure_type': 'primitive', # or 'conventional' or ''
                }
        hexagonal = HexagonalClosePacked(a=2.93,
                                         c=4.65,
                                         specie='Ti',
                                         wyckoff='c')
        self.hexaognal = get_structuredata(get_pymatgen_structure(hexagonal))
        self.return_vals = get_sheared_structures(
                               structure=self.hexaognal,
                               shear_conf=Dict(dict=self.shear_conf),
                               )

    def tearDown(self):
        pass

    def test_check_wyckoff(self):
        print("")
        print("-----------------------------")
        print("ckech wyckoff has not changed")
        print("-----------------------------")
        names = ['parent', 'shear_000']
        # names = ['shear_000']
        for name in names:
            print("test %s " % name)
            analyzer = SpacegroupAnalyzer(self.return_vals[name].get_pymatgen())
            self.assertEqual(analyzer.get_symmetry_dataset()['wyckoffs'][0], 'c')

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGetShearedStructure)
    unittest.TextTestRunner(verbosity=2).run(suite)
