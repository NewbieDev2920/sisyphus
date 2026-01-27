import pandas as pd
import numpy as np

def rolling_std(df : pd.DataFrame,target : str,index: str,start,end,) -> float:
    data = df[target]
    if type(start) is int and type(end) is int:
        return data.iloc[start:end].std()
    else:
        string_indexed_df = df.set_index(index)
        return string_indexed_df.loc[start:end,target].std()
