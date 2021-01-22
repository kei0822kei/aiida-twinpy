#!/usr/bin/env python

import warnings
from aiida.common.extendeddicts import AttributeDict
from aiida.orm import (load_node, Code, Bool, Dict,
                       Float, Int, Str, KpointsData)
from aiida.plugins import WorkflowFactory
from aiida import load_profile
from aiida_twinpy.common.interfaces import get_vasp_settings_for_from_phonopy
from twinpy.interfaces.aiida.vasp import AiidaRelaxWorkChain
from twinpy.interfaces.aiida.twinboundary \
        import AiidaTwinBoudnaryRelaxWorkChain

load_profile()


def get_calcjob_builder_for_modulation(label,
                                       description,
                                       computer,
                                       structure,
                                       modulation_conf,
                                       ):
    conf = modulation_conf.get_dict()
    incar_update = conf['incar_update_settings']
    incar_update.update({'isif': 2})

    vasp_settings = get_vasp_settings_for_from_phonopy(
            phonon_pk=conf['phonon_pk'],
            incar_update_settings=incar_update,
            clean_workdir=conf['clean_workdir'],
            parser_settings=conf['parser_settings'],
            queue=modulation_conf['queue'],
            kpoints=modulation_conf['kpoints']
            )
    builder = get_calcjob_builder(label=label,
                                  description=description,
                                  calc_type='vasp',
                                  computer=computer,
                                  structure=structure,
                                  calculator_settings={'vasp': vasp_settings},
                                  )
    return builder


def get_calcjob_builder_for_twinboundary_shear(label,
                                               description,
                                               computer,
                                               structure,
                                               kpoints,
                                               twinboundary_shear_conf):
    conf = dict(twinboundary_shear_conf)
    aiida_twinboundary = AiidaTwinBoudnaryRelaxWorkChain(
            load_node(conf['twinboundary_relax_pk']))
    aiida_relax = \
            AiidaRelaxWorkChain(load_node(conf['additional_relax_pks'][-1]))

    if conf['additional_relax_pks'] is None:
        rlx_pk = aiida_twinboundary.get_pks()['relax_pk']
    else:
        rlx_pk = conf['additional_relax_pks'][-1]
    rlx_node = load_node(rlx_pk)
    builder = rlx_node.get_builder_restart()
    builder.options = _get_options(**twinboundary_shear_conf['options'])
    builder.kpoints = kpoints
    builder.structure = structure
    builder.metadata.label = label
    builder.metadata.description = description
<<<<<<< HEAD
    builder.code = Code.get_from_string(
                       '{}@{}'.format('vasp544mpi', computer.value))
=======
>>>>>>> 41e75928fe54ad5cda979f953e61d1d53409263a

    # fix relax conf
    builder.relax.convergence_max_iterations = Int(40)
    builder.relax.positions = Bool(True)
    builder.relax.shape = Bool(False)
    builder.relax.volume = Bool(False)
    builder.relax.convergence_positions = Float(1e-6)
    builder.relax.force_cutoff = \
            Float(aiida_relax.get_max_force())

    # fix queue

    return builder


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
        >>> calculator_settings = { \\
        >>>     'relax': { \\
        >>>         'vasp_code': vasp_code,
        >>>         'incar_settings': incar_settings,
        >>>         'potential_family': potential_family,
        >>>         'potential_mapping': potential_mapping,
        >>>         'kpoints': kpoints,
        >>>         'options': {'queue_name': queue_name,
        >>>                     'max_wallclock_seconds':
        >>>                         max_wallclock_seconds},
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
        >>>                     'max_wallclock_seconds':
        >>>                         max_wallclock_seconds},
        >>>         'phonon_conf': phonon_conf
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
        >>> relax_conf = {
        >>>     # set automatically => 'perform': True,
        >>>     # set automatically => 'positions': True,
        >>>     # set automatically => 'volume': False,
        >>>     # set automatically => 'shape': False,
        >>>     'algo': 'rd',  # you can also choose 'cg' (default)
        >>>     'steps': 20,
        >>>     'convergence_absolute': False,
        >>>     'convergence_max_iterations': 2,
        >>>     'convergence_on': True,
        >>>     'convergence_positions': 0.01,
        >>>     'convergence_shape_angles': 0.1,
        >>>     'convergence_shape_lengths': 0.1,
        >>>     'convergence_volume': 0.01,
        >>>     'force_cutoff': 0.001,  # or 'energy_cutoff': 1e-4,
        >>>     }
        >>> phonon_conf =  {'distance': 0.03,
        >>>                 'phonopy_mesh': [13,13,13],
        >>>                 'supercell_matrix': [2,2,2],
        >>>                 'symmetry_tolerance': 1e-5,
        >>>                 # set automatically => 'is_nac': False
        >>>                }
    """
    # not use get_dict() in the case calculator_settings is 'dict' object
    dic = dict(calculator_settings)
    if calc_type == 'vasp':
        workflow = WorkflowFactory('vasp.vasp')
    elif calc_type == 'relax':
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

    if calc_type == 'relax' or calc_type == 'vasp':
        builder.code = Code.get_from_string('{}@{}'.format(
            dic[calc_type]['vasp_code'], computer.value))
        builder.clean_workdir = Bool(dic[calc_type]['clean_workdir'])
        builder.verbose = Bool(True)
        builder.parameters = Dict(dict=dic[calc_type]['incar_settings'])
        builder.settings = \
            Dict(dict={'parser_settings': dic[calc_type]['parser_settings']})
        builder.kpoints = _get_kpoints(dic[calc_type]['kpoints'])
        builder.potential_family = Str(dic[calc_type]['potential_family'])
        builder.potential_mapping = \
            Dict(dict=dic[calc_type]['potential_mapping'])
        if calc_type == 'relax':
            builder.relax = _get_relax_attribute(dic[calc_type]['relax_conf'])

    elif calc_type == 'phonon':
        builder.code_string = Str('{}@{}'.format('phonopy', computer.value))
        builder.run_phonopy = Bool(True)
        builder.remote_phonopy = Bool(False)
        ph = _get_phonon_vasp_settings(computer.value, dic[calc_type])
        builder.phonon_settings = Dict(dict=ph['ph_settings'])
        builder.calculator_settings = \
                Dict(dict={'forces': ph['forces_config']})

    return builder


def _get_phonon_vasp_settings(computer, settings):
    forces_config = {'code_string': settings['vasp_code']+'@'+computer,
                     'kpoints_mesh': settings['kpoints']['mesh'],
                     'kpoints_offset': settings['kpoints']['offset'],
                     'potential_family': settings['potential_family'],
                     'potential_mapping': settings['potential_mapping'],
                     'options': dict(_get_options(**settings['options'])),
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
                 max_wallclock_seconds=100 * 3600):
    options = AttributeDict()
    options.account = ''
    options.qos = ''
    options.resources = {'tot_num_mpiprocs': 16,
                         'parallel_env': 'mpi*'}
    options.queue_name = queue_name
    options.max_wallclock_seconds = max_wallclock_seconds
    return Dict(dict=options)


def _get_relax_attribute(relax_conf):
    # updates = {'perform': True,
    #            'positions': True,
    #            'volume': False,
    #            'shape': False}
    updates = {'perform': True}
    for key in updates.keys():
        if key in relax_conf.keys():
            if relax_conf[key] is not updates[key]:
                warnings.warn("key {} in 'relax_conf' is overwritten to {}"
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
