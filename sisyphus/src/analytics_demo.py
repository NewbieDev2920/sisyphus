import pandas as pd
from analytics.rolling_std import rolling_std
import matplotlib.pyplot as plt

player_list = [['M.S.Dhoni', 36, 75, 5428000],
               ['A.B.D Villers', 38, 74, 3428000],
               ['V.Kohli', 31, 70, 8428000],
               ['S.Smith', 34, 80, 4428000],
               ['C.Gayle', 40, 100, 4528000],
               ['J.Root', 33, 72, 7028000],
               ['K.Peterson', 42, 85, 2528000]]


df = pd.DataFrame(player_list, columns=["Name","age","score","salary"])

std_r = rolling_std(df,"salary","Name","V.Kohli","C.Gayle")

series = df["salary"]

print(series.ewm(alpha = 2/3).mean())



