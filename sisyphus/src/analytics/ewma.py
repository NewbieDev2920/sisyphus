import pandas as pd
import math

#CALCULATE EWMA SERIES AND EWMA LAST VALUE O(N), AVOID USING EWMA_POINT.

def ewma_series(series : pd.Series , alpha : float) -> pd.Series:
    return series.ewm(alpha = alpha).mean()

def ewma_point(series : pd.Series, alpha : float) -> float:
    return series.ewm(alpha = alpha).mean().iloc[len(series)-1]

def ewma_series(series : pd.Series , halflife : float) -> pd.Series:
    return series.ewm(halflife = halflife).mean()

def ewma_point(series : pd.Series, halflife : float) -> float:
    return series.ewm(halflife=halflife).mean().iloc[len(series)-1]

def ewma_series(series : pd.Series , com : float) -> pd.Series:
    return series.ewm(com = com).mean()

def ewma_point(series : pd.Series, com : float) -> float:
    return series.ewm(com=com).mean().iloc[len(series)-1]

### CALCULATE NEW EWMA O(1)

def next_ewma_point(current_ewma : float, point : float ,alpha : float) -> float:
    return alpha*point + (1-alpha)*current_ewma

def next_ewma_point(current_ewma : float, point : float, halflife : float) -> float:
    if halflife <= 0:
        raise Exception("halflife must hold the following condition: \n halflife > 0")
    alpha =  1 - math.exp(-math.log(2)/halflife)
    return alpha*point + (1-alpha)*current_ewma

def next_ewma_point(current_ewma : float, point : float, com : float) -> float :
    if com < 0:
        raise Exception("com must hold the following condition: \n com >= 0")
    alpha = 1/(1+com)
    return alpha*point + (1-alpha)*current_ewma

