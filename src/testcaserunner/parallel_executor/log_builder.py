import os
import hashlib
import json
from collections import defaultdict
from typing import Any
import datetime

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from ..debug import call_logger
from ..defines import LibraryMetadata
from .testcase import TestCase, TestCaseResult
from .log import RunnerLog

class LogBuilder:
    js_file_path = "js"
    infile_col = "in"
    stdout_col = "stdout"
    stderr_col = "stderr"
    infilename_col = "testcase"
    status_col = "status"
    description_col = "result_description"
    input_hash_col = "input_hash"
    stdout_hash_col = "stdout_hash"
    stderr_hash_col = "stderr_hash"

    def __init__(self, results: list[tuple[TestCase, TestCaseResult]], log_folder_name: str) -> None:
        self.log_folder_name = log_folder_name
        self.results = results

    def make_folder(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
    
    @call_logger
    def build(self) -> RunnerLog:
        self.make_json_file()
        self.make_figure()
        return self.runner_log

    @call_logger
    def make_figure(self) -> None:
        # ヒストグラムを描画
        df = self.runner_log.get_dataframe()
        df.hist()
        fig_dir_path = os.path.join(self.log_folder_name, "fig")
        self.make_folder(fig_dir_path)
        plt.savefig(os.path.join(fig_dir_path, 'histgram.png'))
        plt.close()

        # 相関係数のヒートマップ
        corr = df.corr(numeric_only=True)
        heatmap = sns.heatmap(corr, annot=True)
        heatmap.set_title('Correlation Coefficient Heatmap')
        plt.savefig(os.path.join(fig_dir_path, 'heatmap.png'))

    @call_logger
    def make_json_file(self) -> None:
        counter: dict[str, int] = defaultdict(int)
        def add_hash_info(hash: str, suffix: str) -> str:
            subhash = f"{hash}.{suffix}"
            index = counter[subhash]
            counter[subhash] += 1
            hash = f"{subhash}.{index}"
            return hash

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

        contents: defaultdict[str, list[Any]] = defaultdict(list)
        for testcase, result in zip(testcases, results):
            contents[self.infilename_col].append(os.path.basename(testcase.input_file_path))
            contents[self.input_hash_col].append(add_hash_info(self.get_file_hash(testcase.input_file_path), "in"))
            contents[self.stdout_hash_col].append(add_hash_info(self.get_file_hash(testcase.stdout_file_path), "stdout"))
            contents[self.stderr_hash_col].append(add_hash_info(self.get_file_hash(testcase.stderr_file_path), "stderr"))
            contents[self.infile_col].append(os.path.relpath(testcase.input_file_path, self.log_folder_name))
            contents[self.stdout_col].append(os.path.relpath(testcase.stdout_file_path, self.log_folder_name))
            contents[self.stderr_col].append(os.path.relpath(testcase.stderr_file_path, self.log_folder_name))
            contents[self.status_col].append([result.error_status, result.result_description])
            for key in user_attributes:
                value = result.attribute[key] if key in result.attribute else None
                contents[key].append(value)
        
        # jsonデータをそろえるため一度DataFrameにしてからjsonに直す
        contents = json.loads(pd.DataFrame(contents).to_json())
        
        metadata = {
            "library_name": LibraryMetadata.LIBRARY_NAME,
            "library_version": LibraryMetadata.LIBRARY_VERSION,
            "created_date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M"),
            "attributes": user_attributes,
            "log_folder_path": self.log_folder_name,
        }
        self.json_file = {
            "contents": contents,
            "metadata": metadata,
        }
        self.runner_log: RunnerLog = RunnerLog(contents, metadata)
        json_file_path = os.path.join(self.log_folder_name, "result.json")
        with open(json_file_path, 'w') as f:
            json.dump(self.json_file, f, indent=2)
    
    @call_logger
    def get_file_hash(self, path: str) -> str:
        if os.path.exists(path):
            return self.calculate_file_hash(path)
        else:
            return "" #ファイルが開けないときは空文字にしておく

    @call_logger
    def calculate_file_hash(self, file_path: str) -> str:
        hash_obj = hashlib.new('sha256')
        with open(file_path, 'rb') as file:
            while chunk := file.read(4096):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
