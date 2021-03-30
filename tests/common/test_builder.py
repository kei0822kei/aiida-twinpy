#!/usr/bin/env python

import unittest
import numpy as np
from copy import deepcopy
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure
from aiida.engine import submit
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm.nodes.data import Dict, Str, StructureData, KpointsData
from aiida_twinpy.common.builder import get_calcjob_builder
from twinpy.structure import get_pymatgen_structure, HexagonalClosePacked

@with_dbenv()
def get_structuredata(pmgstructure):
    structure = StructureData(pymatgen_structure=pmgstructure)
    structure.label = "hexagonal Ti"
    structure.description = "hexagonal Ti, for common/builder.py test"
    structure.store()
    return structure

@with_dbenv()
class TestBuilder(unittest.TestCase):

    def setUp(self):
        twin_structure = HexagonalClosePacked(a=2.93, c=4.65, specie='Ti')
        twin_structure.set_parent(twinmode='10-12')
        parent = twin_structure.get_parent_structure()
        self.structure = get_structuredata(get_pymatgen_structure(parent))
        self.incar_settings = \
                 {
                    'addgrid': True,
                    'ediff': 1e-6,
                    'encut': 300,
                    'gga': 'PS',
                    'ialgo': 38,
                    'lcharg': False,
                    'lreal': False,
                    'lwave': False,
                    'npar': 4,
                    'prec': 'Accurate',
                    'ismear': 1,
                    'sigma': 0.4,
                 }
        self.relax_settings = \
                {
                   'nsw': 40,
                   'ibrion': 2,
                   'isif': 3,
                   'ediffg': -1e-4
                }
        self.computer = 'stern'
        self.queue_name = ''
        self.vasp_code = 'vasp544mpi'
        self.potential_family = 'PBE.54'
        self.potential_mapping = {'Ti': 'Ti_pv'}
        self.kpoints_relax = {'mesh': [10, 4, 4],
                              'offset': [0.5, 0.5, 0.5]}
        self.kpoints_phonon = {'mesh': [5, 2, 2],
                               'offset': [0.5, 0.5, 0.5]}
        self.relax_conf = {
            # set automatically => 'perform': True,
            # set automatically => 'positions': True,
            # set automatically => 'volume': False,
            # set automatically => 'shape': False,
            # 'algo': 'cg',  # you can also choose 'rd'
            'steps': 20,
            'convergence_absolute': False,
            'convergence_max_iterations': 2,
            'convergence_on': True,
            'convergence_positions': 0.01,
            'convergence_shape_angles': 0.1,
            'convergence_shape_lengths': 0.1,
            'convergence_volume': 0.01,
            'force_cutoff': 0.001,  # or 'energy_cutoff': 1e-4,
            }
        self.phonon_conf =  {
                'distance': 0.03,
                'phonopy_mesh': [13,13,13],
                'supercell_matrix': [2,2,2],
                'symmetry_tolerance': 1e-5,
                # set automatically => 'is_nac': False
                       }
        self.max_wallclock_seconds = 10 * 3600
        self.clean_workdir = True

    def tearDown(self):
        pass

    def get_calculator_settings(self):
        calculator_settings = {
            'relax': {
                'vasp_code': self.vasp_code,
                'incar_settings': self.incar_settings,
                'potential_family': self.potential_family,
                'potential_mapping': self.potential_mapping,
                'kpoints': self.kpoints_relax,
                'options': {'queue_name': self.queue_name,
                            'max_wallclock_seconds': self.max_wallclock_seconds},
                'relax_conf': self.relax_conf,
                'clean_workdir': self.clean_workdir,
            },
            'phonon': {
                'vasp_code': self.vasp_code,
                'incar_settings': self.incar_settings,
                'potential_family': self.potential_family,
                'potential_mapping': self.potential_mapping,
                'kpoints': self.kpoints_phonon,
                'options': {'queue_name': self.queue_name,
                            'max_wallclock_seconds': self.max_wallclock_seconds},
                'phonon_conf': self.phonon_conf
            },
        }
        return calculator_settings

    def test_get_relax_builder(self):
        print("")
        print("---------------------------")
        print("get_calcjob_builder (relax)")
        print("---------------------------")
        label = description = "test 'get_calcjob_builder' (relax)"
        calculator_settings = self.get_calculator_settings()
        builder = get_calcjob_builder(
            label=label,
            description=description,
            calc_type='relax',
            computer=Str(self.computer),
            structure=self.structure,
            calculator_settings=calculator_settings
            )
        future = submit(builder)
        print(future)
        print('Running workchain with pk={}'.format(future.pk))
        print("-------------------------------")
        print("get_calcjob_builder (relax) END")
        print("-------------------------------")

    def test_get_phonon_builder(self):
        print("")
        print("----------------------------")
        print("get_calcjob_builder (phonon)")
        print("----------------------------")
        label = description = "test 'get_calcjob_builder' (phonon)"
        calculator_settings = self.get_calculator_settings()
        builder = get_calcjob_builder(
            label=label,
            description=description,
            calc_type='phonon',
            computer=Str(self.computer),
            structure=self.structure,
            calculator_settings=calculator_settings
            )
        future = submit(builder)
        print(future)
        print('Running workchain with pk={}'.format(future.pk))
        print("--------------------------------")
        print("get_calcjob_builder (phonon) END")
        print("--------------------------------")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBuilder)
    unittest.TextTestRunner(verbosity=2).run(suite)
