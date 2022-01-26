import sys
import csv
import FileLib as fl
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import DebugLib as dl
from settings import *
import os

####################################

def InitCSV(array: list[str]) -> None:
    """CSVファイルを作成しarrayを書き込む"""
    global statisticsDirec, csvFileName
    path = os.path.join(statisticsDirec, csvFileName)
    array = list(map(str, array))
    with open(path, 'w', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(array)

def AddCSVFileSub(array: list[str]) -> None:
    """CSVファイルにarrayを追加する"""
    global statisticsDirec, csvFileName
    path = os.path.join(statisticsDirec, csvFileName)
    array = list(map(str, array))
    with open(path, 'a', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(array)


def statisticsMain() -> None:
    """統計処理のmain処理"""
    global statisticsDirec, csvFileName
    path = os.path.join(statisticsDirec, csvFileName)
    df = pd.read_csv(path)

    statisticsInfo = dl.statisticsInfoArray
    length = len(statisticsInfo)
    for x in statisticsInfo[1:length-1]:
        ax_x = x
        ax_y = statisticsInfo[-1]
        df.plot.scatter(x = ax_x, y = ax_y, alpha = 0.5)
        outPath = os.path.join(statisticsDirec, ax_x, "-", ax_y, ".png")
        plt.savefig(outPath)
        plt.close('all')

if __name__ == "__main__":
    statisticsMain()

