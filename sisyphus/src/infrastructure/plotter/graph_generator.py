from domain.ports.graph.graph_generator_port import GraphGeneratorPort
from domain.ports.graph.function_type import FunctionType
from domain.ports.graph.axis_type import AxisType
from utils.hash_gen import hash_gen 
import matplotlib.pyplot as plt


class GraphGenerator(GraphGeneratorPort):

    def __init__(self, IMAGE_STORAGE_PATH):
        self.IMAGE_STORAGE_PATH = IMAGE_STORAGE_PATH

    def plot(self, function_list : list, title: str, x_axis: dict, y_axis: dict, figure_size = (5,2.7)):
        plt.style.use('seaborn-v0_8')
        fig, ax = plt.subplots(figsize = figure_size, layout="constrained")        
        for f in function_list:
            f_marker = None
            f_linestyle = None
            if f.type == FunctionType.LINE_SEGMENTS:
                f_linestyle = "-"
            elif f.type == FunctionType.SCATTER:
                f_marker = "."
                f_linestyle = ""
            elif f.type == FunctionType.SOFT_CURVE:
                f_linestyle = "-"
            elif f.type == FunctionType.STEM:
                pass
            
            if f.type is not FunctionType.STEM:
                ax.plot(f.sampled_data["domain"],f.sampled_data["range"](f.sampled_data["domain"]), 
                    label = f.name, color = f.color, marker = f_marker, linestyle= f_linestyle
                )
            else:
                ax.stem(f.sampled_data["domain"],f.sampled_data["range"](f.sampled_data["domain"]))
        
        ax.set_xlabel(x_axis["label"])
        ax.set_ylabel(y_axis["label"])
        ax.set_title(title)
        ax.legend()
        figure_name = hash_gen()
        plt.savefig(self.IMAGE_STORAGE_PATH+figure_name+".jpg")
        print("FIGURE GENERATED AND SAVED SUCCESSFULLY!")



    def plot_in_R2(self, function_list: list, title: str):
        self.plot(function_list,title,{"label":"x","type": AxisType.CONTINUOUS},{"label":"x","type":AxisType.CONTINUOUS})

    def plot_time_series(self, function_list : list, title : str):
        self.plot(function_list,title,{"label":"time","type": AxisType.DATE},{"label":"f(t)","type":AxisType.CONTINUOUS})