import os
import json
import glob
from typing import Type
import re

import pandas as pd
import numpy as np

from .logging_config import setup_logger
from .testcase_logger import RunnerLog, HtmlParser, LIB_NAME

class RunnerLogDiff(RunnerLog):
    def __init__(self, contents: dict, metadata: dict):
        super().__init__(contents, metadata)

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
