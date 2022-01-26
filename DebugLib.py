import sys
import glob
import FileLib as fl
import pandas as pd
import StatisticsLib as sl
from settings import *
import time
import os
import datetime
import shutil

####################################
def ExacProg():
    #プログラムの実行(名前が変わったなら変える)
    t_start = time.time()
    errMessage = "NaN"
    name = os.path.basename(fl.GetFileName())
    try:
        import main
        main.print = DebugPrint
        main.input = DebugInput
        main.main()
    except Exception as e:        
        print("error in ", name)
        errMessage = str(e)
    t_end = time.time()

    csvArr = [name, str(t_end - t_start)]
    for i, name in enumerate(statisticsInfoArray):
        try:    cont = getattr(main, name)
        except: cont = errMessage
        if i == len(statisticsInfoArray) - 1:
            fl.SetScoreSub(cont)
            print(cont)
        csvArr.append(cont)
    
    sl.AddCSVFileSub(csvArr)

    #Pythonは自動でimportガードがついてるので一度モジュールを削除する
    if 'main' in sys.modules: del sys.modules["main"]

####################################
#summaryファイル, csv, mainファイルをコピーして保存する
def SaveFile():
    dt = datetime.datetime.now()
    d = dt.strftime('%Y%m%d%H%M%S')
    path =  os.path.join(logFilePath, str(d))
    os.mkdir(path)

    # mainファイルコピー
    filePath = "main.py"
    shutil.copy(filePath, path)

    # summaryファイルコピー
    filePath = os.path.join(scoreFilePath, scoreFileName)
    shutil.copy(filePath, path)

    # csvファイルコピー
    filePath = os.path.join(statisticsDirec, csvFileName)
    shutil.copy(filePath, path)

####################################
#Debug用の入出力

def DebugPrint(*arg, **keys):
    f = open(os.path.join(resultFilePath, GetLogFileName()), 'a')
    print(*arg, **keys, file=f)
    f.close()

def DebugInput():
    return str(fl.fileContents.pop())

####################################
#logファイルの管理

def InitLogFile():
    f = open(os.path.join(resultFilePath, GetLogFileName()), 'w')
    f.close()

def GetAllFileName():
    return glob.glob(os.path.join(inputFilePath, "*"))

def GetLogFileName():
    return "log_" + os.path.basename(fl.GetFileName())

####################################
#scoreの管理
def WriteScore():
    global scoreFilePath, scoreFileName
    scores = fl.GetScore()
    fileNameList, scoresList = [], []
    for i, [filePath, scoreStr] in enumerate(scores):
        fileName = os.path.basename(filePath)
        try:    score = int(scoreStr)
        except: score = 0
        fileNameList.append(fileName)
        scoresList.append(score)
    
    f = open(os.path.join(scoreFilePath, scoreFileName), 'w')
    f.write(str(len(scores)) + " files inputs" + "\n")
    f.write("score average is " + str(sum(scoresList)/len(scores)) + "\n")
    f.write("max score is " + str(max(scoresList)) + ", filename is " + fileNameList[scoresList.index(max(scoresList))] + "\n")
    f.write("min score is " + str(min(scoresList)) + ", filename is " + fileNameList[scoresList.index(min(scoresList))] + "\n")
    f.write("\n")
    for fileName, score in scores:
        f.write(os.path.basename(fileName) + " " + str(score) + "\n")
    f.close()

####################################
#main

def main():
    ar = ["FileName", "Time"] + statisticsInfoArray
    sl.InitCSV(ar)
    for filename in GetAllFileName():
        fl.SetFileName(filename)
        fl.SetFileContents()
        
        InitLogFile()
        ExacProg()
    WriteScore()
    sl.statisticsMain()
    SaveFile()

if __name__ == "__main__":
    main()
