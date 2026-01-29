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
#
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
        

    
