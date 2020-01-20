# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Usage: verdi run submit.py
"""

vasp_params = {}
vasp_params['description'] = "description",
vasp_params['label'] = "label",
vasp_params['computer'] = 'stern',
vasp_params['clean_workdir'] = False,
vasp_params['queue'] = None,
vasp_params['kpoints'] = {
        'mesh': [6,6,6],
        'offset': [0.5,0.5,0.5]
        },
vasp_params['options'] = {
        'max_wallclock_seconds': 36000,
        'tot_num_mpiprocs': 16
        }
vasp_params['incar'] = {
    'addgrid': True,
    'ediff': 1.0e-06,
    'encut': 375,
    'gga': 'PS',
    'ialgo': 38,
    'ismear': 0,
    'lcharg': False,
    'lreal': False,
    'lwave': False,
    'npar': 4,
    'prec': 'Accurate',
    'sigma': 0.01
        }
vasp_params['potcar'] = {
        'potential_family': 'PBE.54',
        'potential_mapping': {'As': 'As', 'Ga': 'Ga'}
    }
