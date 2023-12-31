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
        contents = json_data["contents"]
        self.testcase_num = json_data["testcase_num"]
        self.file_content_hash = json_data["file_content_hash"]
        self.file_name_hash = json_data["file_name_hash"]
        self.has_score = json_data["has_score"]
        self.df = pd.DataFrame(contents)
    
    def show_log(self):
        print(self.df)
    
    def get_iuput_file_hash(self):
        return (self.testcase_num, self.file_content_hash, self.file_name_hash)

class LogManager():
    def __init__(self, path):
        def is_log_dir(path: str)->bool:
            path = os.path.join(path, log_file)
            return os.path.isfile(path)
        self.logs: List[Log] = []
        for dir in glob.glob(os.path.join(path, "*")):
            if is_log_dir(dir):
                path = os.path.join(dir, log_file)
                log = Log(path)
                self.logs.append(log)
    
    def show_log(self, index: int):
        self.logs[index].show_log()
    
    def is_same_inputfiles(self, index1: int, index2: int):
        return self.logs[index1].get_iuput_file_hash() \
            == self.logs[index2].get_iuput_file_hash()
    
    def show_two_data(self, index1: int, index2: int):
        if not self.is_same_inputfiles(index1, index2):
            return
        merged_df = pd.merge(self.logs[index1].df, self.logs[index2].df, on='input_file')
        print(merged_df)

if __name__ == "__main__":
    database = LogManager(log_dir)
    database.show_log(0)
    database.show_log(1)
    database.show_two_data(0, 1)
