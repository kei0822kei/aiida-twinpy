#!/usr/bin/env python

from aiida.common.extendeddicts import AttributeDict
from aiida.orm import Code
from aiida.plugins import WorkflowFactory
from aiida_vasp.utils.aiida_utils import get_data_class, get_data_node

def get_vasp_builder(structure, params):
    workflow = WorkflowFactory('vasp.vasp')
    builder = workflow.get_builder()
    builder.code = Code.get_from_string(
            '{}@{}'.format(params['code'], params['computer']))
    builder.clean_workdir = get_data_node('bool', params['clean_workdir'])
    builder.structure = structure

    kpt = get_data_class('array.kpoints')()
    kpt.set_cell_from_structure(builder.structure)
    kpt.set_kpoints_mesh(params['kpoints']['mesh'],
                         offset=params['kpoints']['offset'])
    builder.kpoints = kpt

    options = AttributeDict()
    options.account = ''
    options.qos = ''
    options.resources = {'tot_num_mpiprocs': params['options']['tot_num_mpiprocs'],
                         'parallel_env': 'mpi*'}
    options.queue_name = params['queue']
    options.max_wallclock_seconds = params['options']['max_wallclock_seconds']
    builder.options = get_data_node('dict', dict=options)

    builder.parameters = get_data_node(
            'dict', dict=params['incar'])

    builder.potential_family = \
            get_data_node('str', params['potcar']['potential_family'])
    builder.potential_mapping = \
            get_data_node('dict', dict=params['potcar']['potential_mapping'])
    return builder
