import os
import json
import glob
from typing import Any, Optional, Match
import re

import pandas as pd
import numpy as np
from jsonschema import validate, ValidationError

from .runner_defines import RunnerMetadata
from .runner_logger import RunnerLogger
from .testcase_logger import RunnerLog, RunnerLogManager
from .html_parser import HtmlParser

class DiffHtmlParser(HtmlParser):
    logger = RunnerLogger("DiffHtmlParser")
    def __init__(self, runner_log: RunnerLog, output_path: str, debug: bool) -> None:
        super().__init__(runner_log, output_path, debug)
    
    column_pattern = r'^([a-zA-Z0-9]+)\.([12])$'
    @logger.function_tracer
    def get_match(self, column: str) -> Optional[Match]:
        return re.match(self.column_pattern, column)

    @logger.function_tracer
    def is_diff_column(self, column: str) -> bool:
        return bool(self.get_match(column))
    
    extensions = ["1", "2"]
    @logger.function_tracer
    def get_diff_data(self, column: str, row: int) -> tuple[Any, Any]:
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

    @logger.function_tracer
    def get_color(self, this: Any, other: Any) -> str:
        if type(this) is str or type(other) is str:
            return "Gold"
        else:
            if this < other:
                return "Cyan"
            else:
                return "Hotpink"

    @logger.function_tracer
    def get_text_cell(self, column: str, row: int) -> str:
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
    logger = RunnerLogger("RunnerLogViewer")
    merged_data_suffixes = (".1", ".2")
    def __init__(self, path: str="log", _debug=False) -> None:
        if _debug:
            self.logger.enable_debug_mode()
        self.logs: list[RunnerLog] = []
        pattern = os.path.join(path, "**", "*.json")
        for file in glob.glob(pattern, recursive=True):
            self.load_log(file)
    
    @logger.function_tracer
    def is_valid(self, data: dict) -> bool:
        try:
            schema_path = os.path.join(os.path.split(__file__)[0], "schemas", "result_schema.json")
            with open(schema_path, 'r') as f:
                schema: dict = json.load(f)
            validate(instance=data, schema=schema)
        except ValidationError as e:
            self.logger.info("json schema validation error.")
            return

        metadata: dict|None = data.get("metadata")
        libname = metadata.get("library_name")
        if libname != RunnerMetadata.LIB_NAME:
            return False # ライブラリ名が入っていなかったらFalse

        return True

    @logger.function_tracer
    def load_log(self, file: str) -> None:
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
        assert contents is not None, "contentsがNoneだよ"
        assert type(contents) is dict, "contentsがdict型ではないよ"
        assert metadata is not None, "metadataがNoneだよ"
        assert type(metadata) is dict, "metadataがNonedict型ではないよ"

        self.logs.append(RunnerLog(contents, metadata))
        self.logger.info(f"{file} を読み込みました。")
    
    @logger.function_tracer
    def get_logs(self) -> list[RunnerLog]:
        return self.logs

    @logger.function_tracer
    def test_diff(self, log1: RunnerLog, log2: RunnerLog) -> None:
        # 不要な列を削除する
        log2.drop(RunnerLogManager.infilename_col)
        
        # 属性名を置換する
        attributes1 = log1.metadata["attributes"]
        att1: dict[Any, Any] = {}
        for k, v in attributes1.items():
            if k != RunnerLogManager.input_hash_col and k != RunnerLogManager.infilename_col:
                att1[f"{k}.1"] = v
            else:
                att1[k] = v
        
        attributes2 = log2.metadata["attributes"]
        att2: dict[Any, Any] = {}
        for k, v in attributes2.items():
            if k != RunnerLogManager.input_hash_col and k != RunnerLogManager.infilename_col:
                att1[f"{k}.2"] = v
            else:
                att1[k] = v

        # attributeを合成
        attributes = {**att1, **att2}
        metadata = log1.metadata
        metadata["attributes"] = attributes

        # DataFrameをマージ
        merged_df = pd.merge(log1.df, log2.df, on=RunnerLogManager.input_hash_col, suffixes=self.merged_data_suffixes)

        runner_log = RunnerLog(json.loads(merged_df.to_json()), metadata)

        parser = DiffHtmlParser(runner_log, ".", False) # TODO 要調整 リンクが切れたりする
        parser.make_html()
