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
    try:
        import main
        main.print = DebugPrint
        main.input = DebugInput
        main.main()
    except Exception as e:
        name = fl.GetFileName().split("\\")[-1]
        print("error in ", name)
        errMessage = str(e)
    t_end = time.time()

    length = len(statisticsInfoArray)
    name = fl.GetFileName().split("\\")[-1]
    t = t_end - t_start
    csvArr = [name, str(t)]
    for i, name in enumerate(statisticsInfoArray):
        try:
            cont = getattr(main, name)
        except:
            cont = errMessage
        if i == length - 1:
            SetScore(cont)
            print(cont)
        csvArr.append(cont)
    
    AddCSVFile(csvArr)

    #Pythonは自動でimportガードがついてるので一度モジュールを削除する
    if 'main' in sys.modules: del sys.modules["main"]

####################################
#statisticsの管理
def AddCSVFile(ar):
    sl.AddCSVFileSub(ar)

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
    global inputFilePath
    return glob.glob(os.path.join(inputFilePath, "*"))

def GetLogFileName():
    fileName =  fl.GetFileName().split("\\")[-1]
    logFileName = "log_" + fileName
    return logFileName

####################################
#scoreの管理
def SetScore(score):
    fl.SetScoreSub(score)

def WriteScore():

    global scoreFilePath, scoreFileName
    scores = fl.GetScore()
    length = len(scores)
    if length == 0: return
    scoreSum = 0
    scoreMin = float("Inf")
    scoreMinFileName = 0
    scoreMax = -float("Inf")
    scoreMaxFileName = 0
    for i, [fileName, scoreStr] in enumerate(scores):
        score = 0
        try:
            score = int(scoreStr)
        except:
            pass
        fileName = fileName.split("\\")[-1]
        if score < scoreMin:
            scoreMin = score
            scoreMinFileName = fileName
        if scoreMax < score:
            scoreMax = score
            scoreMaxFileName = fileName
        scoreSum += score

    f = open(os.path.join(scoreFilePath, scoreFileName), 'w')
    f.write(str(length) + " files inputs" + "\n")
    f.write("score average is " + str(scoreSum/length) + "\n")
    f.write("max score is " + str(scoreMax) + ", filename is " + scoreMaxFileName + "\n")
    f.write("min score is " + str(scoreMin) + ", filename is " + scoreMinFileName + "\n")
    f.write("\n")
    for fileName, score in scores:
        fileName = fileName.split("\\")[-1]
        f.write(fileName + " " + str(score) + "\n")
    f.close()

####################################
#main

def main():
    fileLis = GetAllFileName()
    ar = ["FileName", "Time"] + statisticsInfoArray
    sl.InitCSV(ar)
    for filename in fileLis:
        fl.SetFileName(filename)
        fl.SetFileContents()
        
        InitLogFile()
        ExacProg()
    WriteScore()
    sl.statisticsMain()
    SaveFile()

if __name__ == "__main__":
    main()
