#!/usr/bin/env python

from aiida.common.extendeddicts import AttributeDict
from aiida.orm import (load_node, Code, Bool, Dict,
                       Float, Int, Str)
from aiida.plugins import WorkflowFactory

def _get_options(queue, max_wallclock_seconds):
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

def _get_relax_attribute(relax_conf):
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

def get_vasp_builder(computer,
                     label,
                     description,
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
                      incar_settings,
                      kpoints,
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
    def _get_vasp_settings(dic):
        settings = {}
        base_config = {'code_string': dic['vasp_code']+'@'+computer.value,
                       'kpoints_mesh': dic['kpoints_mesh'],
                       'kpoints_offset': dic['kpoints_offset'],
                       'potential_family': dic['potential_family'],
                       'potential_mapping': dic['potential_mapping'],
                       'options': {'resources': {'parallel_env': 'mpi*',
                                                 'tot_num_mpiprocs': 16,
                                                 'num_machines': 1},
                                   'max_wallclock_seconds': max_wallclock_seconds.value}}
        base_parser_settings = {'add_energies': True,
                                'add_forces': True,
                                'add_stress': True}
        forces_config = base_config.copy()
        forces_config.update({'parser_settings': base_parser_settings,
                              'parameters': dic['incar_settings']})
        settings['forces'] = forces_config
        if dict(phonon_settings['is_nac']):
            nac_config = base_config.copy()
            nac_parser_settings = {'add_born_charges': True,
                                   'add_dielectrics': True}
            nac_parser_settings.update(base_parser_settings)
            nac_incar_dict = {'lepsilon': True}
            nac_incar_dict.update(dic['incar_settings'])
            del nac_incar_dict['npar']
            # density = np.average(kpoints_fc2['densities'])
            # print("for nac calc, always primitive structure is used")
            # print("kpoints density for calc fc2 was: %f" % density)
            # print("for calc nac, multiply kpoints density is used")
            # print("from {} to {}".format(density, density*2))
            # kpoints_nac = get_kpoints(
            #         structure=pmgstructure.get_primitive_structure(),
            #         kdensity=density*2,
            #         offset=kpoints['offset'])
            nac_config.update({'kpoints_mesh': kpoints_nac['mesh'],
                               'parser_settings': nac_parser_settings,
                               'parameters': nac_incar_dict})
            settings['nac'] = nac_config
        return settings

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
    builder.phonon_settings = phonon_settings
