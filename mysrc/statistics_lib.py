import pandas as pd
import matplotlib.pyplot as plt
import os

from mysrc.settings import *

scoreStr   = "score"

def statisticsMain() -> None:
    """統計処理のmain処理"""
    df = pd.read_csv(os.path.join(statistics_path, csv_file_name))
    for x in statistics_info_define_array:
        ax_x, ax_y = x, scoreStr
        df.plot.scatter(x = ax_x, y = ax_y, alpha = 0.5)
        outPath = os.path.join(statistics_path, ax_x + "-" + ax_y + ".png")
        plt.savefig(outPath)
        plt.close('all')

if __name__ == "__main__":
    statisticsMain()

