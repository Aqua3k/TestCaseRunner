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
import numpy as np

from .runner import RunnerSettings, ResultStatus, TestCase, TestCaseResult
from .logging_config import setup_logger

class HtmlColumnType(IntEnum):
    """HTMLファイルのcolumnの情報
    """
    URL = auto()
    STATUS = auto()
    TEXT = auto()

class RunnerLog:
    def __init__(self, contents: dict, metadata: dict):
        self.df = pd.DataFrame(contents)
        self.metadata = metadata

class LogManager:
    js_file_path = "js"
    infile_col = "in"
    stdout_col = "stdout"
    stderr_col = "stderr"
    infilename_col = "testcase"
    status_col = "status"
    def __init__(self, results: List[Tuple[TestCase, TestCaseResult]], settings: RunnerSettings):
        self.settings = settings
        self.logger = setup_logger("LogManager", self.settings.debug)
        self.results = results
        self.attributes = {
            self.infile_col: HtmlColumnType.URL,
            self.stdout_col: HtmlColumnType.URL,
            self.stderr_col: HtmlColumnType.URL,
            self.infilename_col: HtmlColumnType.TEXT,
            self.status_col: HtmlColumnType.STATUS,
        }
        self.make_json_file()
        self.make_figure()
        self.base_dir = os.path.split(__file__)[0]
    
    def get_log(self) -> RunnerLog:
        return self.runner_log

    def make_html(self):
        self.html_parser = HtmlParser(self.runner_log, self.settings.log_folder_name, self.settings.debug)
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
    def add_attribute(self, key, type):
        self.attributes[key] = type

    histgram_fig_name = 'histgram.png'
    heatmap_fig_name = 'heatmap.png'
    def make_figure(self):
        # ヒストグラムを描画
        self.runner_log.df.hist()
        plt.savefig(os.path.join(self.settings.fig_dir_path, self.histgram_fig_name))
        plt.close()

        # 相関係数のヒートマップ
        corr = self.runner_log.df.corr(numeric_only=True)
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
            self.add_attribute(key, HtmlColumnType.TEXT)

        file_hashes = []
        contents = defaultdict(list)
        for testcase, result in zip(testcases, results):
            path = testcase.input_file_path
            file_hashes.append(self.calculate_file_hash(path))
            contents[self.infile_col].append(os.path.relpath(testcase.input_file_path, self.settings.log_folder_name))
            contents[self.stdout_col].append(os.path.relpath(testcase.stdout_file_path, self.settings.log_folder_name))
            contents[self.stderr_col].append(os.path.relpath(testcase.stderr_file_path, self.settings.log_folder_name))
            contents[self.infilename_col].append(os.path.basename(testcase.input_file_path))
            contents[self.status_col].append(result.error_status)
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
        self.runner_log = RunnerLog(contents, metadata)
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
    def __init__(self, runner_log: RunnerLog, output_path: str, debug: bool):
        self.debug = debug
        self.runner_log = runner_log
        self.output_path = output_path
        self.logger = setup_logger("HtmlParser", self.debug)
        self.base_dir = os.path.split(__file__)[0]
        loader = FileSystemLoader(os.path.join(self.base_dir, r"templates"))
        self.environment = Environment(loader=loader)

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
            "date": self.runner_log.metadata["created_date"],
            "summary": f"<pre>{self.runner_log.df.describe()}</pre>",
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
        for row in range(self.runner_log.metadata["testcase_num"]):
            rows = {}
            for column in self.runner_log.df.columns:
                value = self.runner_log.df.at[row, column]
                match self.runner_log.metadata["attributes"][column]:
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
                    case HtmlColumnType.TEXT:
                        if type(value) is np.float64 or type(value) is np.float32:
                            value = round(value, 3)
                        template = self.environment.get_template("cell.j2")
                        data = {
                            "value": value,
                            }
                        value = template.render(data)
                rows[column] = value
            ret.append(rows)
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
