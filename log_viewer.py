import glob
import os
from typing import List
import json

import pandas as pd

from testcase_runner.testcase_runner import ResultStatus

log_dir = "log"
log_file = "result.json"

class Log():
    def __init__(self, path):
        with open(path, 'r') as file:
            json_data = json.load(file)
        tmp = os.path.split(path)[0]
        self.foleder_name = os.path.basename(tmp)
        contents = json_data["contents"]
        self.testcase_num = json_data["testcase_num"]
        self.file_content_hash = json_data["file_content_hash"]
        self.file_name_hash = json_data["file_name_hash"]
        self.has_score = json_data["has_score"]
        self.average_score = json_data["average_score"]
        self.__df = pd.DataFrame(contents)
    
    @property
    def df(self):
        return self.__df
    
    def get_iuput_file_hash(self):
        return (self.testcase_num, self.file_content_hash, self.file_name_hash)

class LogViewer():
    def __init__(self):
        def is_log_dir(path: str)->bool:
            path = os.path.join(path, log_file)
            return os.path.isfile(path)
        self.logs: List[Log] = []
        for dir in glob.glob(os.path.join(log_dir, "*")):
            if is_log_dir(dir):
                path = os.path.join(dir, log_file)
                log = Log(path)
                self.logs.append(log)
        
    def is_same_inputfiles(self, index_list: List[int]):
        s = set()
        for index in index_list:
            s.add(self.logs[index].get_iuput_file_hash())
        return len(s) == 1

    def show_two_data(self, index1: int, index2: int):
        if not self.is_same_inputfiles(index1, index2):
            return
        merged_df = pd.merge(self.logs[index1].df, self.logs[index2].df, on='input_file')
        print(merged_df)
    
    def get_data_frame(self, index: int):
        return self.logs[index].df
