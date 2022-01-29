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
import traceback
from typing import Any
from template import *

####################################
def ExacProg() -> ResultInfo:
    """プログラムを実行して結果を返す"""
    t_start = time.time()
    errMessage = ""
    name = os.path.basename(fl.GetFileName())
    errFlg = False
    try:
        import main
        main.print = DebugPrint
        main.input = DebugInput
        main.main()
    except:
        errFlg = True
        print("error in ", name)
        errMessage = traceback.format_exc()
    t_end = time.time()

    try:    score = str(getattr(main, scoreStr))
    except: score = "None"

    lis = []
    for val in statisticsInfoArray:
        try:    cont = str(getattr(main, val))
        except: cont = "None"
        lis.append(cont)

    #Pythonは自動でimportガードがついてるので一度モジュールを削除する
    if 'main' in sys.modules: del sys.modules["main"]

    return ResultInfo(name, score, t_end-t_start, errFlg, errMessage, lis)

####################################
def MakeLog() -> None:
    """summaryファイル, csv, mainファイルをコピーしてlog以下に保存する"""
    timeInfo = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    path =  os.path.join(logFilePath, str(timeInfo))
    os.mkdir(path)

    # mainファイルコピー
    shutil.copy("main.py", path)
    # summaryファイルコピー
    shutil.copy(os.path.join(scoreFilePath, scoreFileName), path)
    # csvファイルコピー
    shutil.copy(os.path.join(statisticsDirec, csvFileName), path)

####################################
def DebugPrint(*arg: Any, **keys: Any) -> None:
    """Debug用の出力"""
    f = open(os.path.join(resultFilePath, GetLogFileName()), 'a')
    print(*arg, **keys, file=f)
    f.close()

def DebugInput() -> str:
    """Debug用の入力"""
    return str(fl.fileContents.pop())

####################################
def InitLogFile() -> None:
    """Logフォルダの初期化"""
    shutil.rmtree(resultFilePath, ignore_errors=True)
    os.mkdir(resultFilePath)

def GetAllFileName() -> list[str]:
    """inputするファイルすべての名前を取得"""
    return glob.glob(os.path.join(inputFilePath, "*"))

def GetLogFileName() -> str:
    """現在のLogファイルの名前を返す"""
    return "log_" + os.path.basename(fl.GetFileName())

####################################
def MakeCSVFile(resultAll):
    sl.InitCSV()
    sl.AddCSVFile(sl.CSVHeader)
    for result in resultAll:
        sl.AddCSVFile(result.GetMember())

####################################
def MakeSummaryFile(resultAll: list[ResultInfo]) -> None:
    """サマリファイルを作る"""
    fileNameList, scoresList = [], []
    for result in resultAll:
        fileNameList.append(os.path.basename(result.name))
        scoresList.append(0 if result.score == "None" else int(result.score))

    f = open(os.path.join(scoreFilePath, scoreFileName), 'w')
    f.write(str(len(resultAll)) + " files inputs" + "\n")
    f.write("score average is " + str(sum(scoresList)/len(resultAll)) + "\n")
    f.write("max score is " + str(max(scoresList)) + ", filename is " + fileNameList[scoresList.index(max(scoresList))] + "\n")
    f.write("min score is " + str(min(scoresList)) + ", filename is " + fileNameList[scoresList.index(min(scoresList))] + "\n")
    f.write("\n")
    for result in resultAll:
        f.write(os.path.basename(result.name) + " " + str(result.score) + "\n")
    f.close()

####################################
#main

def main() -> None:
    resultAll = []
    InitLogFile()
    for filename in GetAllFileName():
        fl.SetFileName(filename)
        fl.SetFileContents()
        result = ExacProg()
        resultAll.append(result)
    MakeSummaryFile(resultAll)
    MakeCSVFile(resultAll)
    sl.statisticsMain()
    MakeLog()

if __name__ == "__main__":
    main()
