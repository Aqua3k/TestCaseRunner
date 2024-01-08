import glob
import os
from typing import List
import json
import shutil
import time

from flask import Flask, request
from flask_cors import CORS
import pandas as pd
from jinja2 import Environment, FileSystemLoader

log_dir = "log"
log_file = "result.json"
html_path = "result.html"
css_path = "https://newcss.net/new.min.css"

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
    
    def erase_log_folder(self):
        path = os.path.join(log_dir, self.foleder_name)
        shutil.rmtree(path)

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
    
    def erase_log(self, index: int):
        assert 0 <= index < len(self.logs)
        self.logs[index].erase_log_folder()
        self.logs.pop(index)
        
    def is_inputfiles_same(self, index_list: List[int]):
        s = set()
        for index in index_list:
            s.add(self.logs[index].get_hash())
        return len(s) == 1

    def get_merged_data_frame(self, index1: int, index2: int):
        if not self.is_inputfiles_same([index1, index2]):
            return
        merged_df = pd.merge(self.logs[index1].df, self.logs[index2].df, on='input_file')
        return merged_df
    
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
            d[""] = cell_template.render({"value": checkbox})
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

    def get_diff_html(self, checkbox_list):
        index1 = int(checkbox_list[0])
        index2 = int(checkbox_list[1])
        merged_df = log_manager.get_merged_data_frame(index1, index2)
        print(merged_df.to_html(index=False))
        table = merged_df.to_html(index=False)
        
        css_template = self.environment.get_template("css.j2")
        css = css_template.render({"link": css_path})
        
        template = self.environment.get_template("diff_main.j2")
        data = {
            "css_list": [css],
            "table": table,
        }
        contents = template.render(data)
        return merged_df.to_json()
        return contents

log_manager = LogViewer()

app = Flask(__name__)
CORS(app)

@app.route('/api/log_table', methods=['POST'])
def post_handler():
    assert request.is_json
    data = request.json
    ret = ""
    print("recieve request!")
    match data["type"]:
        case "0":
            print("update")
            ret = log_manager.make_html_contents()
        case "1":
            print("erase")
            erase_log(data["checkbox"])
        case "2":
            ret = log_manager.get_diff_html(data["checkbox"])
            print("diff")
        case _:
            assert 0

    return ret

def erase_log(checkbox_list):
    for index in checkbox_list:
        print(index)
        log_manager.erase_log(int(index))
    time.sleep(0.5)

if __name__ == '__main__':
    app.run(debug=True)
