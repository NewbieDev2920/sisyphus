import pandas as pd

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
