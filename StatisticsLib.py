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

def InitCSV(ar):
    global statisticsDirec, csvFileName
    path = os.path.join(statisticsDirec, csvFileName)
    ar = list(map(str, ar))
    with open(path, 'w', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(ar)

def AddCSVFileSub(ar):
    global statisticsDirec, csvFileName
    path = os.path.join(statisticsDirec, csvFileName)
    ar = list(map(str, ar))
    with open(path, 'a', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(ar)


def statisticsMain():
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

