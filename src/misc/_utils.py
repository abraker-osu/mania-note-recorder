import math
import numpy as np


class Utils():

    @staticmethod
    def normal_distr(x: np.ndarray, avg: np.ndarray, std: np.ndarray):
        return 1/(std*((2*math.pi)**0.5))*math.exp(-0.5*((x - avg)/std)**2)


    @staticmethod
    def get_freq_hist(data: np.ndarray):
        freq = np.zeros(data.shape[0])
        unique = np.unique(data)

        for val in unique:
            val_filter = (data == val)
            freq[val_filter] = np.arange(freq[val_filter].shape[0])

        return freq


    @staticmethod
    def calc_err(x_data: np.ndarray, y_data: np.ndarray, r: np.ndarray, t_min: np.ndarray, y: int | np.ndarray = 0):
        curve_fit = Utils.softplus_func(x_data, r, t_min, y)
        return np.sum(np.abs(y_data - curve_fit))


    @staticmethod
    def softplus_func(t: np.ndarray, r: np.ndarray, t_min: np.ndarray, y: int | np.ndarray = 0):
        lin = r*(t - t_min)
        lin[lin < 100] = np.log(np.exp(lin[lin < 100]) + np.exp(y))
        return lin
