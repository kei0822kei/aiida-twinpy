#!/usr/bin/env python

from aiida.common.extendeddicts import AttributeDict
from aiida.orm import (load_node, Code, Bool, Dict,
                       Float, Int, Str)
from aiida.plugins import WorkflowFactory

def _get_string(string):
    if type(string) == Str:
        return string.value
    else:
        return string

def get_options(queue, max_wallclock_seconds):
    options = AttributeDict()
    options.account = ''
    options.qos = ''
    options.resources = {
                         'tot_num_mpiprocs': 16,
                         'num_machines': 1,
                         'parallel_env': 'mpi*'}
    options.queue_name = queue
    options.max_wallclock_seconds = max_wallclock_seconds
    return Dict(dict=options)

def get_relax(relax_conf):
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
    if 'algo' in keys:
        relax_attribute.shape = \
                Bool(relax_conf['algo'])
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
    return relax_attribute

def get_relax_builder(computer,
                      label,
                      description,
                      structure,
                      incar_settings,
                      relax_conf,
                      kpoints,
                      potential_family,
                      potential_mapping,
                      queue='',
                      vaspcode='vasp544mpi',
                      max_wallclock_seconds=3600*10,
                      clean_workdir=Bool(True),
                      verbose=Bool(True)
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
        # >>> kpoints = \ => kpoints object
        #       {
        #          'mesh': [6, 6, 6],
        #          # 'kdensity': 0.2,
        #          'offset': [0.5, 0.5, 0.5]
        #       }
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
    builder.code = Code.get_from_string('{}@{}'.format(vaspcode, computer.value))
    builder.clean_workdir = clean_workdir
    builder.verbose = verbose
    builder.options = get_options(queue, max_wallclock_seconds)
    builder.structure = structure
    builder.parameters = incar_settings
    settings = dict(relax_conf)
    settings.update({
        'perform': True,
        'positions': True,
        'volume': False,
        'shape': False,
    })
    builder.relax =  get_relax(settings)
    builder.settings = Dict(
            dict={
                   'add_energies': True,
                   'add_forces': True,
                   'add_stress': True,
                 })
    builder.kpoints = kpoints
    builder.potential_family = potential_family
    builder.potential_mapping = potential_mapping
    return builder
