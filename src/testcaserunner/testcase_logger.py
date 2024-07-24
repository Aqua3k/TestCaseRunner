import os
import shutil
from pathlib import Path
import hashlib
import json
from enum import IntEnum, auto
from collections import defaultdict
import glob
from typing import Type
import re

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
    METADATA = auto()

class RunnerLog:
    def __init__(self, contents: dict, metadata: dict):
        self._df = pd.DataFrame(contents)
        self._metadata = metadata
    
    @property
    def df(self) -> pd.DataFrame:
        return self._df

    @property
    def metadata(self):
        return self._metadata
    
    def drop(self, column: str):
        self._df = self._df.drop(columns=[column], errors='ignore')
        self._metadata["attributes"].pop(column, None)
    
    def _df_at(self, column, row):
        return self._df.at[str(row), column]

class RunnerLogDiff(RunnerLog):
    def __init__(self, contents: dict, metadata: dict):
        super().__init__(contents, metadata)

LIB_NAME = "testcaserunner"
class RunnerLogManager:
    js_file_path = "js"
    infile_col = "in"
    stdout_col = "stdout"
    stderr_col = "stderr"
    infilename_col = "testcase"
    status_col = "status"
    hash_col = "hash"
    def __init__(self, results: list[tuple[TestCase, TestCaseResult]], settings: RunnerSettings):
        self.settings = settings
        self.logger = setup_logger("RunnerLogManager", self.settings.debug)
        self.results = results
        self.attributes = {
            self.infilename_col: HtmlColumnType.TEXT,
            self.hash_col: HtmlColumnType.METADATA,
            self.infile_col: HtmlColumnType.URL,
            self.stdout_col: HtmlColumnType.URL,
            self.stderr_col: HtmlColumnType.URL,
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

        testcases: list[TestCase] = []
        results: list[TestCaseResult] = []
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

        contents = defaultdict(list)
        for testcase, result in zip(testcases, results):
            path = testcase.input_file_path
            hash = self.calculate_file_hash(path)
            contents[self.infilename_col].append(os.path.basename(testcase.input_file_path))
            contents[self.hash_col].append(f"{os.path.basename(testcase.input_file_path)}.{hash}")
            contents[self.infile_col].append(os.path.relpath(testcase.input_file_path, self.settings.log_folder_name))
            contents[self.stdout_col].append(os.path.relpath(testcase.stdout_file_path, self.settings.log_folder_name))
            contents[self.stderr_col].append(os.path.relpath(testcase.stderr_file_path, self.settings.log_folder_name))
            contents[self.status_col].append(result.error_status)
            for key in user_attributes:
                value = result.attribute[key] if key in result.attribute else None
                contents[key].append(value)
        
        # jsonデータをそろえるため一度DataFrameにしてからjsonに直す
        contents = json.loads(pd.DataFrame(contents).to_json())
        
        metadata = {
            "library_name": LIB_NAME,
            "created_date": self.settings.datetime.strftime("%Y/%m/%d %H:%M"),
            "testcase_num": len(testcases),
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
    def __init__(self, runner_log: Type[RunnerLog], output_path: str, debug: bool):
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
    
    def get_url_cell(self, column, row):
        value = self.runner_log._df_at(column, row)
        template = self.environment.get_template("cell_with_file_link.j2")
        data = {
            "link": value,
            "value": "+",
            }
        return template.render(data)
    
    def get_status_cell(self, column, row):
        value = self.runner_log._df_at(column, row)
        text, color = self.status_texts.get(value, ("IE", "red"))
        template = self.environment.get_template("cell_with_color.j2")
        data = {
            "color": color,
            "value": text,
            }
        return template.render(data)
    
    def get_text_cell(self, column, row):
        value = self.runner_log._df_at(column, row)
        if type(value) is np.float64 or type(value) is np.float32:
            value = round(value, 3)
        template = self.environment.get_template("cell.j2")
        data = {
            "value": value,
            }
        return template.render(data)

    def make_table(self) -> dict[str, str]:
        ret = []
        for row in range(self.runner_log.metadata["testcase_num"]):
            rows = {}
            for column in self.runner_log.df.columns:
                match self.runner_log.metadata["attributes"][column]:
                    case HtmlColumnType.URL:
                        value = self.get_url_cell(column, row)
                    case HtmlColumnType.STATUS:
                        value = self.get_status_cell(column, row)
                    case HtmlColumnType.TEXT:
                        value = self.get_text_cell(column, row)
                    case HtmlColumnType.METADATA:
                        continue
                    case _:
                        assert "error: 不明なHtmlColumnTypeがあります。"
                rows[column] = value
            ret.append(rows)
        return ret
    
    def make_script_list(self) -> list[str]:
        template = self.environment.get_template("script.j2")
        ret = [
            template.render({"link": r"js/Table.js"}),
        ]
        return ret
    
    def make_css_list(self) -> list[str]:
        template = self.environment.get_template("css.j2")
        ret = [
            template.render({"link": r"js/SortTable.css"}),
            template.render({"link": r"https://newcss.net/new.min.css"}),
        ]
        return ret

class DiffHtmlParser(HtmlParser):
    def __init__(self, runner_log: Type[RunnerLog], output_path: str, debug: bool):
        super().__init__(runner_log, output_path, debug)
    
    column_pattern = r'^([a-zA-Z0-9]+)\.([12])$'
    def get_match(self, column):
        return re.match(self.column_pattern, column)

    def is_diff_column(self, column):
        return bool(self.get_match(column))
    
    extensions = ["1", "2"]
    def get_diff_data(self, column, row):
        match = self.get_match(column)
        if match:
            original_column = match.group(1)
            extension = match.group(2)
            this = self.runner_log._df_at(column, row)
            idx = self.extensions.index(extension)
            other_column = f"{original_column}.{self.extensions[idx^1]}"
            other = self.runner_log._df_at(other_column, row)
        else:
            assert 0, "ここにくるはずないんだけど…"
        return this, other

    def get_color(self, this, other):
        if type(this) is str or type(other) is str:
            return "Gold"
        else:
            if this < other:
                return "Cyan"
            else:
                return "Hotpink"

    def get_text_cell(self, column, row):
        # column名を確認して、両方のデータにあるやつなら差分を調べる
        if self.is_diff_column(column):
            this, other = self.get_diff_data(column, row)
            if this != other:
                if type(this) is np.float64 or type(this) is np.float32:
                    this = round(this, 3)
                template = self.environment.get_template("cell_with_color.j2")
                data = {
                    "color": self.get_color(this, other),
                    "value": this,
                    }
                return template.render(data)

        # それ以外は普通のデータを返す
        return super().get_text_cell(column, row)

class RunnerLogViewer:
    merged_data_suffixes = (".1", ".2")
    def __init__(self, path: str="log", _debug=False):
        self.logger = setup_logger("RunnerLogViewer", _debug)
        self.logs: list[RunnerLog] = []
        pattern = os.path.join(path, "**", "*.json")
        for file in glob.glob(pattern, recursive=True):
            self.load_log(file)
    
    def is_valid(self, data: dict):
        contents: dict|None = data.get("contents")
        metadata: dict|None = data.get("metadata")
        if contents is None or metadata is None:
            return False # データが取得できるか？

        libname = metadata.get("library_name")
        if libname != LIB_NAME:
            return False # ライブラリ名が入っていなかったらFalse

        return True

    def load_log(self, file: str):
        try:
            with open(file, 'r') as f:
                loaded_data: dict = json.load(f)
        except:
            # ロードできなければ処理しない
            self.logger.info(f"{file} のロードでエラーが起きました。")
            return
        
        if not self.is_valid(loaded_data):
            self.logger.info(f"{file} は正しいデータではありませんでした。")
            return
        
        contents = loaded_data.get("contents")
        metadata = loaded_data.get("metadata")
        self.logs.append(RunnerLog(contents, metadata))
        self.logger.info(f"{file} を読み込みました。")
    
    def get_logs(self):
        return self.logs

    default_columns = [
        "in",
        "stdout",
        "stderr",
        "testcase",
        "status",
        "hash",
    ]
    def test_diff(self, log1: RunnerLog, log2: RunnerLog):
        # 不要な列を削除する
        log2.drop("testcase")
        
        # 属性名を置換する
        attributes1 = log1.metadata["attributes"]
        att1 = {}
        for k, v in attributes1.items():
            if k != "hash" and k != "testcase":
                att1[f"{k}.1"] = v
            else:
                att1[k] = v
        
        attributes2 = log2.metadata["attributes"]
        att2 = {}
        for k, v in attributes2.items():
            if k != "hash" and k != "testcase":
                att1[f"{k}.2"] = v
            else:
                att1[k] = v

        # attributeを合成
        attributes = {**att1, **att2}
        metadata = log1.metadata
        metadata["attributes"] = attributes

        # DataFrameをマージ
        merged_df = pd.merge(log1.df, log2.df, on="hash", suffixes=self.merged_data_suffixes)

        runner_log = RunnerLog(json.loads(merged_df.to_json()), metadata)

        parser = DiffHtmlParser(runner_log, ".", False) # TODO 要調整 リンクが切れたりする
        parser.make_html()
