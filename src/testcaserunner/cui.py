import os
from enum import Enum, auto
from abc import ABC, abstractmethod

from rich import print
from rich.table import Table
from rich.console import Console

from .parallel_executor import RunnerLog, LogManager
from .debug import Logger, call_logger
from .defines import InternalError

class Result:
    def __init__(self):
        pass

class ResultTable:
    def __init__(self, log: RunnerLog):
        self.log = log

    def add_result(self, result: Result):
        pass

class Singleton(ABC):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cls] = instance
            if hasattr(instance, "first_init"):  # 初回だけ実行
                instance.first_init()
        return cls._instances[cls]

    @abstractmethod
    def first_init(self):
        pass

class Database(Singleton):
    def first_init(self):
        pass

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
            atts = log.get_metadata().get("attributes")
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
            columns.append(metadata.get("created_date"))

            for attribute in attributes:
                columns.append("None")
            
            table.add_row(*columns)

        # テーブルを表示
        console = Console()
        console.print(table)
    
    def handle_input(self, key: str) -> ScreenStatus:
        return ScreenStatus.MAIN_SCREEN

class CUI:
    def __init__(self, screens: dict[ScreenStatus, BaseScreen]):
        self.screens = screens
    
    def __get_screen(self, status: ScreenStatus) -> BaseScreen:
        result = self.screens.get(status)
        if result is None:
            raise InternalError("screenが取得できないよ")
        return result
    
    def __open_screen(self, screen: BaseScreen|None) -> None:
        if screen is None:
            return
        screen.open()
    
    def __close_screen(self, screen: BaseScreen|None) -> None:
        if screen is None:
            return
        screen.close()
    
    def __display_screen(self, screen: BaseScreen|None) -> None:
        if screen is None:
            return
        screen.display()
    
    def __handle_input(self, screen: BaseScreen|None, key: str) -> ScreenStatus:
        if screen is None:
            raise InternalError("処理できない画面を開こうとしたよ")
        return screen.handle_input(key)
    
    def main_loop(self, default_screen: ScreenStatus) -> None:
        status: ScreenStatus|None = None
        next_status = default_screen
        screen: BaseScreen|None = None
        while 1:
            if status != next_status:
                # 前の画面を閉じる
                self.__close_screen(screen)

                status = next_status
                screen = self.__get_screen(status)
                # 次の画面を開く
                self.__open_screen(screen)
                self.__display_screen(screen)
            key = input()
            if key == "q":
                break
            next_status = self.__handle_input(screen, key)

    def activate(self, default_screen: ScreenStatus) -> None:
        try:
            self.main_loop(default_screen)
        except KeyboardInterrupt:
            pass
        print("bye!")

def construct_screens() -> dict[ScreenStatus, BaseScreen]:
    screen = MainScreen()
    screens: dict[ScreenStatus, BaseScreen] = {
            ScreenStatus.MAIN_SCREEN: screen,
        }
    return screens

def main():
    screens = construct_screens()
    cui = CUI(screens)
    cui.activate(ScreenStatus.MAIN_SCREEN)
