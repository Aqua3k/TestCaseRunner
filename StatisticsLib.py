import sys
import csv
import FileLib as fl
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import DebugLib as dl
import settings as stg

####################################
# settings

#入力が書いてある場所
statisticsDirec = stg.statisticsDirec
csvFileName = stg.csvFileName

####################################

def InitCSV(ar):
    global statisticsDirec, csvFileName
    path = statisticsDirec + csvFileName
    ar = list(map(str, ar))
    with open(path, 'w', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(ar)

def AddCSVFileSub(ar):
    global statisticsDirec, csvFileName
    path = statisticsDirec + csvFileName
    ar = list(map(str, ar))
    with open(path, 'a', newline="") as f:
        writer = csv.writer(f)
        writer.writerow(ar)


def statisticsMain():
    global statisticsDirec, csvFileName
    path = statisticsDirec + csvFileName
    df = pd.read_csv(path)

    statisticsInfo = dl.statisticsInfoArray
    length = len(statisticsInfo)
    for x in statisticsInfo[1:length-1]:
        ax_x = x
        ax_y = statisticsInfo[-1]
        df.plot.scatter(x = ax_x, y = ax_y, alpha = 0.5)
        outPath = statisticsDirec + ax_x + "-" + ax_y + ".png"
        plt.savefig(outPath)
        plt.close('all')

if __name__ == "__main__":
    statisticsMain()

