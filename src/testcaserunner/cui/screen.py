import os
from enum import Enum, auto
from abc import ABC, abstractmethod

from rich import print
from rich.table import Table
from rich.console import Console

from ..parallel_executor import LogManager
from ..debug import call_logger

class ScreenStatus(Enum):
    MAIN_SCREEN = auto()
    VIEW_RESULTS = auto()
    SORT_RESULTS = auto()
    DELETE_RESULTS = auto()
    COMPARE_RESULTS = auto()

class BaseScreen(ABC):
    @call_logger
    def open(self) -> None:
        pass
    
    @call_logger
    def close(self) -> None:
        pass

    @abstractmethod
    def display(self) -> None:
        pass

    @abstractmethod
    def handle_input(self, key: str) -> ScreenStatus:
        pass

class MainScreen(BaseScreen):
    main_menu_string = (
        "=== Test Result Manager ===\n"
        "1. View All Results\n"
        "2. Sort Results\n"
        "3. Delete Result\n"
        "4. Compare Results\n"
        "5. Exit\n"
        )
    def display(self) -> None:
        print(f"current directory: {os.getcwd()}")

        print(self.main_menu_string)
        viewer = LogManager()
        logs = viewer.get_log()

        attributes = dict()
        for log in logs:
            atts = log.get_metadata().attributes
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
            metadata = log.get_metadata()
            columns.append(metadata.created_date)

            for attribute in attributes:
                columns.append("None")
            
            table.add_row(*columns)

        # テーブルを表示
        console = Console()
        console.print(table)
    
    def handle_input(self, key: str) -> ScreenStatus:
        return ScreenStatus.MAIN_SCREEN
