import glob
import os
from typing import List
import json

import pandas as pd
import PySimpleGUI as sg

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
        self.setup_log_data()

        heading, table = self.make_table()
        self.table_length = len(table)
        self.row_select = [False for i in range(self.table_length)]
        colors = []
        for i in range(self.table_length):
            colors.append([i, "white"])
        layout = [
            [sg.Table(values=table, headings=heading,
            display_row_numbers=False, auto_size_columns=False,
            justification='right', num_rows=min(25, self.table_length),
            enable_events=True, key='-TABLE-')]
        ]
        # ウィンドウの生成
        self.main_window = sg.Window('Log Viewer', layout)

    def main_loop(self):
        # イベントループ
        while True:
            event, values = self.main_window.read()
            if event == sg.WINDOW_CLOSED:
                break
            elif event == '-TABLE-':
                if values['-TABLE-']:
                    row = values['-TABLE-'][0]
                    self.toggle_row_select(row)

        # ウィンドウを閉じる
        self.main_window.close()
    
    def toggle_row_select(self, row):
        self.row_select[row] = not self.row_select[row]
        self.update_window()
    
    def update_window(self):
        colors = []
        for i in range(self.table_length):
            if self.row_select[i]:
                colors.append((i, "yellow"))
        heading, table = self.make_table()
        self.main_window['-TABLE-'].update(row_colors=colors, values=table)

    def setup_log_data(self):
        def is_log_dir(path: str)->bool:
            path = os.path.join(path, log_file)
            return os.path.isfile(path)
        self.logs: List[Log] = []
        for dir in glob.glob(os.path.join(log_dir, "*")):
            if is_log_dir(dir):
                path = os.path.join(dir, log_file)
                log = Log(path)
                self.logs.append(log)
    
    default_heading = [
        "folder name",
        "average score",
        "show detail",
    ]
    def make_table(self):
        table = []
        for log in self.logs:
            row = [
                log.foleder_name,
                log.average_score,
                'ボタン',
            ]
            table.append(row)
        return self.default_heading, table
    
        
    def is_same_inputfiles(self, index1: int, index2: int):
        return self.logs[index1].get_iuput_file_hash() \
            == self.logs[index2].get_iuput_file_hash()

    def show_two_data(self, index1: int, index2: int):
        if not self.is_same_inputfiles(index1, index2):
            return
        merged_df = pd.merge(self.logs[index1].df, self.logs[index2].df, on='input_file')
        print(merged_df)
    
    def get_data_frame(self, index: int):
        return self.logs[index].df

    def show_diff(self):
        pass

a = LogViewer()

df = a.get_data_frame(0)

df.info()
p = df.describe()
print(p)

import matplotlib.pyplot as plt
import seaborn as sns

# ヒストグラムを描画
df.hist()
plt.show()

# ボックスプロットを描画
sns.boxplot(data=df)
plt.show()

exit()
a.main_loop()
