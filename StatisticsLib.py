import pandas as pd
import matplotlib.pyplot as plt
import os

from settings import *

####################################
def statisticsMain() -> None:
    """統計処理のmain処理"""
    df = pd.read_csv(os.path.join(statisticsDirec, csvFileName))
    for x in statisticsInfoArray:
        ax_x, ax_y = x, scoreStr
        df.plot.scatter(x = ax_x, y = ax_y, alpha = 0.5)
        outPath = os.path.join(statisticsDirec, ax_x + "-" + ax_y + ".png")
        plt.savefig(outPath)
        plt.close('all')

if __name__ == "__main__":
    statisticsMain()

