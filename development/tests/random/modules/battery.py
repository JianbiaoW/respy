
""" This modules contains some additional tests that are only used in
long-run development tests.
"""

# standard library
from pandas.util.testing import assert_frame_equal
import pandas as pd
import numpy as np
import sys
import os

# project library
from modules.auxiliary import compile_package

# ROBUPY import
sys.path.insert(0, os.environ['ROBUPY'])
from robupy.tests.random_init import generate_random_dict, print_random_dict
from robupy import read, solve, simulate

''' Main
'''
def test_97():
    """ Compare results between FORTRAN and PYTHON implementations.
    """
    compile_package('fast')

    import robupy.performance.fortran.fortran_core as fort
    import robupy.performance.python.python_core as py

    for _ in range(1000):

        # Draw random matrix for testing purposes
        matrix = (np.random.multivariate_normal(np.zeros(4), np.identity(4), 4))
        cov = np.dot(matrix, matrix.T)

        # Inverse
        py = np.linalg.inv(cov)
        f90 = fort.debug_inverse(cov, 4)
        np.testing.assert_allclose(py, f90, rtol=1e-06)

        # Determinant
        py = np.linalg.det(cov)
        f90 = fort.debug_determinant(cov)

        np.testing.assert_allclose(py, f90, rtol=1e-06)

        # Trace
        py = np.trace(cov)
        f90 = fort.debug_trace(cov)

        np.testing.assert_allclose(py, f90, rtol=1e-06)


def test_98():
    """  Compare results from the RESTUD program and the ROBUPY package.
    """

    # Prepare RESTUD program
    os.chdir('modules')
    os.system(' gfortran -o dp3asim dp3asim.f95 > /dev/null 2>&1 ')
    os.remove('pei_additions.mod')
    os.remove('imsl_replacements.mod')
    os.chdir('../')

    # Impose some constraints on the initialization file which ensures that
    # the problem can be solved by the RESTUD code.
    constraints = dict()
    constraints['edu'] = (10, 20)
    constraints['level'] = 0.00

    # Generate random initialization file. The RESTUD code uses the same random
    # draws for the solution and simulation of the model. Thus, the number of
    # draws is required to be less or equal to the number of agents.
    init_dict = generate_random_dict(constraints)

    num_agents = init_dict['SIMULATION']['agents']
    num_draws = init_dict['SOLUTION']['draws']
    if num_draws < num_agents:
        init_dict['SOLUTION']['draws'] = num_agents

    print_random_dict(init_dict)

    # Perform toolbox actions
    robupy_obj = read('test.robupy.ini')

    init_dict = robupy_obj.get_attr('init_dict')

    # This flag aligns the random components between the RESTUD program and
    # ROBUPY package. The existence of the file leads to the RESTUD program
    # to write out the random components.
    robupy_obj.is_restud = True
    open('.write_out', 'a').close()

    with open('in.txt', 'w') as file_:

        # Write out some basic information about the problem.
        num_agents = init_dict['SIMULATION']['agents']
        num_periods = init_dict['BASICS']['periods']
        num_draws = init_dict['SOLUTION']['draws']
        file_.write(' {0:03d} {1:05d} {2:06d} {3:06f}'
            ' {4:06f}\n'.format(num_periods, num_agents, num_draws,-99.0,
            500.0))

        # Write out coefficients for the two occupations.
        for label in ['A', 'B']:
            coeffs = [init_dict[label]['int']] + init_dict[label]['coeff']
            line = ' {0:10.6f} {1:10.6f} {2:10.6f} {3:10.6f}  {4:10.6f}' \
                    ' {5:10.6f}\n'.format(*coeffs)
            file_.write(line)

        # Write out coefficients for education and home payoffs as well as
        # the discount factor. The intercept is scaled. This is later undone
        # again in the original FORTRAN code.
        edu_int = init_dict['EDUCATION']['int'] / 1000; edu_coeffs = [edu_int]
        home = init_dict['HOME']['int'] / 1000
        for j in range(2):
            edu_coeffs += [-init_dict['EDUCATION']['coeff'][j] / 1000]
        delta = init_dict['BASICS']['delta']
        coeffs = edu_coeffs + [home, delta]
        line = ' {0:10.6f} {1:10.6f} {2:10.6f} {3:10.6f}' \
                ' {4:10.6f}\n'.format(*coeffs)
        file_.write(line)

        # Write out coefficients of correlation, which need to be constructed
        # based on the covariance matrix.
        shocks = init_dict['SHOCKS']; rho = np.identity(4)
        rho_10 = shocks[1][0] / (np.sqrt(shocks[1][1]) * np.sqrt(shocks[0][0]))
        rho_20 = shocks[2][0] / (np.sqrt(shocks[2][2]) * np.sqrt(shocks[0][0]))
        rho_30 = shocks[3][0] / (np.sqrt(shocks[3][3]) * np.sqrt(shocks[0][0]))
        rho_21 = shocks[2][1] / (np.sqrt(shocks[2][2]) * np.sqrt(shocks[1][1]))
        rho_31 = shocks[3][1] / (np.sqrt(shocks[3][3]) * np.sqrt(shocks[1][1]))
        rho_32 = shocks[3][2] / (np.sqrt(shocks[3][3]) * np.sqrt(shocks[2][2]))
        rho[1, 0] = rho_10; rho[2, 0] = rho_20; rho[3, 0] = rho_30
        rho[2, 1] = rho_21; rho[3, 1] = rho_31; rho[3, 2] = rho_32
        for j in range(4):
            line = ' {0:10.5f} {1:10.5f} {2:10.5f} ' \
                   ' {3:10.5f}\n'.format(*rho[j, :])
            file_.write(line)

        # Write out standard deviations. Scaling for standard deviations in the
        # education and home equation required. This is undone again in the
        # original FORTRAN code.
        sigmas = np.sqrt(np.diag(shocks)); sigmas[2:] = sigmas[2:]/1000
        line = '{0:10.5f} {1:10.5f} {2:10.5f} {3:10.5f}\n'.format(*sigmas)
        file_.write(line)

    # Solve model using RESTUD code.
    os.system('./modules/dp3asim > /dev/null 2>&1')

    # Solve model using ROBUPY package.
    solve(robupy_obj); simulate(robupy_obj)

    # Compare the simulated datasets generated by the programs.
    py = pd.DataFrame(np.array(np.genfromtxt('data.robupy.dat',
            missing_values='.'), ndmin=2)[:, -4:])

    fort = pd.DataFrame(np.array(np.genfromtxt('ftest.txt',
            missing_values='.'), ndmin=2)[:, -4:])

    assert_frame_equal(py, fort)

def test_99():
    """ Testing whether the results from a fast and slow execution of the
    code result in identical simulate datasets.
    """
    # Set up constraints
    compile_package('fast')

    # Constraint to risk model
    constraints = dict()
    constraints['level'] = 0.0

    # Generate random initialization
    init_dict = generate_random_dict(constraints)

    # Initialize containers
    base = None

    for fast in ['True', 'False']:

        # Prepare initialization file
        init_dict['SOLUTION']['fast'] = fast

        print_random_dict(init_dict)

        # Simulate the ROBUPY package
        os.system('robupy-solve --simulate --model test.robupy.ini')

        # Load simulated data frame
        data_frame = pd.read_csv('data.robupy.dat')

        # Compare
        if base is None:
            base = data_frame.copy()

        assert_frame_equal(base, data_frame)