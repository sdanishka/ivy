# global
import os
import pytest
from typing import Dict

# local
from ivy_tests.test_ivy import helpers
from ivy import clear_framework_stack, DefaultDevice


FW_STRS = ['numpy', 'jax', 'tensorflow', 'torch', 'mxnet']


TEST_FRAMEWORKS: Dict[str, callable] = {'numpy': lambda: helpers.get_ivy_numpy(),
                                        'jax': lambda: helpers.get_ivy_jax(),
                                        'tensorflow': lambda: helpers.get_ivy_tensorflow(),
                                        'torch': lambda: helpers.get_ivy_torch(),
                                        'mxnet': lambda: helpers.get_ivy_mxnet()}
TEST_CALL_METHODS: Dict[str, callable] = {'numpy': helpers.np_call,
                                          'jax': helpers.jnp_call,
                                          'tensorflow': helpers.tf_call,
                                          'torch': helpers.torch_call,
                                          'mxnet': helpers.mx_call}

if 'ARRAY_API_TESTS_MODULE' not in os.environ:
    os.environ['ARRAY_API_TESTS_MODULE'] = 'ivy.functional.backends.numpy'

@pytest.fixture(autouse=True)
def run_around_tests(dev, f, array_mode, compile_graph, implicit, call):
    if array_mode and call is helpers.tf_graph_call:
        # ToDo: add support for array_mode and tensorflow compilation
        pytest.skip()
    if array_mode and call is helpers.jnp_call:
        # ToDo: add support for array_mode with jax, presumably some errenously wrapped jax methods
        pytest.skip()
    if 'gpu' in dev and call is helpers.np_call:
        # Numpy does not support GPU
        pytest.skip()
    clear_framework_stack()
    with f.use:
        f.set_array_mode(array_mode)
        with DefaultDevice(dev):
            yield


def pytest_generate_tests(metafunc):

    # dev
    raw_value = metafunc.config.getoption('--dev')
    if raw_value == 'all':
        devs = ['cpu', 'gpu:0', 'tpu:0']
    else:
        devs = raw_value.split(',')

    # framework
    raw_value = metafunc.config.getoption('--framework')
    if raw_value == 'all':
        f_strs = TEST_FRAMEWORKS.keys()
    else:
        f_strs = raw_value.split(',')

    # array_mode
    raw_value = metafunc.config.getoption('--array_mode')
    if raw_value == 'both':
        array_modes = [True, False]
    elif raw_value == 'true':
        array_modes = [True]
    else:
        array_modes = [False]

    # compile_graph
    raw_value = metafunc.config.getoption('--compile_graph')
    if raw_value == 'both':
        compile_modes = [True, False]
    elif raw_value == 'true':
        compile_modes = [True]
    else:
        compile_modes = [False]

    # implicit
    raw_value = metafunc.config.getoption('--with_implicit')
    if raw_value == 'true':
        implicit_modes = [True, False]
    else:
        implicit_modes = [False]

    # create test configs
    configs = list()
    for f_str in f_strs:
        for dev in devs:
            for array_mode in array_modes:
                for compile_graph in compile_modes:
                    for implicit in implicit_modes:
                        configs.append(
                            (dev, TEST_FRAMEWORKS[f_str](), array_mode, compile_graph, implicit,
                             TEST_CALL_METHODS[f_str]))
    metafunc.parametrize('dev,f,array_mode,compile_graph,implicit,call', configs)


def pytest_addoption(parser):
    parser.addoption('--dev', action="store", default="cpu")
    parser.addoption('--framework', action="store", default="jax,mxnet,numpy,tensorflow,torch")
    parser.addoption('--array_mode', action="store", default="true")
    parser.addoption('--compile_graph', action="store", default="true")
    parser.addoption('--with_implicit', action="store", default="false")
