import pandas as pd

class MockStream:
    
    def __init__(self, df : pd.DataFrame):
        self.df = df
