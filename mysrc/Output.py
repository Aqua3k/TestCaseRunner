import shutil
import glob
import datetime
import os
import datetime

from mysrc.MyLib import ResultInfoAll
from mysrc.HTMLtemplate import *
from mysrc.settings import *

CSVHeader = ["Test Case Name", "Score", "Time"] + statisticsInfoArray

def InitAll() -> None:
    """初期化処理のまとめ"""
    InitLogFile()

def MakeAllResult(resultAll: ResultInfoAll) -> None:
    """ファイルに出力処理のまとめ"""
    resultAll.make_html_file()
    resultAll.MakeCSVFile()
    if makeFigure:
        import mysrc.StatisticsLib as sl #外部モジュールのimportが必要なのでここに
        sl.statisticsMain()
    MakeLog()

def InitLogFile() -> None:
    """Logフォルダの初期化"""
    shutil.rmtree(resultFilePath, ignore_errors=True)
    os.mkdir(resultFilePath)

def InitCSV() -> None:
    """CSVフォルダを初期化する"""
    shutil.rmtree(statisticsDirec, ignore_errors=True)
    os.mkdir(statisticsDirec)

def MakeLog() -> None:
    """html, csv, mainファイルをコピーしてlog以下に保存する"""
    timeInfo = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    if logFilePath not in glob.glob("*"): os.mkdir(logFilePath)
    path =  os.path.join(logFilePath, str(timeInfo))
    os.mkdir(path)

    # mainファイルコピー
    shutil.copy("main.py", path)
    # htmlファイルコピー
    shutil.copy("result.html", path)
    # csvファイルコピー
    shutil.copy(os.path.join(statisticsDirec, csvFileName), path)
