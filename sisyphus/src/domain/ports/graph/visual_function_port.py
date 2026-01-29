from abc import ABC, abstractmethod
from domain.ports.graph.function_type import FunctionType


class VisualFunctionPort(ABC):
    def __init__(self, name: str, ftype : FunctionType, sampled_data, color: str):
        self.name = name
        self.ftype = ftype
        self.sampled_dat = sampled_data
        #RRGGBB
        self.color = color
