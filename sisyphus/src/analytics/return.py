import math 

def abs_return(final_value: float, initial_value:float) -> float:
    return final_value - initial_value

def percentage_return(final_value : float,initial_value : float) -> float:
    return (abs_return(final_value,initial_value)/final_value) * 100

def log_return(final_value : float, initial_value : float) -> float:
    return math.log(1+ percentage_return(final_value,initial_value))

    
