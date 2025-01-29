import os
from enum import Enum, auto

from rich import print
from rich.table import Table
from rich.console import Console

from .diff_viewer import RunnerLogViewer
from .testcase_logger import RunnerLog

class Result:
    def __init__(self):
        pass

class ResultTable:
    def __init__(self, log: RunnerLog):
        self.log = log

    def add_result(self, result: Result):
        pass

class Status(Enum):
    MENU = auto()
    VIEW_RESULTS = auto()
    SORT_RESULTS = auto()
    DELETE_RESULTS = auto()
    COMPARE_RESULTS = auto()

class CUI:
    main_menu_string = (
        "=== Test Result Manager ===\n"
        "1. View All Results\n"
        "2. Sort Results\n"
        "3. Delete Result\n"
        "4. Compare Results\n"
        "5. Exit\n"
        )
    def __init__(self):
        pass
    
    def activate(self):
        print(self.main_menu_string)
        while 1:
            key = input()
            pass

def main():
    print(f"current directory: {os.getcwd()}")
    viewer = RunnerLogViewer()
    logs = viewer.get_logs()

    attributes = dict()
    for log in logs:
        atts = log.get_attributes()
        for att in atts:
            attributes[att] = ""

    # テーブル作成
    table = Table(title="Test Results")

    table.add_column("ID")
    table.add_column("created_data")

    for attribute in attributes.keys():
        table.add_column(attribute)

    for i, log in enumerate(logs):
        columns = []

        columns.append(f"{i+1}")
        columns.append(log.get_created_date())

        for attribute in attributes:
            columns.append("None")
        
        table.add_row(*columns)

    # テーブルを表示
    console = Console()
    console.print(table)

    cui = CUI()
    cui.activate()
