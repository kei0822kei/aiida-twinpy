#!/usr/bin/env python

from aiida.common.extendeddicts import AttributeDict
from aiida.orm import (load_node, Code, Bool, Dict,
                       Float, Int, KpointsData, Str)
from aiida.plugins import WorkflowFactory
from aiida_vasp.utils.aiida_utils import get_data_class, get_data_node

def _add_options(builder, queue, max_wallclock_seconds):
    options = AttributeDict()
    options.account = ''
    options.qos = ''
    options.resources = {'tot_num_mpiprocs': 16,
                         'parallel_env': 'mpi*'}
    options.queue_name = queue
    options.max_wallclock_seconds = max_wallclock_seconds
    builder.options = Dict(dict=options)

def _add_potcar(builder, potential_family, potential_mapping):
    builder.potential_family = Str(potential_family)
    builder.potential_mapping = Dict(dict=potential_mapping)

def _add_kpoints(builder, kpoints, verbose):
    kpt = KpointsData()
    if 'kdensity' in kpoints.keys():
        kpt.set_cell_from_structure(builder.structure)
        kpt.set_kpoints_mesh_from_density(
                kpoints['kdensity'], offset=kpoints['offset'])
        if verbose:
            kmesh = kpt.get_kpoints_mesh()
            print("kdensity is: %s" % str(kpoints['kdensity']))
            print("reciprocal lattice (included 2*pi) is:")
            print(kpt.reciprocal_cell)
            print("set kpoints mesh as:")
            print(kmesh[0])
            print("set offset as:")
            print(kmesh[1])
    else:
        kpt.set_kpoints_mesh(kpoints['mesh'], offset=kpoints['offset'])
    builder.kpoints = kpt

def _add_relax(builder, relax_conf, relax_settings):
    relax_attribute = AttributeDict()
    keys = relax_conf.keys()
    if 'perform' in keys:
        relax_attribute.perform = \
                Bool(relax_conf['perform'])
    if 'positions' in keys:
        relax_attribute.positions = \
                Bool(relax_conf['positions'])
    if 'volume' in keys:
        relax_attribute.volume = \
                Bool(relax_conf['volume'])
    if 'shape' in keys:
        relax_attribute.shape = \
                Bool(relax_conf['shape'])
    if 'steps' in keys:
        relax_attribute.steps = \
                Int(relax_conf['steps'])
    if 'convergence_absolute' in keys:
        relax_attribute.convergence_absolute = \
                Bool(relax_conf['convergence_absolute'])
    if 'convergence_max_iterations' in keys:
        relax_attribute.convergence_max_iterations = \
                Int(relax_conf['convergence_max_iterations'])
    if 'convergence_on' in keys:
        relax_attribute.convergence_on = \
                Bool(relax_conf['convergence_on'])
    if 'convergence_positions' in keys:
        relax_attribute.convergence_positions = \
                Float(relax_conf['convergence_positions'])
    if 'convergence_shape_angles' in keys:
        relax_attribute.convergence_shape_angles = \
                Float(relax_conf['convergence_shape_angles'])
    if 'convergence_shape_lengths' in keys:
        relax_attribute.convergence_shape_lengths = \
                Float(relax_conf['convergence_shape_lengths'])
    if 'convergence_volume' in keys:
        relax_attribute.convergence_volume = \
                Float(relax_conf['convergence_volume'])
    if 'force_cutoff' in keys:
        relax_attribute.force_cutoff = \
                Float(relax_conf['force_cutoff'])
    if 'energy_cutoff' in keys:
        relax_attribute.energy_cutoff = \
                Float(relax_conf['energy_cutoff'])
    builder.relax = relax_attribute
    builder.settings = Dict(dict=relax_settings)

def get_relax_builder(computer,
                      label,
                      description,
                      structure,
                      incar_settings,
                      relax_conf,
                      relax_settings,
                      kpoints,
                      potential_family,
                      potential_mapping,
                      queue='',
                      vaspcode='vasp544mpi',
                      max_wallclock_seconds=3600*10,
                      clean_workdir=True,
                      verbose=True
                     ):
    """
    Examples:
        input sample:
        all of the input values must be wrapped by aiida datatype
        except 'label', 'description', 'vaspcode' and 'computer'

        >>> computer = 'vega'
        >>> label = 'label of relax workflow'
        >>> description = 'description of relax workflow'
        >>> structure = 'aiida structure object'
        >>> incar_settings = \
              {
                 'addgrid': True,
                 'ediff': 1e-6,
                 'gga': 'PS',
                 'ialgo': 38,
                 'lcharg': False,
                 'lreal': False,
                 'lwave': False,
                 'npar': 4,
                 'prec': 'Accurate',
                 'encut': 520
                 'ismear': 1,
                 'sigma': 0.2
              }
        >>> relax_conf = \
              {
                 'perform': True,
                 'positions': True,
                 'volume': True,
                 'shape': True,
                 'steps': 20,
                 'convergence_absolute': False,
                 'convergence_max_iterations': 3,
                 'convergence_on': True,
                 'convergence_positions': 0.01,
                 'convergence_shape_angles': 0.1,
                 'convergence_shape_lengths': 0.1,
                 'convergence_volume': 0.01,
                 'force_cutoff': 0.0001,
              }
        >>> relax_settings = \
              {
                 'add_energies': True,
                 'add_forces': True,
                 'add_stress': True,
              }
        >>> kpoints = \
              {
                 'mesh': [6, 6, 6],
                 # 'kdensity': 0.2,
                 'offset': [0.5, 0.5, 0.5]
              }
        >>> potential_family = 'PBE.54'
        >>> potential_mapping = \
              {
                 'Na': 'Na',
                 'Cl': 'Cl'
              }
        >>> queue = ''  # default
        >>> vaspcode = 'vasp544mpi'  # default
        >>> max_wallclock_seconds = '3600*10'  # default
        >>> clean_workdir = True  # default
        >>> verbose = True  # defualt
    """
    workflow = WorkflowFactory('vasp.relax')
    builder = workflow.get_builder()
    builder.metadata.label = label
    builder.metadata.description = description
    builder.code = Code.get_from_string('{}@{}'.format(vaspcode, computer))
    builder.clean_workdir = clean_workdir
    builder.verbose = verbose
    _add_options(builder, queue, max_wallclock_seconds)
    builder.structure = structure
    builder.parameters = incar_settings
    _add_relax(builder, relax_conf, relax_settings)
    _add_kpoints(builder, kpoints, verbose)
    _add_potcar(builder, potential_family, potential_mapping)
    return builder

# def get_vasp_builder(structure, params):
#     workflow = WorkflowFactory('vasp.vasp')
#     builder = workflow.get_builder()
#     builder.code = Code.get_from_string(
#             '{}@{}'.format(params['code'], params['computer']))
#     builder.clean_workdir = get_data_node('bool', params['clean_workdir'])
#     builder.structure = structure
# 
#     kpt = get_data_class('array.kpoints')()
#     kpt.set_cell_from_structure(builder.structure)
#     kpt.set_kpoints_mesh(params['kpoints']['mesh'],
#                          offset=params['kpoints']['offset'])
#     builder.kpoints = kpt
# 
#     options = AttributeDict()
#     options.account = ''
#     options.qos = ''
#     options.resources = {'tot_num_mpiprocs': params['options']['tot_num_mpiprocs'],
#                          'parallel_env': 'mpi*'}
#     options.queue_name = params['queue']
#     options.max_wallclock_seconds = params['options']['max_wallclock_seconds']
#     builder.options = get_data_node('dict', dict=options)
# 
#     builder.parameters = get_data_node(
#             'dict', dict=params['incar'])
# 
#     builder.potential_family = \
#             get_data_node('str', params['potcar']['potential_family'])
#     builder.potential_mapping = \
#             get_data_node('dict', dict=params['potcar']['potential_mapping'])
#     return builder
# 
