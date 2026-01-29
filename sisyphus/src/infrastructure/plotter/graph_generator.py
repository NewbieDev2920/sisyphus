from cProfile import label
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
            if f.ftype == FunctionType.LINE_SEGMENTS:
                f_linestyle = "-"
            elif f.ftype == FunctionType.SCATTER:
                f_marker = "."
                f_linestyle = ""
            elif f.ftype == FunctionType.SOFT_CURVE:
                f_linestyle = "-"
            elif f.ftype == FunctionType.STEM:
                pass
            elif f.ftype == FunctionType.SHADED_STEP:
                ymin, ymax = ax.get_ylim()
                ax.fill_between(f.sampled_data["domain"],ymin,ymax, 
                    where = (f.sampled_data["range"] == 1) | (f.sampled_data["range"] == True), color = "green", alpha = 0.21, step="post", label = f.name+" == 1")

                ax.fill_between(f.sampled_data["domain"],ymin,ymax, 
                    where = (f.sampled_data["range"] == 0) | (f.sampled_data["range"] == False), color = "red", alpha = 0.21, step="post", label = f.name+ " == 0")
            
            if f.ftype is not FunctionType.STEM and f.ftype is not FunctionType.SHADED_STEP:
                ax.plot(f.sampled_data["domain"],f.sampled_data["range"](f.sampled_data["domain"]), 
                    label = f.name, color = f.color, marker = f_marker, linestyle= f_linestyle
                )
            elif f.ftype is not FunctionType.SHADED_STEP:
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

    #series must be a list of pd.Series
    #colors must be a list of strings in #RRGGBB format
    def plot_hist(self, series : list, title : str ,x_axis_label : str, colors : list ,bins = 12 ,density = False):
        plt.style.use('seaborn-v0_8')
        fig, ax = plt.subplots()
        ax.set_xlabel(x_axis_label)
        ax.set_title(title)
        ax.hist(series, density = density, bins= bins, color=color)
        figure_name = hash_gen()
        plt.savefig(self.IMAGE_STORAGE_PATH+figure_name+".jpg")
        print("HISTOGRAM GENERATED AND SAVED SUCCESSFULLY!")


