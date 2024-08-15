import os
import json
import glob
from typing import Any
from copy import deepcopy
from dataclasses import dataclass, field
import datetime

from jinja2 import Environment, FileSystemLoader
import pandas as pd
import numpy as np
from jsonschema import ValidationError

from .runner_defines import RunnerMetadata, ResultStatus
from .logger import RunnerLogger
from .testcase_logger import RunnerLog, RunnerLogManager
from .html_builder import HtmlBuilder, Column, HtmlColumnType

@dataclass
class DiffColumn(Column):
    has_sub_category: bool
    sub_category_num: int
    has_sort_button: bool
    use_hash: bool = False
    hash_column: str = ""
    sub_categories: list[str] = field(default_factory=list)

class DiffHtmlBuilder(HtmlBuilder):
    logger = RunnerLogger("DiffHtmlBuilder")
    #TODO repeat_countを考慮しないとうまくいかなそう…
    def __init__(self, output_html_path: str, logs: list[RunnerLog], debug: bool) -> None:
        loader = FileSystemLoader(os.path.join(os.path.split(__file__)[0], r"templates"))
        self.environment = Environment(loader=loader)
        self.output_html_path = output_html_path
        self.logs = logs
        self.renamed_logs = deepcopy(self.logs)
        if debug:
            self.logger.enable_debug_mode()
        self.columns = self.construct_table_columns()
        self.merged_df = self.merge_data_frames()
        self.contents: list[str] = []
        self.title = ""
    
    def get_data(self, column: str, row: int, sub_category_index: int):
        # 欠損値の場合は空文字にする
        col = (column, sub_category_index)
        if col not in self.merged_df.columns:
            return "" # 列がないならNoneを返す
        ret = self.merged_df.at[row, col]
        if ret is None:
            ret = ""
        if type(ret) is np.float64 or type(ret) is np.float32:
            ret = round(ret, 3)
        return ret
        
    def construct_table_columns(self):
        columns = [
            DiffColumn("testcase", HtmlColumnType.TEXT, False, len(self.logs), True),
            DiffColumn("in", HtmlColumnType.URL, False, len(self.logs), False),
            DiffColumn("stdout", HtmlColumnType.URL, True, len(self.logs), False, True, "stdout_hash"),
            DiffColumn("stderr", HtmlColumnType.URL, True, len(self.logs), False, True, "stderr_hash"),
            DiffColumn("status", HtmlColumnType.STATUS, True, len(self.logs), False),
        ]
        attributes = {}
        for log in self.logs:
            for attribute in log.metadata["attributes"]:
                attributes[attribute] = ""
        for attribute in attributes.keys():
            columns.append(DiffColumn(attribute, HtmlColumnType.TEXT, True, len(self.logs), True))
        
        for column in columns:
            for i in range(len(self.logs)):
                if column.has_sub_category:
                    column.sub_categories.append(f"{column.title}.{i+1}")
        return columns
    
    def merge_data_frames(self):
        attributes = {}
        for i, log in enumerate(self.renamed_logs):
            rename_list = {}
            for column in log.df.columns:
                attributes[column] = ""
                if column != "input_hash":
                    rename_list[column] = (column, i)
            log._df = log.df.rename(columns=rename_list)

        # DataFrameをマージ
        merged_df = self.renamed_logs[0].df
        for log in self.renamed_logs[1:]:
            merged_df = pd.merge(merged_df, log.df, on=RunnerLogManager.input_hash_col)
        return merged_df

    def set_title(self, title: str) -> None:
        self.title = title

    @logger.function_tracer
    def add_heading(self, text: str) -> None:
        template = self.environment.get_template("heading.j2")
        self.contents.append(template.render({"text": text}))

    def add_figure(self, figure_path: str) -> None:
        pass

    def add_summary(self) -> None:
        pass

    def add_table(self) -> None:
        template = self.environment.get_template("diff_table.j2")
        data = {
            "columns": self.columns,
            "table": self.make_table_contents(),
        }
        self.contents.append(template.render(data))

    @logger.function_tracer
    def make_table_contents(self) -> list[list[str]]:
        def make_cell_tata(column: DiffColumn, row: int, sub_category_index: int) -> str:
            match column.type:
                case HtmlColumnType.URL:
                    return self.get_url_cell(column, row, sub_category_index)
                case HtmlColumnType.STATUS:
                    return self.get_status_cell(column, row, sub_category_index)
                case HtmlColumnType.TEXT:
                    return self.get_text_cell(column, row, sub_category_index)
                case _:
                    raise ValueError("error: 不明なHtmlColumnTypeがあります。")

        table = []
        for row in range(len(self.merged_df)):
            rows = []
            for column in self.columns:
                if column.has_sub_category:
                    for sub_category_index in range(len(column.sub_categories)):
                        ret = make_cell_tata(column, row, sub_category_index)
                        rows.append(ret)
                else:
                    ret = make_cell_tata(column, row, 0)
                    rows.append(ret)

            table.append(rows)
        return table
    
    status_texts = {
        ResultStatus.AC: ("AC", "lime"),
        ResultStatus.WA: ("WA", "gold"),
        ResultStatus.RE: ("RE", "gold"),
        ResultStatus.TLE: ("TLE", "gold"),
        ResultStatus.IE: ("IE", "red"),
    }
    @logger.function_tracer
    def get_status_cell(self, column: DiffColumn, row: int, sub_category_index: int) -> str:
        value = self.get_data(column.title, row, sub_category_index)
        text, color = self.status_texts.get(value, ("IE", "red"))
        template = self.environment.get_template("cell_with_color.j2")
        data = {
            "color": color,
            "value": text,
            }
        return template.render(data)

    @logger.function_tracer
    def add_script(self, script_path: str) -> None:
        template = self.environment.get_template("script.j2")
        file = os.path.join(os.path.split(__file__)[0], script_path)
        self.contents.append(template.render({"text": self.load_file(file)}))

    @logger.function_tracer
    def add_css(self, css_path: str) -> None:
        template = self.environment.get_template("css.j2")
        file = os.path.join(os.path.split(__file__)[0], css_path)
        self.contents.append(template.render({"text": self.load_file(file)}))

    @logger.function_tracer
    def add_css_link(self, css_path: str) -> None:
        template = self.environment.get_template("css_link.j2")
        self.contents.append(template.render({"link": css_path}))
    
    @logger.function_tracer
    def write(self) -> None:
        template = self.environment.get_template("main.j2")
        data = {
            "title": self.title,
            "sections": self.contents,
        }
        with open(self.output_html_path, mode="w") as f:
            f.write(template.render(data))

    @logger.function_tracer
    def load_file(self, file: str) -> str:
        with open(file, mode="r", encoding="utf-8") as f:
            text = f.read()
        return text

    def get_text_cell_normal(self, value: Any):
        template = self.environment.get_template("cell.j2")
        return template.render({"value": value})

    @logger.function_tracer
    def get_text_cell(self, column: DiffColumn, row: int, sub_category_index: int) -> str:
        this, others = self.get_cell_data(column, row, sub_category_index)
        if len( set([this]) | (set(others)) ) == 1:
            return self.get_text_cell_normal(this)

        template = self.environment.get_template("cell_with_color.j2")
        data = {
            "color": self.get_color(this, others),
            "value": this,
            }
        return template.render(data)

    def get_url_cell_normal(self, value: Any) -> str:
        template = self.environment.get_template("cell_with_file_link.j2")
        data = {
            "link": value,
            "value": "+",
            }
        return template.render(data)

    @logger.function_tracer
    def get_url_cell(self, column: DiffColumn, row: int, sub_category_index: int) -> str:
        if not column.hash_column:
            return self.get_url_cell_normal(self.get_data(column.title, row, sub_category_index))

        this, others = self.get_cell_hash_data(column, row, sub_category_index)
        if len( set([this]) | (set(others)) ) == 1:
            return self.get_url_cell_normal(self.get_data(column.title, row, sub_category_index))
        
        template = self.environment.get_template("cell_with_file_link_and_color.j2")
        data = {
            "link": self.get_data(column.title, row, sub_category_index),
            "value": "+",
            "color": "Gold",
        }
        return template.render(data)

    def get_cell_data(self, column: DiffColumn, row: int, sub_category_index: int):
        if not column.has_sub_category:
            return self.get_data(column.title, row, sub_category_index), []

        this = None
        others = []
        for i in range(len(self.renamed_logs)):
            if i == sub_category_index:
                this = self.get_data(column.title, row, sub_category_index)
            else:
                others.append(self.get_data(column.title, row, i))

        assert this is not None
        assert len(others) == len(self.renamed_logs) - 1

        return this, others

    def get_cell_hash_data(self, column: DiffColumn, row: int, sub_category_index: int):
        this = None
        others = []
        for i in range(len(self.renamed_logs)):
            if i == sub_category_index:
                this = self.get_data(column.hash_column, row, sub_category_index)
            else:
                others.append(self.get_data(column.hash_column, row, sub_category_index))

        assert this is not None
        assert len(others) == len(self.renamed_logs) - 1

        return this, others

    @logger.function_tracer
    def get_color(self, this: Any, others: list[Any]) -> str:
        # NOTE: 暫定で最小値と最大値だけを見る
        try:
            if this <= min(others):
                return "Cyan"
            elif max(others) <= this:
                return "Hotpink"
            else:
                return "Gold"
        except:
            pass
        return "Gold"

    def add_datetime(self) -> None:
        template = self.environment.get_template("datetime.j2")
        data = {
            "date" : datetime.datetime.now().strftime("%Y/%m/%d %H:%M"),
        }
        self.contents.append(template.render(data))

    @logger.function_tracer
    def add_other_file_summary(self, index: int) -> None:
        self.contents.append(f"<pre>{self.logs[index].df.describe()}</pre>")

    @logger.function_tracer
    def add_link(self, index: int) -> None:
        template = self.environment.get_template("link.j2")
        data = {
            "link" : os.path.join("..", self.logs[index].base_dir, "result.html"),
            "text": "view details",
        }
        self.contents.append(template.render(data))

class DiffDirector:
    def __init__(self, builder: DiffHtmlBuilder):
        self.__builder = builder

    def construct(self):
        self.__builder.set_title("Compare Result")
        self.__builder.add_datetime()
        self.__builder.add_heading("Summary 1")
        self.__builder.add_link(0)
        self.__builder.add_other_file_summary(0)
        self.__builder.add_heading("Summary 2")
        self.__builder.add_link(1)
        self.__builder.add_other_file_summary(1)
        self.__builder.add_heading("Compare Table")
        self.__builder.add_table()
        self.__builder.add_script("js/Table.js")
        self.__builder.add_script("js/checkbox.js")
        self.__builder.add_css("js/SortTable.css")
        self.__builder.add_css_link(r"https://newcss.net/new.min.css")
        self.__builder.write()

class RunnerLogViewer:
    logger = RunnerLogger("RunnerLogViewer")
    def __init__(self, path: str="log", _debug=False) -> None:
        self.debug = _debug
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
            #validate(instance=data, schema=schema)
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

        folder = os.path.split(file)[0]
        self.logs.append(RunnerLog(contents, metadata, os.path.split(folder)[1]))
        self.logger.info(f"{file} を読み込みました。")
    
    @logger.function_tracer
    def get_logs(self) -> list[RunnerLog]:
        return self.logs

    def get_log_file_path(self) -> str:
        log_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_COMPARE"
        path = os.path.join("log", log_name)
        os.makedirs(path, exist_ok=True)
        return path

    @logger.function_tracer
    def compare(self, log1: RunnerLog, log2: RunnerLog) -> None:
        folder = self.get_log_file_path()
        builder = DiffHtmlBuilder(os.path.join(folder, "result.html"), [log1, log2], self.debug)
        director = DiffDirector(builder)
        director.construct()
