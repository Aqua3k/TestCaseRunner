import os

from rich import print
from rich.table import Table
from rich.console import Console

from .diff_viewer import RunnerLogViewer

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
