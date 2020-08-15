#!/usr/bin/env python

import unittest
from aiida.orm import Dict
from aiida.cmdline.utils.decorators import with_dbenv
from twinpy.structure.base import get_hexagonal_cell
from aiida_twinpy.common.kpoints import get_kpoints_data_from_structure
from aiida_twinpy.common.structure import get_aiida_structure


@with_dbenv()
class TestKpoints(unittest.TestCase):

    def setUp(self):
        self._hcp_structure = get_hexagonal_cell(a=2.93,
                                                 c=4.65,
                                                 symbol='Ti',
                                                 wyckoff='c')

    def tearDown(self):
        pass

    def test_get_kpoints_data_from_structure(self):
        print("")
        print("-------------------------------")
        print("get_kpoints_data_from_structure")
        print("-------------------------------")
        structure = get_aiida_structure(cell=self._hcp_structure)
        kpts_info = Dict(dict={'interval': 0.15, 'include_two_pi': True})
        return_vals = get_kpoints_data_from_structure(
                structure=structure, dic=kpts_info)
        print("KpointsData pk: {}".format(return_vals['kpoints'].pk))
        print("kpoints_dict Dict pk: {}".format(
            return_vals['kpoints_dict'].pk))
        print("-------------------------------------")
        print("get_kpoints_data_from_structure (END)")
        print("-------------------------------------")


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKpoints)
    unittest.TextTestRunner(verbosity=2).run(suite)
