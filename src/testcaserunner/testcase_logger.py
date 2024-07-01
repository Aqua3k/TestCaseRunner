import os
import shutil
from typing import List, Dict, Any, Tuple, Callable
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from collections import defaultdict
import warnings

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from .runner import RunnerSettings, ResultStatus, TestCase, TestCaseResult

class LogManager:
    @dataclass
    class Column:
        title: str
        getter: Callable[[int], str]

    js_file_path = "js"
    def __init__(self, settings: RunnerSettings):
        self.base_dir = os.path.split(__file__)[0]
        self.settings = settings
        loader = FileSystemLoader(os.path.join(self.base_dir, r"templates"))
        self.environment = Environment(loader=loader)

    def sortup_attributes(self) -> List[str]:
        attributes = dict() # setだと順番が保持されないのでdictにする
        for test_result in self.results:
            for attribute in test_result.attribute.keys():
                attributes[attribute] = ""
        return list(attributes.keys())
    
    def get_in(self, attribute: Any, row: int) -> str:
        template = self.environment.get_template("cell_with_file_link.j2")
        rel_path = os.path.relpath(self.testcases[row].input_file_path, self.settings.log_folder_name)
        data = {
            "link": rel_path,
            "value": "+",
            }
        return template.render(data)
    def get_stdout(self, attribute: Any, row: int) -> str:
        template = self.environment.get_template("cell_with_file_link.j2")
        rel_path = os.path.relpath(self.testcases[row].stdout_file_path, self.settings.log_folder_name)
        data = {
            "link": rel_path,
            "value": "+",
            }
        return template.render(data)
    def get_testcase_name(self, attribute: Any, row: int) -> str:
        template = self.environment.get_template("cell.j2")
        data = {
            "value": self.testcases[row].testcase_name,
            }
        return template.render(data)
    def get_stderr(self, attribute: Any, row: int) -> str:
        template = self.environment.get_template("cell_with_file_link.j2")
        rel_path = os.path.relpath(self.testcases[row].stderr_file_path, self.settings.log_folder_name)
        data = {
            "link": rel_path,
            "value": "+",
            }
        return template.render(data)
    status_texts = {
        ResultStatus.AC: ("AC", "lime"),
        ResultStatus.WA: ("WA", "gold"),
        ResultStatus.RE: ("RE", "gold"),
        ResultStatus.TLE: ("TLE", "gold"),
        ResultStatus.IE: ("IE", "red"),
    }
    def get_status(self, attribute: Any, row: int) -> str:
        status = self.results[row].error_status
        text, color = self.status_texts.get(status, ("IE", "red"))
        template = self.environment.get_template("cell_with_color.j2")
        data = {
            "color": color,
            "value": text,
            }
        return template.render(data)
    def get_other(self, _: Any, attribute: str, row: int) -> None:
        attributes = self.results[row].attribute
        if attribute not in attributes:
            value = "---"
        else:
            value = attributes[attribute]
            if type(value) is float:
                value = round(value, 3)
        template = self.environment.get_template("cell.j2")
        data = {
            "value": value,
            }
        return template.render(data)

    columns = [
        Column("in", get_in),
        Column("out", get_stdout),
        Column("stdout", get_stderr),
        Column("testcase", get_testcase_name),
        Column("status", get_status),
    ]
    def analyze_result(self, results: List[Tuple[TestCase, TestCaseResult]]) -> None:
        self.testcases: List[TestCase] = []
        self.results: List[TestCaseResult] = []
        for t, r in results:
            self.testcases.append(t)
            self.results.append(r)
        self.attributes = self.sortup_attributes()

    def make_result_log(self, results: List[Tuple[TestCase, TestCaseResult]]) -> None:
        self.analyze_result(results)
        self.make_json_file()
        self.make_html()
    
    histgram_fig_name = 'histgram.png'
    heatmap_fig_name = 'heatmap.png'
    def make_figure(self) -> str:
        # ヒストグラムを描画
        self.df.hist()
        plt.savefig(os.path.join(self.settings.fig_dir_path, self.histgram_fig_name))
        plt.close()

        # 相関係数のヒートマップ
        corr = self.df.corr(numeric_only=True)
        heatmap = sns.heatmap(corr, annot=True)
        heatmap.set_title('Correlation Coefficient Heatmap')
        plt.savefig(os.path.join(self.settings.fig_dir_path, self.heatmap_fig_name))
        
        ret = []
        template = self.environment.get_template("figure.j2")
        fig = template.render({"link": os.path.join("fig", self.histgram_fig_name)})
        ret.append(fig)
        fig = template.render({"link": os.path.join("fig", self.heatmap_fig_name)})
        ret.append(fig)
        return "".join(ret)

    html_file_name = "result.html"
    def make_html(self) -> None:
        for attribute in self.attributes:
            self.columns.append(self.Column(attribute, self.get_other))
        
        template = self.environment.get_template("main.j2")
        data = {
            "date": self.settings.datetime.strftime("%Y/%m/%d %H:%M:%S"),
            "summary": f"<pre>{self.df.describe()}</pre>",
            "script_list": self.make_script_list(),
            "figures": self.make_figure(),
            "css_list": self.make_css_list(),
            "table": self.make_table(),
            }
        html_file_path = os.path.join(self.settings.log_folder_name, self.html_file_name)
        with open(html_file_path, mode="w") as f:
            f.write(template.render(data))
    
    def make_table(self) -> Dict[str, str]:
        ret = []
        for row in range(len(self.results)):
            d = {}
            for column in self.columns:
                d[column.title] = column.getter(self, column.title, row)
            ret.append(d)
        return ret
    
    def make_script_list(self) -> List[str]:
        template = self.environment.get_template("script.j2")
        ret = [
            template.render({"link": r"js/Table.js"}),
        ]
        return ret
    
    def make_css_list(self) -> List[str]:
        template = self.environment.get_template("css.j2")
        ret = [
            template.render({"link": r"js/SortTable.css"}),
            template.render({"link": r"https://newcss.net/new.min.css"}),
        ]
        return ret

    def finalize(self) -> None:
        """html, csv, main, in, outファイルをコピーしてlog以下に保存する"""
        for file in self.settings.copy_target_files:
            file_path = Path(file)
            if file_path.is_file():
                shutil.copy(file, self.settings.log_folder_name)
            elif file_path.is_dir():
                warnings.warn(f"{file}はディレクトリパスです。コピーは行いません。")
            else:
                warnings.warn(f"{file}が見つかりません。コピーは行いません。")
        shutil.copytree(
            os.path.join(self.base_dir, self.js_file_path),
            os.path.join(self.settings.log_folder_name, self.js_file_path)
            )
    
    json_file_name = "result.json"
    def make_json_file(self) -> None:
        file_hash = ""
        file_names = ""
        contents = defaultdict(list)
        for testcase, result in zip(self.testcases, self.results):
            path = testcase.input_file_path
            file_names += file_names
            file_hash += self.calculate_file_hash(path)
            contents["input_file"].append(os.path.basename(testcase.input_file_path))
            contents["stdout_file"].append(os.path.basename(testcase.stdout_file_path))
            contents["stderr_file"].append(os.path.basename(testcase.stderr_file_path))
            contents["status"].append(self.status_texts[result.error_status][0])
            for key in self.attributes:
                value = result.attribute[key] if key in result.attribute else None
                contents[key].append(value)
        
        file_content_hash = self.calculate_string_hash(file_hash)
        file_name_hash = self.calculate_string_hash(file_names)
        
        json_file = {
            "created_date": self.settings.datetime.strftime("%Y/%m/%d %H:%M"),
            "testcase_num": len(self.testcases),
            "file_content_hash": file_content_hash,
            "file_name_hash": file_name_hash,
            "contents": contents,
        }
        self.df = pd.DataFrame(contents)
        json_file_path = os.path.join(self.settings.log_folder_name, self.json_file_name)
        with open(json_file_path, 'w') as f:
            json.dump(json_file, f, indent=2)

    def calculate_file_hash(self, file_path: str, hash_algorithm: str ='sha256') -> str:
        hash_obj = hashlib.new(hash_algorithm)
        with open(file_path, 'rb') as file:
            while chunk := file.read(4096):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def calculate_string_hash(self, input_string: str, hash_algorithm: str ='sha256') -> str:
        encoded_string = input_string.encode('utf-8')
        hash_obj = hashlib.new(hash_algorithm)
        hash_obj.update(encoded_string)
        return hash_obj.hexdigest()
