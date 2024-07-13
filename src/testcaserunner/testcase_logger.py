import os
import shutil
from typing import List, Dict, Tuple
from pathlib import Path
import hashlib
import json
from enum import IntEnum, auto
from collections import defaultdict

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from jinja2 import Environment, FileSystemLoader

from .runner import RunnerSettings, ResultStatus, TestCase, TestCaseResult
from .logging_config import setup_logger

class HtmlColumnType(IntEnum):
    """HTMLファイルのcolumnの情報
    """
    URL = auto()
    STATUS = auto()
    TEXT = auto()
    USER = auto()

class LogManager:
    js_file_path = "js"
    def __init__(self, results: List[Tuple[TestCase, TestCaseResult]], settings: RunnerSettings):
        self.settings = settings
        self.logger = setup_logger("LogManager", self.settings.debug)
        self.results = results
        self.attributes = {
            "input_file": HtmlColumnType.URL,
            "stdout_file": HtmlColumnType.URL,
            "stderr_file": HtmlColumnType.URL,
            "testcase_name": HtmlColumnType.TEXT,
            "status": HtmlColumnType.STATUS,
        }
        self.make_json_file()
        self.make_figure()
        self.base_dir = os.path.split(__file__)[0]

    def make_html(self):
        self.html_parser = HtmlParser(self.json_file, self.settings.log_folder_name, self.settings.debug)
        self.html_parser.make_html()

    def finalize(self) -> None:
        """ファイルをコピーしてlog以下に保存する"""
        self.logger.debug("function finalize() started")
        for file in self.settings.copy_target_files:
            file_path = Path(file)
            if file_path.is_file():
                shutil.copy(file, self.settings.log_folder_name)
            elif file_path.is_dir():
                self.logger.warning(f"{file}はディレクトリパスです。コピーは行いません。")
            else:
                self.logger.warning(f"{file}が見つかりません。コピーは行いません。")
        shutil.copytree(
            os.path.join(self.base_dir, self.js_file_path),
            os.path.join(self.settings.log_folder_name, self.js_file_path)
            )
        self.logger.debug("function finalize() finished")

    json_file_name = "result.json"
    status_texts = {
        ResultStatus.AC: ("AC", "lime"),
        ResultStatus.WA: ("WA", "gold"),
        ResultStatus.RE: ("RE", "gold"),
        ResultStatus.TLE: ("TLE", "gold"),
        ResultStatus.IE: ("IE", "red"),
    }

    def add_attribute(self, key, type):
        self.attributes[key] = type

    histgram_fig_name = 'histgram.png'
    heatmap_fig_name = 'heatmap.png'
    def make_figure(self):
        # ヒストグラムを描画
        self.df.hist()
        plt.savefig(os.path.join(self.settings.fig_dir_path, self.histgram_fig_name))
        plt.close()

        # 相関係数のヒートマップ
        corr = self.df.corr(numeric_only=True)
        heatmap = sns.heatmap(corr, annot=True)
        heatmap.set_title('Correlation Coefficient Heatmap')
        plt.savefig(os.path.join(self.settings.fig_dir_path, self.heatmap_fig_name))

    def make_json_file(self) -> None:
        self.logger.debug("function make_json_file() started")

        testcases: List[TestCase] = []
        results: List[TestCaseResult] = []
        for t, r in self.results:
            testcases.append(t)
            results.append(r)

        attributes = dict() # setだと順番が保持されないのでdictにする
        for test_result in results:
            for attribute in test_result.attribute.keys():
                attributes[attribute] = ""
        user_attributes = list(attributes.keys())

        for key in user_attributes:
            self.add_attribute(key, HtmlColumnType.USER)

        file_hashes = []
        contents = defaultdict(list)
        for testcase, result in zip(testcases, results):
            path = testcase.input_file_path
            file_hashes.append(self.calculate_file_hash(path))
            contents["input_file"].append(os.path.relpath(testcase.input_file_path, self.settings.log_folder_name))
            contents["stdout_file"].append(os.path.relpath(testcase.stdout_file_path, self.settings.log_folder_name))
            contents["stderr_file"].append(os.path.relpath(testcase.stderr_file_path, self.settings.log_folder_name))
            contents["testcase_name"].append(os.path.basename(testcase.input_file_path))
            contents["status"].append(self.status_texts[result.error_status][0])
            for key in user_attributes:
                value = result.attribute[key] if key in result.attribute else None
                contents[key].append(value)
        
        metadata = {
            "created_date": self.settings.datetime.strftime("%Y/%m/%d %H:%M"),
            "testcase_num": len(testcases),
            "file_content_hash": file_hashes,
            "attributes": self.attributes,
        }
        self.json_file = {
            "contents": contents,
            "metadata": metadata,
        }
        self.df = pd.DataFrame(contents)
        json_file_path = os.path.join(self.settings.log_folder_name, self.json_file_name)
        with open(json_file_path, 'w') as f:
            json.dump(self.json_file, f, indent=2)
        self.logger.debug("function make_json_file() finished")

    def calculate_file_hash(self, file_path: str, hash_algorithm: str ='sha256') -> str:
        hash_obj = hashlib.new(hash_algorithm)
        with open(file_path, 'rb') as file:
            while chunk := file.read(4096):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

class HtmlParser:
    def __init__(self, jsonfile: dict, output_path: str, debug: bool):
        self.debug = debug
        self.output_path = output_path
        self.logger = setup_logger("HtmlParser", self.debug)
        self.base_dir = os.path.split(__file__)[0]
        loader = FileSystemLoader(os.path.join(self.base_dir, r"templates"))
        self.environment = Environment(loader=loader)
        self.parse_data(jsonfile)
    
    def parse_data(self, jsonfile):
        self.contents: dict = jsonfile["contents"]
        self.df = pd.DataFrame(self.contents)
        self.metadata: dict = jsonfile["metadata"]

    status_texts = {
        ResultStatus.AC: ("AC", "lime"),
        ResultStatus.WA: ("WA", "gold"),
        ResultStatus.RE: ("RE", "gold"),
        ResultStatus.TLE: ("TLE", "gold"),
        ResultStatus.IE: ("IE", "red"),
    }
    
    histgram_fig_name = 'histgram.png'
    heatmap_fig_name = 'heatmap.png'
    def make_figure(self) -> str:
        self.logger.debug("function make_figure() started")
        ret = []
        template = self.environment.get_template("figure.j2")
        fig = template.render({"link": os.path.join("fig", self.histgram_fig_name)})
        ret.append(fig)
        fig = template.render({"link": os.path.join("fig", self.heatmap_fig_name)})
        ret.append(fig)
        self.logger.debug("function make_figure() finished")
        return "".join(ret)

    html_file_name = "result.html"
    def make_html(self) -> None:
        self.logger.debug("function make_html() started")
        
        template = self.environment.get_template("main.j2")
        data = {
            "date": self.metadata["created_date"],
            "summary": f"<pre>{self.df.describe()}</pre>",
            "script_list": self.make_script_list(),
            "figures": self.make_figure(),
            "css_list": self.make_css_list(),
            "table": self.make_table(),
            }
        html_file_path = os.path.join(self.output_path, self.html_file_name)
        with open(html_file_path, mode="w") as f:
            f.write(template.render(data))
        self.logger.debug("function make_html() finished")

    def make_table(self) -> Dict[str, str]:
        ret = []
        for row in range(self.metadata["testcase_num"]):
            d = {}
            for column in self.contents.keys():
                value = self.contents[column][row]
                match self.metadata["attributes"][column]:
                    case HtmlColumnType.URL:
                        template = self.environment.get_template("cell_with_file_link.j2")
                        data = {
                            "link": value,
                            "value": "+",
                            }
                        value = template.render(data)
                    case HtmlColumnType.STATUS:
                        text, color = self.status_texts.get(value, ("IE", "red"))
                        template = self.environment.get_template("cell_with_color.j2")
                        data = {
                            "color": color,
                            "value": text,
                            }
                        value = template.render(data)
                    case HtmlColumnType.TEXT|HtmlColumnType.USER:
                        if type(value) is float:
                            value = round(value, 3)
                        template = self.environment.get_template("cell.j2")
                        data = {
                            "value": value,
                            }
                        value = template.render(data)
                d[column] = value
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
