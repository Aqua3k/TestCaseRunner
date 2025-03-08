import os

from jinja2 import Environment, FileSystemLoader
import numpy as np
from typing import Any
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass

from ..debug import call_logger
from ..parallel_executor import RunnerLog
from ..defines import InternalError

class HtmlColumnType(Enum):
    """HTMLファイルのcolumnの情報
    """
    URL = auto()
    STATUS = auto()
    TEXT = auto()
    METADATA = auto()

@dataclass
class Column:
    title: str
    type: HtmlColumnType

class BaseHtmlBuilder(ABC): # pragma: no cover
    @abstractmethod
    def set_title(self, title: str) -> None:
        pass
    @abstractmethod
    def add_heading(self, text: str) -> None:
        pass
    @abstractmethod
    def add_figure(self, figure_path: str) -> None:
        pass
    @abstractmethod
    def add_summary(self) -> None:
        pass
    @abstractmethod
    def add_table(self) -> None:
        pass
    @abstractmethod
    def add_script(self, script_path: str) -> None:
        pass
    @abstractmethod
    def add_css(self, css_path: str) -> None:
        pass
    @abstractmethod
    def add_css_link(self, css_path: str) -> None:
        pass
    @abstractmethod
    def add_datetime(self) -> None:
        pass
    @abstractmethod
    def write(self) -> None:
        pass

class ResultHtmlBuilder(BaseHtmlBuilder):
    def __init__(self, output_html_path: str, log: RunnerLog) -> None:
        loader = FileSystemLoader(os.path.join(os.path.split(__file__)[0], r"templates"))
        self.environment = Environment(loader=loader)
        self.log = log
        self.output_html_path = output_html_path
        self.contents: list[str] = []
        self.columns = self.construct_table_columns()
        self.title = ""

    def set_title(self, title: str) -> None:
        self.title = title
    
    def get_title(self) -> str:
        return self.title
    
    def add_contents(self, contents: str) -> None:
        self.contents.append(contents)
    
    def get_contents(self) -> list[str]:
        return self.contents

    @call_logger
    def add_heading(self, text: str) -> None:
        template = self.environment.get_template("heading.j2")
        self.add_contents(template.render({"text": text}))

    @call_logger
    def add_figure(self, figure_path: str) -> None:
        template = self.environment.get_template("figure.j2")
        self.add_contents(template.render({"link": os.path.join("fig", figure_path)}))
    
    def add_datetime(self) -> None:
        template = self.environment.get_template("datetime.j2")
        metadata = self.log.get_metadata()
        data = {
            "date" : metadata.created_date,
        }
        self.add_contents(template.render(data))
    
    @call_logger
    def add_summary(self) -> None:
        self.add_contents(f"<pre>{self.log.get_dataframe().describe()}</pre>")

    @call_logger
    def add_table(self) -> None:
        template = self.environment.get_template("table.j2")
        data = {
            "table": self.make_table_contents(),
            "table_columns": self.make_table_columns(),
        }
        self.add_contents(template.render(data))

    @call_logger
    def add_script(self, script_path: str) -> None:
        template = self.environment.get_template("script.j2")
        file = os.path.join(os.path.split(__file__)[0], script_path)
        self.add_contents(template.render({"text": self.load_file(file)}))

    @call_logger
    def add_css(self, css_path: str) -> None:
        template = self.environment.get_template("css.j2")
        file = os.path.join(os.path.split(__file__)[0], css_path)
        self.add_contents(template.render({"text": self.load_file(file)}))

    @call_logger
    def add_css_link(self, css_path: str) -> None:
        template = self.environment.get_template("css_link.j2")
        self.add_contents(template.render({"link": css_path}))
    
    @call_logger
    def write(self) -> None:
        template = self.environment.get_template("main.j2")
        data = {
            "title": self.get_title(),
            "sections": self.get_contents(),
        }
        with open(self.output_html_path, mode="w") as f:
            f.write(template.render(data))
    
    @call_logger
    def construct_table_columns(self) -> list[Column]:
        columns = [
            Column("testcase", HtmlColumnType.TEXT),
            Column("in", HtmlColumnType.URL),
            Column("stdout", HtmlColumnType.URL),
            Column("stderr", HtmlColumnType.URL),
            Column("status", HtmlColumnType.STATUS),
            Column("input_hash", HtmlColumnType.METADATA),
            Column("stdout_hash", HtmlColumnType.METADATA),
            Column("stderr_hash", HtmlColumnType.METADATA),
        ]
        metadata = self.log.get_metadata()
        for attribute in metadata.attributes:
            columns.append(Column(attribute, HtmlColumnType.TEXT))
        return columns

    @call_logger
    def load_file(self, file: str) -> str:
        with open(file, mode="r", encoding="utf-8") as f:
            text = f.read()
        return text

    @call_logger
    def get_data(self, column: str, row: int) -> Any:
        def df_at(column: str, row: int) -> Any:
            dataframe = self.log.get_dataframe()
            if column not in dataframe.columns:
                return None # 列がないならNoneを返す
            return dataframe.at[str(row), column]
        ret = df_at(column, row)
        return ret

    @call_logger
    def make_table_contents(self) -> list[dict[str, str]]:
        ret = []
        for row in range(len(self.log.get_dataframe())):
            rows = {}
            for column in self.columns:
                match column.type:
                    case HtmlColumnType.URL:
                        value = self.get_url_cell(column.title, row)
                    case HtmlColumnType.STATUS:
                        value = self.get_status_cell(column.title, row)
                    case HtmlColumnType.TEXT:
                        value = self.get_text_cell(column.title, row)
                    case HtmlColumnType.METADATA:
                        continue
                    case _:
                        raise InternalError("不明なHtmlColumnTypeがあります。")
                rows[column.title] = value
            ret.append(rows)
        return ret

    @call_logger
    def make_table_columns(self) -> dict[str, str]:
        table_columns = dict()
        for column in self.columns:
            match column.type:
                case HtmlColumnType.URL|HtmlColumnType.STATUS:
                    table_columns[column.title] = "normal"
                case HtmlColumnType.TEXT:
                    table_columns[column.title] = "sort"
                case HtmlColumnType.METADATA:
                    continue
                case _:
                    raise InternalError("不明なHtmlColumnTypeがあります。")
        return table_columns

    @call_logger
    def get_url_cell(self, column: str, row: int) -> str:
        value = self.get_data(column, row)
        template = self.environment.get_template("cell_with_file_link.j2")
        data = {
            "link": value,
            "value": "+",
            }
        return template.render(data)
    
    @call_logger
    def get_status_cell(self, column: str, row: int) -> str:
        text, description = self.get_data(column, row)
        match text:
            case None:
                text = "Success"
                color = "lime"
            case "IE":
                color = "red"
            case "Canceled":
                color = "gray"
            case _:
                color = "gold"
        if description is not None:
            template = self.environment.get_template("cell_with_color_and_mouseover_message.j2")
            data = {
                "color": color,
                "value": text,
                "description": description,
                }
        else:
            template = self.environment.get_template("cell_with_color.j2")            
            data = {
                "color": color,
                "value": text,
                }
        return template.render(data)
    
    @call_logger
    def get_text_cell(self, column: str, row: int) -> str:
        value = self.get_data(column, row)
        if type(value) is np.float64 or type(value) is np.float32:
            value = round(value, 3)
        template = self.environment.get_template("cell.j2")
        data = {
            "value": value,
            }
        return template.render(data)

class Director:
    def __init__(self, builder: BaseHtmlBuilder) -> None:
        self.__builder = builder

    def construct(self):
        self.__builder.set_title("Runner Result")
        self.__builder.add_datetime()
        self.__builder.add_heading("Summary")
        self.__builder.add_summary()
        self.__builder.add_heading("Figures")
        self.__builder.add_figure("histgram.png")
        self.__builder.add_figure("heatmap.png")
        self.__builder.add_heading("Table")
        self.__builder.add_table()
        self.__builder.add_script("js/Table.js")
        self.__builder.add_script("js/checkbox.js")
        self.__builder.add_css("js/SortTable.css")
        self.__builder.add_css_link(r"https://newcss.net/new.min.css")
        self.__builder.write()

def make_html(path: str, log: RunnerLog) -> None:
    builder = ResultHtmlBuilder(path, log)
    director = Director(builder)
    director.construct()
