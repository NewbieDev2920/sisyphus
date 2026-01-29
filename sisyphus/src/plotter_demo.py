import os 
from dotenv import load_dotenv
from infrastructure.plotter.graph_generator import GraphGenerator
from infrastructure.plotter.visual_function import VisualFunction
from domain.ports.graph.function_type import FunctionType
import numpy as np
import pandas as pd

load_dotenv()

IMAGE_STORAGE_PATH = os.getenv("IMAGE_STORAGE_PATH")

f = VisualFunction("demo(x)",FunctionType.SOFT_CURVE,{"domain":np.linspace(-3,7,500),"range": lambda x: x},"#00FF00")
g = VisualFunction("demo(x)",FunctionType.SOFT_CURVE,{"domain":np.linspace(-1,1,500),"range": lambda x: x*x*x},"#0000FF")
h = VisualFunction("demo(x)",FunctionType.SOFT_CURVE,{"domain":np.linspace(-3,7,500),"range": lambda x: np.sin(x)},"#FF0000")
s = VisualFunction("step_f(x)",FunctionType.SHADED_STEP,{"domain":pd.Series([1,2,3,4,5,6,7]),"range":pd.Series([0,0,0,1,1,1,1])}, "#000000")
graph_generator = GraphGenerator(IMAGE_STORAGE_PATH)
graph_generator.plot_in_R2([f,g,h,s],"lolazo.")