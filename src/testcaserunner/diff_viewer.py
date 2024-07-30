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
from .runner import RunnerLog, RunnerLogManager
from .html_builder import ResultHtmlBuilder, HtmlBuilder

class DiffHtmlBuilder(ResultHtmlBuilder):
    logger = RunnerLogger("DiffHtmlTableSection")
    extensions = ["1", "2"]
    def __init__(self, output_html_path: str, log: RunnerLog, debug: bool):
        super().__init__(output_html_path, log, debug)

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
    
    @logger.function_tracer
    def get_url_cell(self, column: str, row: int) -> str:
        match = self.get_match(column)
        if match:
            original_column = match.group(1)
            extension = match.group(2)
        else:
            assert 0, "ここにくるはずないんだけど"
        
        match original_column:
            case RunnerLogManager.infile_col:
                return super().get_url_cell(column, row)
            case RunnerLogManager.stdout_col:
                col = RunnerLogManager.stdout_hash_col
            case RunnerLogManager.stderr_col:
                col = RunnerLogManager.stdout_hash_col
            case _:
                assert 0, "ここにくるはずないんだけど"
        col = f"{col}.{extension}"
        this, other = self.get_diff_data(col, row)
        if this == other:
            return super().get_url_cell(column, row)
        
        template = self.environment.get_template("cell_with_file_link_and_color.j2")
        data = {
            "link": self.get_data(column, row),
            "value": "+",
            "color": "Gold",
        }
        return template.render(data)

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
    def is_diff_column(self, column: str) -> bool:
        return bool(self.get_match(column))

    column_pattern = r'^([a-zA-Z0-9_]+)\.([12])$'
    @logger.function_tracer
    def get_match(self, column: str) -> Optional[Match]:
        return re.match(self.column_pattern, column)

    @logger.function_tracer
    def get_diff_data(self, column: str, row: int) -> tuple[Any, Any]:
        match = self.get_match(column)
        if match:
            original_column = match.group(1)
            extension = match.group(2)
            this = self.get_data(column, row)
            idx = self.extensions.index(extension)
            other_column = f"{original_column}.{self.extensions[idx^1]}"
            other = self.get_data(other_column, row)
        else:
            assert 0, "ここにくるはずないんだけど…"
        return this, other

class DiffDirector:
    def __init__(self, builder: HtmlBuilder):
        self.__builder = builder

    def construct(self):
        self.__builder.add_summary()
        self.__builder.add_figure('histgram.png')
        self.__builder.add_figure('heatmap.png')
        self.__builder.add_table()
        self.__builder.add_script("js/Table.js")
        self.__builder.add_script("js/checkbox.js")
        self.__builder.add_css("js/SortTable.css")
        self.__builder.add_css_link(r"https://newcss.net/new.min.css")
        self.__builder.write()

def make_html(path: str, log: RunnerLog, debug: bool) -> None:
    builder = DiffHtmlBuilder(path, log, debug)
    director = DiffDirector(builder)
    director.construct()

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
            return False

        metadata: dict|None = data.get("metadata")
        assert metadata is not None, "metadataがNoneだよ"
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
        make_html("result.html", runner_log, True)
