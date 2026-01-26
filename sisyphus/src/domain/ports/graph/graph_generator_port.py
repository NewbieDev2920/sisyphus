from abc import ABC, abstractmethod

class GraphGeneratorPort(ABC):
    """
    -Series de tiempo.
    -Funciones suavizadas.
    -Regiones (para stepfunction)
    -Labels
    -Scatter plot
    -Stem Plot
    """

    #a_axis = {"label":"insert label", "type": ENUM label type}
    @abstractmethod
    def plot(self, function_list : list, title: str , x_axis : dict, y_axis: dict): 
        pass

    #f : R -> R, both axis are continuous.
    #Reuse the complete plt.
    @abstractmethod
    def plot(self, function_list: list, title:str):
        pass

    #f: Date -> R, From date to real magnitude, desgined for financial time series.
    #Reuse the complete plt.
    @abstractmethod
    def plot_time_series(self, function_list: list, title:str):
        pass

