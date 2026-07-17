import pandas as pd

#O(n)
def rolling_avg(df : pd.DataFrame,target : str,index: str,start,end,) -> float:
    data = df[target]
    if type(start) is int and type(end) is int:
        return data.iloc[start:end].mean()
    else:
        try:
            string_indexed_df = df.set_index(index)
            return string_indexed_df.loc[start:end,target].mean()
        except:
            raise Exception("There is a problem with the current index you gave. (DataFrame indexing ERROR)")


#O(1)
#Revisar funcion
def next_rolling_avg(df : pd.DataFrame, current_rolling_avg : float,target : str,new_start,new_end,) -> float:
    if type(new_start) is not int or type(new_end) is not int:
        new_start = df.index.get_loc(new_start)
        new_end = df.index.get_loc(new_end)
    window_size = new_end - new_start + 1
    if window_size < 0:
        raise Exception("There is something wrong, new_end - new_start can't be less than 0")
    data = df[target]
    if type(new_start) is int and type(new_end) is int:
        return current_rolling_avg + (-data.iloc[new_start]+data.iloc[new_end])/window_size

# O(1) Matemático puro
def next_sma_point(current_sma: float, new_value: float, old_value: float, window_size: int) -> float:
    """
    Calcula el siguiente punto de la media móvil simple en O(1).
    Fórmula: SMA_actual + (nuevo_valor - valor_viejo_saliendo_ventana) / tamaño_ventana
    """
    if window_size <= 0:
        raise ValueError("El tamaño de la ventana debe ser mayor a 0")
    return current_sma + (new_value - old_value) / window_size

import numpy as np

def compute_wma(window: list, weights: np.ndarray) -> float:
    """
    Calcula la media móvil ponderada realizando un producto punto entre
    la ventana de valores y los pesos inyectados.
    Complejidad O(n).
    """
    if len(window) != len(weights):
        raise ValueError("El tamaño de la ventana debe coincidir con el tamaño de los pesos")
    
    np_window = np.array(window)
    # Si los pesos ya están normalizados (suman 1), se puede quitar la división
    return np.dot(np_window, weights) / np.sum(weights)
