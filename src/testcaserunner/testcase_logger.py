import os
import hashlib
import json
from enum import IntEnum, auto
from collections import defaultdict
from typing import Any

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from .runner_defines import RunnerSettings, RunnerMetadata
from .runner import TestCase, TestCaseResult
from .runner_logger import RunnerLogger

class HtmlColumnType(IntEnum):
    """HTMLファイルのcolumnの情報
    """
    URL = auto()
    STATUS = auto()
    TEXT = auto()
    METADATA = auto()

class RunnerLog:
    def __init__(self, contents: dict, metadata: dict) -> None:
        self._df = pd.DataFrame(contents)
        self._metadata = metadata
    
    @property
    def df(self) -> pd.DataFrame:
        return self._df

    @property
    def metadata(self) -> dict:
        return self._metadata
    
    def drop(self, column: str) -> None:
        self._df = self._df.drop(columns=[column], errors='ignore')
        self._metadata["attributes"].pop(column, None)
    
    def _df_at(self, column: str, row: int) -> Any:
        return self._df.at[str(row), column]

class RunnerLogManager:
    js_file_path = "js"
    infile_col = "in"
    stdout_col = "stdout"
    stderr_col = "stderr"
    infilename_col = "testcase"
    status_col = "status"
    input_hash_col = "input_hash"
    stdout_hash_col = "stdout_hash"
    stderr_hash_col = "stderr_hash"

    logger = RunnerLogger("RunnerLogManager")
    def __init__(self, results: list[tuple[TestCase, TestCaseResult]], settings: RunnerSettings) -> None:
        self.settings = settings
        if settings.debug:
            self.logger.enable_debug_mode()
        self.results = results
        self.attributes: dict[str, HtmlColumnType] = {
            self.infilename_col: HtmlColumnType.TEXT,
            self.input_hash_col: HtmlColumnType.METADATA,
            self.stdout_hash_col: HtmlColumnType.METADATA,
            self.stderr_hash_col: HtmlColumnType.METADATA,
            self.infile_col: HtmlColumnType.URL,
            self.stdout_col: HtmlColumnType.URL,
            self.stderr_col: HtmlColumnType.URL,
            self.status_col: HtmlColumnType.STATUS,
        }
        self.make_json_file()
        self.make_figure()
        self.base_dir = os.path.split(__file__)[0]
    
    @logger.function_tracer
    def get_log(self) -> RunnerLog:
        return self.runner_log

    json_file_name = "result.json"
    @logger.function_tracer
    def add_attribute(self, key: str, type: HtmlColumnType) -> None:
        self.attributes[key] = type

    histgram_fig_name = 'histgram.png'
    heatmap_fig_name = 'heatmap.png'
    @logger.function_tracer
    def make_figure(self) -> None:
        # ヒストグラムを描画
        self.runner_log.df.hist()
        plt.savefig(os.path.join(self.settings.fig_dir_path, self.histgram_fig_name))
        plt.close()

        # 相関係数のヒートマップ
        corr = self.runner_log.df.corr(numeric_only=True)
        heatmap = sns.heatmap(corr, annot=True)
        heatmap.set_title('Correlation Coefficient Heatmap')
        plt.savefig(os.path.join(self.settings.fig_dir_path, self.heatmap_fig_name))

    @logger.function_tracer
    def make_json_file(self) -> None:
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

        contents: defaultdict[str, list[Any]] = defaultdict(list)
        for testcase, result in zip(testcases, results):
            contents[self.infilename_col].append(os.path.basename(testcase.input_file_path))
            contents[self.input_hash_col].append(f"{os.path.basename(testcase.input_file_path)}.{self.get_file_hash(testcase.input_file_path)}")
            contents[self.stdout_hash_col].append(f"{self.get_file_hash(testcase.stdout_file_path)}")
            contents[self.stderr_hash_col].append(f"{self.get_file_hash(testcase.stderr_file_path)}")
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
            "library_name": RunnerMetadata.LIB_NAME,
            "created_date": self.settings.datetime.strftime("%Y/%m/%d %H:%M"),
            "testcase_num": len(testcases),
            "attributes": self.attributes,
        }
        self.json_file = {
            "contents": contents,
            "metadata": metadata,
        }
        self.runner_log: RunnerLog = RunnerLog(contents, metadata)
        json_file_path = os.path.join(self.settings.log_folder_name, self.json_file_name)
        with open(json_file_path, 'w') as f:
            json.dump(self.json_file, f, indent=2)
    
    @logger.function_tracer
    def get_file_hash(self, path: str) -> str:
        if os.path.exists(path):
            return self.calculate_file_hash(path)
        else:
            return "" #ファイルが開けないときは空文字にしておく

    @logger.function_tracer
    def calculate_file_hash(self, file_path: str) -> str:
        hash_obj = hashlib.new('sha256')
        with open(file_path, 'rb') as file:
            while chunk := file.read(4096):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
