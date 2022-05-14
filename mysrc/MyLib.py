import os
import datetime
import csv
import shutil
import copy
from typing import Any

from mysrc.HTMLtemplate import *
from mysrc.settings import *

CSVHeader = ["Test Case Name", "Score", "Time"] + statisticsInfoArray

class ResultInfo:
    """実行結果の情報管理用のクラス"""
    AC = 0
    RE = 1
    TLE = 2
    def __init__(self, name: str, score: str, time: float, errStatus: int, stdOut: str, otherList: list[Any]):
        self.name      = name
        self.score     = score
        self.time      = time
        self.errStatus = errStatus
        self.otherList = copy.deepcopy(otherList)
        self.stdOut    = stdOut
    def GetMember(self) -> list[str]:
        """結果を配列にする"""
        ret = [self.name, self.score, self.time] + copy.deepcopy(self.otherList)
        return ret
    def __lt__(self, other) -> bool:
        """__lt__を定義しておくとクラスのままソートが可能になる"""
        return self.name < other.name


class ResultInfoAll:
    def __init__(self):
        self.result_all = []
    
    def add_result(self, result_info):
        """結果情報を追加する"""
        self.result_all.append(result_info)
    
    def make_html_file(self):
        """結果のHTMLファイルを作成する"""
        tableBody = []
        table = ""
        table += '<th>in</th>'
        table += '<th>out</th>'
        table += '<th>stdout</th>'
        for s in CSVHeader: table += TableCellHeading.format(text=s)
        tableBody.append(TableLine.format(text=table))
        for result in self.result_all:
            table = ""
            link1 = HTMLLinkStr.format(path=os.path.join(inputFilePath, result.name), string="+")
            table += TableCell.format(text=link1)
            link2 = HTMLLinkStr.format(path=os.path.join(resultFilePath, result.name), string="+")
            table += TableCell.format(text=link2)
            link3 = HTMLLinkStr.format(path=os.path.join(resultFilePath, "stdout" + result.name), string="+")
            table += TableCell.format(text=link3)

            table += TableCell.format(text=result.name)
            if result.errStatus == ResultInfo.AC:
                text = str(result.score)
                table += TableCell.format(text=text)
            elif result.errStatus == ResultInfo.RE:
                text = "RE"
                table += TableColoredCell.format(color="gold", text=text)
            elif result.errStatus == ResultInfo.TLE:
                text = "TLE"
                table += TableColoredCell.format(color="gold", text=text)
            else: assert 0, "error in MakeHTML function."
            table += TableCell.format(text=str(round(result.time, 3)))
            for x in result.otherList: table += TableCell.format(text=str(x))
            tableBody.append(TableLine.format(text=table))
        tableAll = "<h2>Table</h2>"
        tableAll += TableHeading.format(body="\n".join(tableBody))
        
        now = datetime.datetime.now()
        nowStr = now.strftime('%Y/%m/%d %H:%M:%S')
        body = '<h6>Creation date and time: {text}</h6>'.format(text=nowStr)
        
        body += "<h2>Summary</h2>"
        body += self.MakeSummaryInfo()
        body += tableAll

        resultFileName = "result.html"
        with open(resultFileName ,'w', encoding='utf-8', newline='\n') as html:
            text = HTMLText.format(body=body, title="Result")
            text = self.InsertTextIntoHTMLHead("<body>", text, cssLink1)
            text = self.InsertTextIntoHTMLHead("<body>", text, cssLink2)
            text = self.InsertTextIntoHTMLHead("<body>", text, scriptLink)
            html.writelines(text)

    def MakeSummaryInfo(self) -> str:
        """サマリ情報を作る"""
        fileNameList, scoresList = [], []
        for result in self.result_all:
            fileNameList.append(os.path.basename(result.name))
            scoresList.append(0 if result.score == "None" or result.errStatus != ResultInfo.AC else int(result.score))

        string = []
        string.append("Input file number: " + str(len(self.result_all)))
        string.append("Average Score: " + str(sum(scoresList)/len(self.result_all)))
        string.append("")
        string.append("Max Score: " + str(max(scoresList)))
        string.append("FileName: " + fileNameList[scoresList.index(max(scoresList))])
        string.append("")
        string.append("Minimum Score: " + str(min(scoresList)))
        string.append("FileName: " + fileNameList[scoresList.index(min(scoresList))])
        string.append("")
        return "<br>\n".join(string)
    
    def InsertTextIntoHTMLHead(self, tag: str, HTMLStr: str, text: str) -> str:
        """HTMLの文字列のtagの中に別の文字列を挿入する"""
        HTMLStrList = HTMLStr.split("\n")
        HTMLStrList.insert(HTMLStrList.index(tag) + 1, text)
        return "\n".join(HTMLStrList)
    
    def MakeCSVFile(self) -> None:
        """CSVファイルを作成"""
        self.InitCSV()
        self.AddCSVFile(CSVHeader)
        for result in self.result_all:
            self.AddCSVFile(result.GetMember())
    
    def InitCSV(self) -> None:
        """CSVフォルダを初期化する"""
        shutil.rmtree(statisticsDirec, ignore_errors=True)
        os.mkdir(statisticsDirec)

    def AddCSVFile(self, array: list[str]) -> None:
        """CSVファイルにarrayを追加する"""
        path = os.path.join(statisticsDirec, csvFileName)
        array = list(map(str, array))
        with open(path, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow(array)
