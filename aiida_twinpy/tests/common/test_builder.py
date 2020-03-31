#!/usr/bin/env python

import unittest
import numpy as np
from copy import deepcopy
from pymatgen.core.lattice import Lattice
from pymatgen.core.structure import Structure
from aiida.engine import submit
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm.nodes.data import Dict, Str, StructureData, KpointsData
from aiida_twinpy.common.builder import (get_vasp_builder,
                                         get_relax_builder,
                                         get_phonon_builder)

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
        pmgstructure = Structure(
                lattice=Lattice.hexagonal(a=2.93, c=4.65),
                coords=[[1/3, -1/3, -1/4], [-1/3, 1/3, 1/4]],
                species=['Ti']*2)
        self.structure = get_structuredata(pmgstructure)
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
        self.queue = ''
        self.vaspcode = 'vasp544mpi'
        self.potential_family = 'PBE.54'
        self.potential_mapping = {'Ti': 'Ti_pv'}
        self.kpoints = {'mesh': [18, 18, 10],
                        'offset': [0, 0, 0.5]}

    def tearDown(self):
        pass

    def test_get_vasp_builder(self):
        label = description = "test 'get_vasp_builder'"
        incar_settings = deepcopy(self.incar_settings)
        incar_settings.update(self.relax_settings)
        kpt = KpointsData()
        kpt.set_kpoints_mesh(self.kpoints['mesh'],
                             offset=self.kpoints['offset'])
        print("")
        print("----------------")
        print("get_vasp_builder")
        print("----------------")
        builder = get_vasp_builder(
            label=label,
            description=description,
            computer=Str(self.computer),
            structure=self.structure,
            incar_settings=Dict(dict=incar_settings),
            kpoints=kpt,
            potential_family=Str(self.potential_family),
            potential_mapping=Dict(dict=self.potential_mapping),
            queue=Str(self.queue)
            )
        future = submit(builder)
        print('Running workchain with pk={}'.format(future.pk))
        print("--------------------")
        print("get_vasp_builder END")
        print("--------------------")

    def test_get_relax_builder(self):
        label = description = "test 'get_relax_builder'"
        kpt = KpointsData()
        kpt.set_kpoints_mesh(self.kpoints['mesh'],
                             offset=self.kpoints['offset'])
        print("")
        print("-----------------")
        print("get_relax_builder")
        print("-----------------")
        relax_conf = {
            'perform': True,
            'positions': True,
            'volume': True,
            'shape': True,
            'algo': 'rd',  # you can also choose 'cg' (default)
            'steps': 20,
            'convergence_absolute': False,
            'convergence_max_iterations': 5,
            'convergence_on': True,
            'convergence_positions': 0.01,
            'convergence_shape_angles': 0.1,
            'convergence_shape_lengths': 0.1,
            'convergence_volume': 0.01,
            'force_cutoff': 0.001,  # or 'energy_cutoff': 1e-4,
            }
        builder = get_relax_builder(
            label=label,
            description=description,
            calc_type='relax',
            computer=Str(self.computer),
            incar_settings=Dict(dict=self.incar_settings),
            kpoints=kpt,
            potential_family=Str(self.potential_family),
            potential_mapping=Dict(dict=self.potential_mapping),
            relax_conf=Dict(dict=relax_conf),
            structure=self.structure,
            queue=Str(self.queue)
            )
        future = submit(builder)
        print(future)
        print('Running workchain with pk={}'.format(future.pk))
        print("---------------------")
        print("get_relax_builder END")
        print("---------------------")

    def test_get_phonon_builder(self):
        print("")
        print("------------------")
        print("get_phonon_builder")
        print("------------------")
        label = description = "test 'get_phonon_builder'"
        phonon_settings = \
             Dict(dict={
                 'distance': 0.03,
                 'mesh': [13, 13, 13],
                 'is_nac': False,
                 'supercell_matrix': [2, 2, 2],
                 'symmetry_tolerance': 1e-5
             })
        vasp_settings = \
             Dict(dict={
                 'vasp_code': 'vasp544mpi',
                 'kpoints_mesh': [9, 9, 6],
                 'kpoints_offset': self.kpoints['offset'],
                 'potential_family': self.potential_family,
                 'potential_mapping': self.potential_mapping,
                 'incar_settings': self.incar_settings
             })
        builder = get_phonon_builder(
            label=label,
            description=description,
            computer=Str(self.computer),
            structure=self.structure,
            phonon_settings=phonon_settings,
            vasp_settings=vasp_settings,
            queue=Str(self.queue)
            )
        future = submit(builder)
        print('Running workchain with pk={}'.format(future.pk))
        print("----------------------")
        print("get_phonon_builder END")
        print("----------------------")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBuilder)
    unittest.TextTestRunner(verbosity=2).run(suite)
