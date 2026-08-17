import pandas as pd
import numpy as np 
from scipy.linalg import cholesky
from cma import RETURNS, COVARIANCE


class MonteCarloSim:

    num_paths : int
    paths : list[float]
    horizon : int

    def __init__(self, num_paths : int, horizon: int):
        '''
        :param num_paths (int): Number of random simulated paths to create
        :param horizon (int) : Time frame (years) for the simulated paths
        '''
        self.num_paths = num_paths
        self.horizon = horizon

    def __get_marginal_data(self):

        l = cholesky(COVARIANCE)
        

        z_vals = self.__gen_paths()

        # Add covariance shape (we use transpose becasue we're applying to the full z_vals)

        correlated_returns = l * z_vals


    def __gen_paths(self): 
    
        num_points = self.horizon * 365
        num_vars = len(RETURNS)

        z_vals = np.random.standard_normal((num_vars, num_points))

        return z_vals