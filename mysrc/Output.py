import shutil
import glob
import datetime
import os
import csv

from mysrc.MyLib import ResultInfo
from mysrc.HTMLtemplate import *
from mysrc.settings import *

CSVHeader = ["Test Case Name", "Score", "Time"] + statisticsInfoArray

####################################
def InitAll() -> None:
    """初期化処理のまとめ"""
    InitLogFile()

def MakeAllResult(resultAll: list[ResultInfo]) -> None:
    """ファイルに出力処理のまとめ"""
    MakeHTML(resultAll)
    MakeCSVFile(resultAll)
    if makeFigure:
        import mysrc.StatisticsLib as sl #外部モジュールのimportが必要なのでここに
        sl.statisticsMain()
    MakeLog()

####################################
def InitLogFile() -> None:
    """Logフォルダの初期化"""
    shutil.rmtree(resultFilePath, ignore_errors=True)
    os.mkdir(resultFilePath)

####################################
def MakeCSVFile(resultAll: list[ResultInfo]) -> None:
    """CSVファイルを作成"""
    InitCSV()
    AddCSVFile(CSVHeader)
    for result in resultAll:
        AddCSVFile(result.GetMember())

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

####################################
def MakeSummaryInfo(resultAll: list[ResultInfo]) -> str:
    """サマリ情報を作る"""
    fileNameList, scoresList = [], []
    for result in resultAll:
        fileNameList.append(os.path.basename(result.name))
        scoresList.append(0 if result.score == "None" else int(result.score))

    string = []
    string.append(str(len(resultAll)) + " files inputs")
    string.append("score average is " + str(sum(scoresList)/len(resultAll)))
    string.append("max score is " + str(max(scoresList)) + ", filename is " +\
         fileNameList[scoresList.index(max(scoresList))])
    string.append("min score is " + str(min(scoresList)) + ", filename is " +\
         fileNameList[scoresList.index(min(scoresList))])
    string.append("")
    return "<br>\n".join(string)

####################################

def InsertTextIntoHTMLHead(tag: str, HTMLStr: str, text: str) -> str:
    """HTMLの文字列のtagの中に別の文字列を挿入する"""
    HTMLStrList = HTMLStr.split("\n")
    HTMLStrList.insert(HTMLStrList.index(tag) + 1, text)
    return "\n".join(HTMLStrList)

def MakeHTML(resultAll: list[ResultInfo]) -> None:
    """結果のHTMLファイルを作成する"""
    tableBody = []
    table = ""
    for s in CSVHeader: table += TableCellHeading.format(text=s)
    tableBody.append(TableLine.format(text=table))
    for result in resultAll:
        table = ""
        link = HTMLLinkStr.format(path=os.path.join(inputFilePath, result.name), string=result.name)
        table += TableCell.format(text=link)
        if not result.errFlg:
            text = str(result.score)
            link = HTMLLinkStr.format(path=os.path.join(resultFilePath, result.name), string=text)
            table += TableCell.format(text=link)
        else:
            text = "RE"
            link = HTMLLinkStr.format(path=os.path.join(resultFilePath, result.name), string=text)
            table += TableColoredCell.format(color="gold", text=link)
        table += TableCell.format(text=str(round(result.time, 3)))
        for x in result.otherList: table += TableCell.format(text=str(x))
        tableBody.append(TableLine.format(text=table))
    tableAll = "<h2>Table</h2>"
    tableAll += TableHeading.format(body="\n".join(tableBody))

    body = "<h2>Summary</h2>"
    body += MakeSummaryInfo(resultAll)
    body += tableAll

    resultFileName = "result.html"
    with open(resultFileName ,'w', encoding='utf-8', newline='\n') as html:
        text = HTMLText.format(body=body, title="Result")
        text = InsertTextIntoHTMLHead("<body>", text, cssLink1)
        text = InsertTextIntoHTMLHead("<body>", text, cssLink2)
        text = InsertTextIntoHTMLHead("<body>", text, scriptLink)
        html.writelines(text)

####################################
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
