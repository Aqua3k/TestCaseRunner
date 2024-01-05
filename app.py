import glob
import os
from typing import List
import json

from flask import Flask
from flask_cors import CORS
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from testcase_runner.testcase_runner import ResultStatus

log_dir = "log"
log_file = "result.json"
html_path = "result.html"

class Log():
    def __init__(self, path):
        with open(path, 'r') as file:
            json_data = json.load(file)
        tmp = os.path.split(path)[0]
        self.html_path = os.path.join(tmp, html_path)
        self.foleder_name = os.path.basename(tmp)
        self.created_date = json_data["created_date"]
        contents = json_data["contents"]
        self.testcase_num = json_data["testcase_num"]
        self.file_content_hash = json_data["file_content_hash"]
        self.file_name_hash = json_data["file_name_hash"]
        self.has_score = json_data["has_score"]
        self.average_score = json_data["average_score"]
        self.__df = pd.DataFrame(contents)
    
    @property
    def df(self):
        return self.__df
    
    def get_hash(self):
        return (self.testcase_num, self.file_content_hash, self.file_name_hash)

class LogViewer():
    def __init__(self):
        loader = FileSystemLoader(r"testcase_runner\templates")
        self.environment = Environment(loader=loader)

        def is_log_dir(path: str)->bool:
            path = os.path.join(path, log_file)
            return os.path.isfile(path)

        self.logs: List[Log] = []
        for dir in glob.glob(os.path.join(log_dir, "*")):
            if is_log_dir(dir):
                path = os.path.join(dir, log_file)
                log = Log(path)
                self.logs.append(log)
        
    def is_inputfiles_same(self, index_list: List[int]):
        s = set()
        for index in index_list:
            s.add(self.logs[index].get_hash())
        return len(s) == 1

    def show_two_data(self, index1: int, index2: int):
        if not self.is_inputfiles_same([index1, index2]):
            return
        merged_df = pd.merge(self.logs[index1].df, self.logs[index2].df, on='input_file')
        print(merged_df)
    
    def get_data_frame(self, index: int):
        return self.logs[index].df
    
    def make_html_contents(self):
        template = self.environment.get_template("log_viewer_main.j2")  # ファイル名を指定
        data = {
            "table": self.make_table(),
            }
        return template.render(data)

    def make_table(self):
        ret = []
        checkbox_template = self.environment.get_template("checkbox.j2")
        cell_template = self.environment.get_template("cell.j2")
        cell_with_link_template = self.environment.get_template("cell_with_file_link.j2")
        for i, log in enumerate(self.logs):
            d = {}
            checkbox = checkbox_template.render({"name": i})
            d["select"] = cell_template.render({"value": checkbox})
            d["created date"] = cell_template.render({"value": log.created_date})
            data = {
                "link": log.html_path,
                "value": log.foleder_name,
            }
            d["folder name"] = cell_with_link_template.render(data)
            if log.has_score:
                score = log.average_score
            else:
                score = "None"
            d["average score"] = cell_template.render({"value": score})
            ret.append(d)
        return ret

log_manager = LogViewer()

app = Flask(__name__)
CORS(app)

@app.route('/api/log_table', methods=['GET'])  # /data エンドポイントに対するGETリクエストを処理
def get_data():
    # レスポンスの内容を返す
    return log_manager.make_html_contents()

if __name__ == '__main__':
    app.run(debug=True)  # デバッグモードでFlaskアプリケーションを実行
