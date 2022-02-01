import shutil
import glob
import datetime
import os

from MyLib import ResultInfo
from HTMLtemplate import *
from settings import *
import StatisticsLib as sl

CSVHeader = ["Test Case Name", "Score", "Time"] + statisticsInfoArray

####################################
def InitAll():
    InitLogFile()

def MakeAllResult(resultAll):
    MakeSummaryFile(resultAll)
    MakeHTML(resultAll)
    if makeCSV:
        MakeCSVFile(resultAll)
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
    sl.InitCSV()
    sl.AddCSVFile(CSVHeader)
    for result in resultAll:
        sl.AddCSVFile(result.GetMember())

####################################
def MakeSummaryFile(resultAll: list[ResultInfo]) -> None:
    """サマリファイルを作る"""
    fileNameList, scoresList = [], []
    for result in resultAll:
        fileNameList.append(os.path.basename(result.name))
        scoresList.append(0 if result.score == "None" else int(result.score))

    f = open(scoreFileName, 'w')
    f.write(str(len(resultAll)) + " files inputs" + "\n")
    f.write("score average is " + str(sum(scoresList)/len(resultAll)) + "\n")
    f.write("max score is " + str(max(scoresList)) + ", filename is " + fileNameList[scoresList.index(max(scoresList))] + "\n")
    f.write("min score is " + str(min(scoresList)) + ", filename is " + fileNameList[scoresList.index(min(scoresList))] + "\n")
    f.write("\n")
    for result in resultAll:
        f.write(os.path.basename(result.name) + " " + str(result.score) + "\n")
    f.close()

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
    tableAll = TableHeading.format(body="\n".join(tableBody))

    resultFileName = "result.html"
    with open(resultFileName ,'w', encoding='utf-8', newline='\n') as html:
        text = HTMLText.format(body=tableAll, title="Result")
        text = InsertTextIntoHTMLHead("<body>", text, cssLink)
        text = InsertTextIntoHTMLHead("<body>", text, scriptLink)
        html.writelines(text)

####################################
def MakeLog() -> None:
    """summary, csv, mainファイルをコピーしてlog以下に保存する"""
    timeInfo = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    if logFilePath not in glob.glob("*"): os.mkdir(logFilePath)
    path =  os.path.join(logFilePath, str(timeInfo))
    os.mkdir(path)

    # mainファイルコピー
    shutil.copy("main.py", path)
    # summaryファイルコピー
    shutil.copy(scoreFileName, path)
    # csvファイルコピー
    shutil.copy(os.path.join(statisticsDirec, csvFileName), path)
