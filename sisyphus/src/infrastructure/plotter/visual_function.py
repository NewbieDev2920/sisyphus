from domain.ports.graph.visual_function_port import VisualFunctionPort
from domain.ports.graph.function_type import FunctionType
import pandas as pd
import numpy as np
 # SAMPLED DATA dict format 
 #{"domain":pd.Series,"range":pd.Series} for discrete data
 #{"domain": np.linspace(min,max,qt), "range": python function (lambda is better)}

class VisualFunction(VisualFunctionPort):
    def __init__(self, name: str, ftype :FunctionType, sampled_data : dict, color: str):
        self.name = name
        self.ftype = ftype
        self.sampled_data = sampled_data
        #Color must be in hexadecimal format. #RRGGBB
        self.color = color

        
            
            
