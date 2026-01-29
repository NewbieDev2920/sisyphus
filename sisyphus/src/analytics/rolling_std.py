import pandas as pd
import math

def rolling_std(df : pd.DataFrame,target : str,index: str,start,end,) -> float:
    data = df[target]
    if type(start) is int and type(end) is int:
        return data.iloc[start:end].std()
    else:
        try:
            string_indexed_df = df.set_index(index)
            return string_indexed_df.loc[start:end,target].std()
        except:
            raise Exception("There is a problem with the current index you gave. (DataFrame indexing ERROR)")

# V(x) = E(x^2) - E(x)^2
#O(1)
def rolling_std_point(expected_value_of_squares: float, square_of_expected_values : float):
    return math.sqrt(expected_value_of_squares-square_of_expected_values)


