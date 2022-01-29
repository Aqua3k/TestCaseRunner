import csv
import pandas as pd
import matplotlib.pyplot as plt
import DebugLib as dl
import shutil
from settings import *
import os

CSVHeader = ["FileName", "score", "Time"] + statisticsInfoArray

####################################

def InitCSV() -> None:
    """CSVフォルダを初期化する"""
    shutil.rmtree(statisticsDirec, ignore_errors=True)
    os.mkdir(statisticsDirec)

def AddCSVFile(array: list[str]) -> None:
    """CSVファイルにarrayを追加する"""
    path = os.path.join(statisticsDirec, csvFileName)
    array = list(map(str, array))
    with open(path, 'a', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(array)

def statisticsMain() -> None:
    """統計処理のmain処理"""
    df = pd.read_csv(os.path.join(statisticsDirec, csvFileName))
    for x in dl.statisticsInfoArray:
        ax_x, ax_y = x, scoreStr
        df.plot.scatter(x = ax_x, y = ax_y, alpha = 0.5)
        outPath = os.path.join(statisticsDirec, ax_x + "-" + ax_y + ".png")
        plt.savefig(outPath)
        plt.close('all')

if __name__ == "__main__":
    statisticsMain()

