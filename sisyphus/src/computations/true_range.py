import math

#Diseñado para average_true_range

def true_range(high : float, low : float, yesterday_closing_price : float) -> float:
    return max(high-low,abs(high-yesterday_closing_price),abs(low-yesterday_closing_price))
