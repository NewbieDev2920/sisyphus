from scipy.stats import zscore
from scipy.stats import norm

def z_score_series(series : pd.Series):
    return zscore(series)

def z_score_point(point : float, mean : float , std : float):
    """
    O(1)
    """
    return (point-mean)/std

def accumulated_normal_distribution(z : float):
    """
    integral de -infinito a z
    """
    return norm.cdf(z)

def accumulated_normal_distribution_interval(z : float, z_0 : float):
    """
    probabilidad acumulada hasta z - probabilidad acumulada hasta z_0
    """

    return norm.cdf(z) - norm.cdf(z_0)


