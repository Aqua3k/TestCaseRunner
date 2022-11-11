import os
import datetime
import copy

from mysrc.html_templates import *
from mysrc.settings import *

csv_header = ["Test Case Name", "Score", "Time"]

class ResultInfo:
    """実行結果の情報管理用のクラス"""
    AC = 0
    RE = 1
    TLE = 2
    def __init__(self, name: str, score: str, time: float, err_stat: int, stdOut: str):
        self.name      = name
        self.score     = score
        self.time      = time
        self.err_stat = err_stat
        self.stdOut    = stdOut
    def get_all_members(self):
        """結果を配列にする"""
        ret = [self.name, self.score, self.time]
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
        table_body = []
        table = ""
        table += '<th>in</th>'
        table += '<th>out</th>'
        table += '<th>stdout</th>'
        for s in csv_header: table += table_cell_heading.format(text=s)
        table_body.append(table_line.format(text=table))
        for result in self.result_all:
            table = ""
            link1 = html_link_str.format(path=os.path.join(input_file_path, result.name), string="+")
            table += table_cell.format(text=link1)
            link2 = html_link_str.format(path=os.path.join(result_file_path, result.name), string="+")
            table += table_cell.format(text=link2)
            link3 = html_link_str.format(path=os.path.join(result_file_path, "stdout" + result.name), string="+")
            table += table_cell.format(text=link3)

            table += table_cell.format(text=result.name)
            if result.err_stat == ResultInfo.AC:
                text = str(result.score)
                table += table_cell.format(text=text)
            elif result.err_stat == ResultInfo.RE:
                text = "RE"
                table += table_colored_cell.format(color="gold", text=text)
            elif result.err_stat == ResultInfo.TLE:
                text = "TLE"
                table += table_colored_cell.format(color="gold", text=text)
            else: assert 0, "error in MakeHTML function."
            table += table_cell.format(text=str(round(result.time, 3)))
            table_body.append(table_line.format(text=table))
        table_all = "<h2>Table</h2>"
        table_all += table_heading.format(body="\n".join(table_body))
        
        now = datetime.datetime.now()
        now_str = now.strftime('%Y/%m/%d %H:%M:%S')
        body = '<h6>Creation date and time: {text}</h6>'.format(text=now_str)
        
        body += "<h2>Summary</h2>"
        body += self.make_summary()
        body += table_all

        result_file_name = "result.html"
        with open(result_file_name ,'w', encoding='utf-8', newline='\n') as html:
            text = html_text.format(body=body, title="Result")
            text = self.insert_text_into_html_head("<body>", text, css_link1)
            text = self.insert_text_into_html_head("<body>", text, css_link2)
            text = self.insert_text_into_html_head("<body>", text, script_link)
            html.writelines(text)

    def make_summary(self) -> str:
        """サマリ情報を作る"""
        file_name_list, scores_list = [], []
        for result in self.result_all:
            file_name_list.append(os.path.basename(result.name))
            scores_list.append(0 if result.score == "None" or result.err_stat != ResultInfo.AC else int(result.score))

        string = []
        string.append("Input file number: " + str(len(self.result_all)))
        string.append("Average Score: " + str(sum(scores_list)/len(self.result_all)))
        string.append("")
        string.append("Max Score: " + str(max(scores_list)))
        string.append("FileName: " + file_name_list[scores_list.index(max(scores_list))])
        string.append("")
        string.append("Minimum Score: " + str(min(scores_list)))
        string.append("FileName: " + file_name_list[scores_list.index(min(scores_list))])
        string.append("")
        return "<br>\n".join(string)
    
    def insert_text_into_html_head(self, tag: str, html_str: str, text: str) -> str:
        """HTMLの文字列のtagの中に別の文字列を挿入する"""
        html_str_list = html_str.split("\n")
        html_str_list.insert(html_str_list.index(tag) + 1, text)
        return "\n".join(html_str_list)
