import os

from jinja2 import Environment, FileSystemLoader
import numpy as np
from typing import Any

from .runner import ResultStatus, RunnerLog, HtmlColumnType
from .runner_logger import RunnerLogger

class HtmlSection:
    logger = RunnerLogger("HtmlSection")
    def __init__(self, environment: Environment, log: RunnerLog):
        self.environment = environment
        self.log = log

    @logger.function_tracer
    def get_html_text(self) -> str:
        return ""

    @logger.function_tracer
    def load_file(self, file: str) -> str:
        with open(file, mode="r", encoding="utf-8") as f:
            text = f.read()
        return text

    def get_data(self, column: str, row: int) -> Any:
        # 欠損値の場合は空文字にする
        ret = self.log._df_at(column, row)
        if ret is None:
            ret = ""
        return ret

class HtmlFigureSection(HtmlSection):
    logger = RunnerLogger("HtmlFigureSection")
    def __init__(self, environment: Environment, log: RunnerLog):
        super().__init__(environment, log)

    histgram_fig_name = 'histgram.png'
    heatmap_fig_name = 'heatmap.png'
    @logger.function_tracer
    def get_html_text(self) -> str:
        template = self.environment.get_template("figure.j2")
        ret = [
            template.render({"link": os.path.join("fig", self.histgram_fig_name)}),
            template.render({"link": os.path.join("fig", self.heatmap_fig_name)}),
        ]
        return "\n".join(ret)

class HtmlSummarySection(HtmlSection):
    logger = RunnerLogger("HtmlSummarySection")
    def __init__(self, environment: Environment, log: RunnerLog):
        super().__init__(environment, log)

    @logger.function_tracer
    def get_html_text(self) -> str:
        template = self.environment.get_template("summary.j2")
        data = {
            "date" : self.log.metadata["created_date"],
            "summary": f"<pre>{self.log.df.describe()}</pre>",
        }
        return template.render(data)

class HtmlTableSection(HtmlSection):
    logger = RunnerLogger("HtmlTableSection")
    def __init__(self, environment: Environment, log: RunnerLog):
        super().__init__(environment, log)

    @logger.function_tracer
    def get_html_text(self) -> str:
        template = self.environment.get_template("table.j2")
        data = {
            "table": self.make_table_contents(),
            "table_columns": self.make_table_columns(),
        }
        return template.render(data)

    @logger.function_tracer
    def make_table_contents(self) -> list[dict[str, str]]:
        ret = []
        for row in range(self.log.metadata["testcase_num"]):
            rows = {}
            for column in self.log.metadata["attributes"].keys():
                match self.log.metadata["attributes"][column]:
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

    @logger.function_tracer
    def make_table_columns(self) -> dict[str, str]:
        table_columns = dict()
        for column in self.log.metadata["attributes"].keys():
            match self.log.metadata["attributes"][column]:
                case HtmlColumnType.URL|HtmlColumnType.STATUS:
                    table_columns[column] = "normal"
                case HtmlColumnType.TEXT:
                    table_columns[column] = "sort"
                case HtmlColumnType.METADATA:
                    continue
                case _:
                    assert "error: 不明なHtmlColumnTypeがあります。"
        return table_columns

    @logger.function_tracer
    def get_url_cell(self, column: str, row: int) -> str:
        value = self.get_data(column, row)
        template = self.environment.get_template("cell_with_file_link.j2")
        data = {
            "link": value,
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
    @logger.function_tracer
    def get_status_cell(self, column: str, row: int) -> str:
        value = self.get_data(column, row)
        text, color = self.status_texts.get(value, ("IE", "red"))
        template = self.environment.get_template("cell_with_color.j2")
        data = {
            "color": color,
            "value": text,
            }
        return template.render(data)
    
    @logger.function_tracer
    def get_text_cell(self, column: str, row: int) -> str:
        value = self.get_data(column, row)
        if type(value) is np.float64 or type(value) is np.float32:
            value = round(value, 3)
        template = self.environment.get_template("cell.j2")
        data = {
            "value": value,
            }
        return template.render(data)

class HtmlHeaderScriptSection(HtmlSection):
    logger = RunnerLogger("HtmlTableSection")
    def __init__(self, environment: Environment, log: RunnerLog):
        super().__init__(environment, log)

    @logger.function_tracer
    def get_html_text(self) -> str:
        template = self.environment.get_template("script.j2")
        file = os.path.join(os.path.split(__file__)[0], "js/Table.js")
        return template.render({"text": self.load_file(file)})

class HtmlFooterScriptSection(HtmlSection):
    logger = RunnerLogger("HtmlTableSection")
    def __init__(self, environment: Environment, log: RunnerLog):
        super().__init__(environment, log)

    @logger.function_tracer
    def get_html_text(self) -> str:
        template = self.environment.get_template("script.j2")
        file = os.path.join(os.path.split(__file__)[0], "js/checkbox.js")
        return template.render({"text": self.load_file(file)})

class HtmlCssSection(HtmlSection):
    logger = RunnerLogger("HtmlTableSection")
    def __init__(self, environment: Environment, log: RunnerLog):
        super().__init__(environment, log)

    @logger.function_tracer
    def get_html_text(self) -> str:
        template1 = self.environment.get_template("css_link.j2")
        template2 = self.environment.get_template("css.j2")
        file = os.path.join(os.path.split(__file__)[0], "js/SortTable.css")
        ret = [
            template2.render({"text": self.load_file(file)}),
            template1.render({"link": r"https://newcss.net/new.min.css"}),
        ]
        return "".join(ret)

class HtmlParser:
    logger = RunnerLogger("HtmlParser")
    def __init__(self, runner_log: RunnerLog, output_path: str, debug: bool) -> None:
        if debug:
            self.logger.enable_debug_mode()
        self.runner_log = runner_log
        self.output_path = output_path
        self.base_dir = os.path.split(__file__)[0]
        self.sections: list[type[HtmlSection]] = [
            HtmlHeaderScriptSection,
            HtmlCssSection,
            HtmlSummarySection,
            HtmlFigureSection,
            HtmlTableSection,
            HtmlFooterScriptSection,
        ]
    html_file_name = "result.html"
    @logger.function_tracer
    def make_html(self) -> None:
        loader = FileSystemLoader(os.path.join(self.base_dir, r"templates"))
        environment = Environment(loader=loader)
        template = environment.get_template("main.j2")
        texts: list[str] = []
        for section in self.sections:
            sect = section(environment, self.runner_log)
            texts.append(sect.get_html_text())
        data = {"sections": texts}
        html_file_path = os.path.join(self.output_path, self.html_file_name)
        with open(html_file_path, mode="w") as f:
            f.write(template.render(data))
