#!/usr/bin/env python

from aiida.common.extendeddicts import AttributeDict
from aiida.orm import (load_node, Code, Bool, Dict,
                       Float, Int, Str, KpointsData)
from aiida.plugins import WorkflowFactory
from aiida import load_profile

load_profile()

def get_calcjob_builder(label,
                        description,
                        calc_type,
                        computer,
                        structure,
                        calculator_settings,
                        ):
    """
    get calcjob builder

    Args:
        label (str): label
        description (str): description
        calc_type (str): 'relax' or 'phonon'
        computer: (Str) computer
        structure: (StructureData) structure
        calculator_settings: (Dict) calculator_settings

    Examples:
        all of the input values must be wrapped by aiida datatype
        except 'label', 'description' and calc_type

        >>> label = 'label of calcjob builder'
        >>> description = 'description of calcjob builder'
        >>> calc_type = 'relax'
        >>> computer = Str('stern')
        >>> structure = StructureData
        >>> vasp_settings = { \\
        >>>     'relax': { \\
        >>>         'vasp_code': vasp_code,
        >>>         'incar_settings': incar_settings,
        >>>         'potential_family': potential_family,
        >>>         'potential_mapping': potential_mapping,
        >>>         'kpoints': kpoints,
        >>>         'options': {'queue_name': queue_name,
        >>>                     'max_wallclock_seconds': max_wallclock_seconds},
        >>>         'relax_conf': relax_conf,
        >>>         'clean_workdir': clean_workdir,
        >>>     },
        >>>     'phonon': { \\
        >>>         'vasp_code': vasp_code,
        >>>         'incar_settings': incar_settings,
        >>>         'potential_family': potential_family,
        >>>         'potential_mapping': potential_mapping,
        >>>         'kpoints': kpoints,
        >>>         'options': {'queue_name': queue_name,
        >>>                     'max_wallclock_seconds': max_wallclock_seconds}
        >>>         'phonon_conf': 
        >>>     },
        >>> }
        >>> # where
        >>> vasp_code = 'vasp544mpi'
        >>> incar_settings = \\
        >>>       Dict(dict={
        >>>          'addgrid': True,
        >>>          'ediff': 1e-6,
        >>>          'gga': 'PS',
        >>>          'ialgo': 38,
        >>>          'lcharg': False,
        >>>          'lreal': False,
        >>>          'lwave': False,
        >>>          'npar': 4,
        >>>          'prec': 'Accurate',
        >>>          'encut': 300,
        >>>          'ismear': 1,
        >>>          'sigma': 0.4,
        >>>          'nsw': 40
        >>>       })
        >>> potential_family = 'PBE.54'
        >>> potential_mapping = {'Ti': 'Ti_pv'}
        >>> kpoints = {'mesh': [18, 18, 10],
        >>>            'offset': [0, 0, 0.5]}
        >>> queue_name = '' # default
        >>> max_wallclock_seconds = 3600*10  # default
        >>> clean_workdir = True  # default
        >>> phonon_conf = {
    """
    dic = dict(calculator_settings)
    if calc_type == 'relax':
        workflow = WorkflowFactory('vasp.relax')
    elif calc_type == 'phonon':
        workflow = WorkflowFactory('phonopy.phonopy')
    else:
        raise ValueError("calc_type: %s is not supported" % calc_type)
    builder = workflow.get_builder()
    builder.metadata.label = label
    builder.metadata.description = description
    builder.options = _get_options(**dic[calc_type]['options'])
    builder.structure = structure

    if calc_type == 'relax':
        builder.code = Code.get_from_string('{}@{}' \
            .format(dic[calc_type]['vasp_code'], computer.value))
        builder.clean_workdir = Bool(dic[calc_type]['clean_workdir'])
        builder.verbose = Bool(True)
        builder.parameters = Dict(dict=dic[calc_type]['incar_settings'])
        builder.relax =  _get_relax_attribute(dic[calc_type]['relax_conf'])
        builder.settings = Dict(dict={'add_energies': True,
                                      'add_forces': True,
                                      'add_stress': True})
        builder.kpoints = _get_kpoints(dic[calc_type]['kpoints'])
        builder.potential_family = Str(dic[calc_type]['potential_family'])
        builder.potential_mapping = Dict(dict=dic[calc_type]['potential_mapping'])

    elif calc_type == 'phonon':
        builder.code_string = Str('{}@{}'.format('phonopy', computer.value))
        builder.run_phonopy = Bool(True)
        builder.remote_phonopy = Bool(True)
        ph = _get_phonon_vasp_settings(computer.value, dic[calc_type])
        builder.phonon_settings = Dict(dict=ph['ph_settings'])
        builder.calculator_settings = Dict(dict=ph['forces_config'])

def _get_phonon_vasp_settings(computer, settings):
    forces_config = {'code_string': settings['vasp_code']+'@'+computer,
                     'kpoints_mesh': settings['kpoints']['mesh'],
                     'kpoints_offset': settings['kpoints']['offset'],
                     'potential_family': settings['potential_family'],
                     'potential_mapping': settings['potential_mapping'],
                     'options': _get_options(**settings['options'])
                     'parser_settings': {'add_energies': True,
                                         'add_forces': True,
                                         'add_stress': True},
                     'parameters': settings['incar_settings']}
    ph_settings = settings['phonon_conf']
    ph_settings['is_nac'] = False
    return {'forces_config': forces_config,
            'ph_settings': ph_settings}

def _get_kpoints(kpoints):
    kpt = KpointsData()
    kpt.set_kpoints_mesh(kpoints['mesh'], offset=kpoints['offset'])
    return kpt

def _get_options(queue_name='',
                 max_wallclock_seconds=10 * 3600):
    options = AttributeDict()
    options.account = ''
    options.qos = ''
    options.resources = {
                         'tot_num_mpiprocs': 16,
                         'num_machines': 1,
                         'parallel_env': 'mpi*'}
    options.queue_name = queue_name
    options.max_wallclock_seconds = max_wallclock_seconds
    return Dict(dict=options)

def _get_relax_attribute(relax_conf):
    updates = {'perform': True,
               'positions': True,
               'volume': False,
               'shape': False}
    for key in updates.keys():
        if key in relax_conf.keys():
            raise Warning("key {} in 'relax_conf' is overwritten to {}"\
                    .format(key, updates[key]))
    relax_conf.update(updates)
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
        relax_attribute.algo = \
                Str(relax_conf['algo'])
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
















def _get_vasp_builder(label,
                     description,
                     computer,
                     structure,
                     incar_settings,
                     kpoints,
                     potential_family,
                     potential_mapping,
                     queue=Str(''),
                     vaspcode=Str('vasp544mpi'),
                     max_wallclock_seconds=Int(3600*10),
                     clean_workdir=Bool(True),
                     verbose=Bool(True)
                     ):
    """
    get relax builder

    Examples:
        all of the input values must be wrapped by aiida datatype
        except 'label', 'description'

        >>> computer = Str('vega')
        >>> label = 'label of relax workflow'
        >>> description = 'description of relax workflow'
        >>> structure = StructureData
        >>> vasp_settings = {
        >>>         'vaspcode': 'vasp544mpi',
        >>>         'incar_settings': incar_settings,
        >>>         'potential_family': potential_family,
        >>>         'potential_mapping': potential_mapping,
        >>>         'kpoints_relax': kpoints_relax,
        >>>         'kpoints_phonon': kpoints_phonon,
        >>>         }
        >>> incar_settings = \\
        >>>       Dict(dict={
        >>>          'addgrid': True,
        >>>          'ediff': 1e-6,
        >>>          'gga': 'PS',
        >>>          'ialgo': 38,
        >>>          'lcharg': False,
        >>>          'lreal': False,
        >>>          'lwave': False,
        >>>          'npar': 4,
        >>>          'prec': 'Accurate',
        >>>          'encut': 520,
        >>>          'ismear': 1,
        >>>          'sigma': 0.2,
        >>>          'nsw': 40
        >>>       })
        >>> kpoints = KpointsData
        >>> potential_family = Str('PBE.54')
        >>> potential_mapping = \
        >>>       Dict(dict={
        >>>            'Na': 'Na',
        >>>            'Cl': 'Cl'
        >>>       })
        >>> queue = Str('')
        >>> vaspcode = Str('vasp544mpi')
        >>> max_wallclock_seconds = 3600*10  # default
        >>> clean_workdir = Bool(True)  # default
        >>> verbose = Bool(True)  # defualt
    """
    workflow = WorkflowFactory('vasp.vasp')
    builder = workflow.get_builder()
    builder.metadata.label = label
    builder.metadata.description = description
    builder.code = Code.get_from_string('{}@{}'.format(vaspcode.value,
                                                       computer.value))
    builder.clean_workdir = clean_workdir
    builder.verbose = verbose
    builder.options = _get_options(queue.value,
                                   max_wallclock_seconds.value)
    builder.structure = structure
    builder.parameters = incar_settings
    builder.kpoints = kpoints
    builder.potential_family = potential_family
    builder.potential_mapping = potential_mapping
    return builder

def get_relax_builder(label,
                      description,
                      calc_type,
                      computer,
                      potential_family,
                      potential_mapping,
                      relax_conf,
                      structure,
                      clean_workdir=Bool(True),
                      max_wallclock_seconds=Int(3600*10),
                      queue=Str(''),
                      vaspcode=Str('vasp544mpi'),
                      verbose=Bool(True)
                     ):
    """
    get relax builder

    Note:
        If calc_type == 'shear', relax_settings {'perform': True,
        'positions': True, 'volume': False, 'shape': False} are
        automatically set.

    Examples:
        all of the input values must be wrapped by aiida datatype
        except 'label', 'description', 'calc_type'

        >>> label = 'label of relax workflow'
        >>> description = 'description of relax workflow'
        >>> calc_type = 'shear'
        >>> computer = Str('vega')
        >>> incar_settings = \\
        >>>       Dict(dict={
        >>>          'addgrid': True,
        >>>          'ediff': 1e-6,
        >>>          'gga': 'PS',
        >>>          'ialgo': 38,
        >>>          'lcharg': False,
        >>>          'lreal': False,
        >>>          'lwave': False,
        >>>          'npar': 4,
        >>>          'prec': 'Accurate',
        >>>          'encut': 520
        >>>          'ismear': 1,
        >>>          'sigma': 0.2
        >>>       })
        >>> kpoints = KpointsData
        >>> structure = StructureData
        >>> potential_family = Str('PBE.54')
        >>> potential_mapping = \
        >>>      Dict(dict={
        >>>         'Na': 'Na',
        >>>         'Cl': 'Cl'
        >>>      })
        >>> relax_conf = \\
        >>>       Dict(dict={
        >>>          'perform': True,
        >>>          'algo': 'rd', (or cg)
        >>>          'positions': True,
        >>>          'volume': True,
        >>>          'shape': True,
        >>>          'steps': 20,
        >>>          'convergence_absolute': False,
        >>>          'convergence_max_iterations': 3,
        >>>          'convergence_on': True,
        >>>          'convergence_positions': 0.01,
        >>>          'convergence_shape_angles': 0.1,
        >>>          'convergence_shape_lengths': 0.1,
        >>>          'convergence_volume': 0.01,
        >>>          'force_cutoff': 0.0001,
        >>>       })
        >>> clean_workdir = Bool(True)  # default
        >>> max_wallclock_seconds = Int(3600*10)  # default
        >>> queue = Str('')  # default (str object)
        >>> vaspcode = Str('vasp544mpi')  # default (str object)
        >>> verbose = Bool(True)  # defualt
    """
    workflow = WorkflowFactory('vasp.relax')
    builder = workflow.get_builder()
    builder.metadata.label = label
    builder.metadata.description = description
    builder.code = Code.get_from_string('{}@{}'.format(vaspcode.value,
                                                       computer.value))
    builder.clean_workdir = clean_workdir
    builder.verbose = verbose
    builder.options = _get_options(queue.value,
                                  max_wallclock_seconds.value)
    builder.structure = structure
    builder.parameters = incar_settings
    settings = dict(relax_conf)
    if calc_type == 'shear':
        settings.update({
            'perform': True,
            'positions': True,
            'volume': False,
            'shape': False,
        })
    elif calc_type == 'relax':
        pass
    builder.relax =  _get_relax_attribute(settings)
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

def get_phonon_builder(label,
                       description,
                       computer,
                       structure,
                       phonon_settings,
                       vasp_settings,
                       max_wallclock_seconds=Int(3600*10),
                       queue=Str(''),
                       ):
    """
    get phonon builder

    Examples:
        all of the input values must be wrapped by aiida datatype
        except 'label', 'description'

        >>> label = 'label of phonon workflow'
        >>> description = 'description of phonon workflow'
        >>> computer = Str('vega')
        >>> structure = StructureData
        >>> phonon_settings = \\
        >>>      Dict(dict={
        >>>          'distance': 0.03,
        >>>          'mesh': [13, 13, 13],
        >>>          'supercell_matrix': [2, 2, 2],
        >>>          'symmetry_tolerance': 1e-5
        >>>      })
        >>> vasp_settings = \\
        >>>        Dict(dict={
        >>>            'vasp_code': 'vasp544mpi',
        >>>            'kpoints_mesh': [3, 3, 3],
        >>>            'kpoints_offset': [0.5, 0.5, 0.5],
        >>>            'potential_family': 'PBE5.4',
        >>>            'potential_mapping': {
        >>>                    'Na': 'Na',
        >>>                    'Cl': 'Cl'
        >>>                    },
        >>>            'incar_settings': {
        >>>                'addgrid': True,
        >>>                'ediff': 1e-6,
        >>>                'gga': 'PS',
        >>>                'ialgo': 38,
        >>>                'lcharg': False,
        >>>                'lreal': False,
        >>>                'lwave': False,
        >>>                'npar': 4,
        >>>                'prec': 'Accurate',
        >>>                'encut': 520
        >>>                'ismear': 1,
        >>>                'sigma': 0.2,
        >>>            }
        >>>       })
        >>> queue = Str('')
        >>> vaspcode = Str('vasp544mpi')
        >>> max_wallclock_seconds = 3600*10  # default
    """
    # common settings
    workflow = WorkflowFactory('phonopy.phonopy')
    builder = workflow.get_builder()
    builder.code_string = Str('{}@{}'.format('phonopy', computer))

    # label and descriptions
    builder.metadata.label = label
    builder.metadata.description = description

    # options
    builder.options = _get_options(queue, max_wallclock_seconds)

    # structure
    builder.structure = structure

    # vasp
    builder.calculator_settings = \
            Dict(dict=_get_vasp_settings(dict(vasp_settings)))

    # phonopy
    builder.run_phonopy = Bool(True)
    builder.remote_phonopy = Bool(True)
    ph_settings = dict(phonon_settings)
    ph_settings['is_nac'] = False
    builder.phonon_settings = Dict(dict=ph_settings)

    return builder
