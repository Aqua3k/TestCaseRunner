from enum import Enum, auto
from abc import ABC, abstractmethod
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.console import RenderableType

from .database import Database

class ScreenStatus(Enum):
    MAIN_MENU = auto()
    SORT_RESULTS = auto()
    DELETE_RESULT = auto()
    COMPARE_RESULTS = auto()
    EXIT = auto()
    NOT_CHANGED = auto()

class KeyboardInputs(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    QUIT = auto()
    ENTER = auto()
    OTHER = auto()

class Color(Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"

def colorize_text(text: str, color: Color, reverse: bool = False, background: Color = None) -> Text:
    """指定された色で文字列を装飾し、オプションで色を反転または背景色を設定する"""
    style = color.value
    if reverse:
        style += " reverse"
    if background:
        style += f" on {background.value}"
    return Text(text, style=style)

class ScreenTableBase(ABC):
    def __init__(self, title: str = "") -> None:
        self.table = Table(title=title)

    def clear(self) -> None:
        self.table.columns.clear()
        self.table.rows.clear()

    def add_row(self, columns: list[RenderableType]) -> None:
        self.table.add_row(*columns)

    def add_column(self, name: str, **kwargs) -> None:
        self.table.add_column(name, **kwargs)

    def get_table(self) -> Table:
        return self.table

    @abstractmethod
    def update(self) -> None:
        pass

    @abstractmethod
    def notify_keyboard_input(self, key: KeyboardInputs) -> ScreenStatus:
        pass

class MainMenuTable(ScreenTableBase):
    def __init__(self) -> None:
        super().__init__(title="Menu")
        self.is_active = False
        self.selected = 0

    options = [
        "1. Sort Results",
        "2. Delete Result",
        "3. Compare Results",
        "4. Exit",
    ]

    def update(self):
        # テーブルの列をクリア
        self.clear()

        self.add_column("Select", justify="center")
        self.add_column("Menu")

        for i, option in enumerate(self.options):
            if i == self.selected:
                marker = ">"
                option = colorize_text(option, Color.BLUE, reverse=True)
            else:
                marker = " "
            self.add_row([marker, option])
    
    def notify_keyboard_input(self, key: KeyboardInputs) -> ScreenStatus:
        self.is_active = True
        match key:
            case KeyboardInputs.ENTER:
                match self.selected:
                    case 0:
                        return ScreenStatus.SORT_RESULTS
                    case 1:
                        return ScreenStatus.DELETE_RESULT
                    case 2:
                        return ScreenStatus.COMPARE_RESULTS
                    case 3:
                        return ScreenStatus.EXIT
            case KeyboardInputs.UP:
                self.selected -= 1
                self.selected %= len(self.options)
            case KeyboardInputs.DOWN:
                self.selected += 1
                self.selected %= len(self.options)
        
        return ScreenStatus.NOT_CHANGED

class ResultTable(ScreenTableBase):
    def __init__(self) -> None:
        super().__init__(title="Results")

    def update(self):
        database = Database()

        # テーブルの列をクリア
        self.clear()

        self.add_column("ID")
        self.add_column("Created Date")
        self.add_column("Link")

        for attribute in database.get_attributes():
            self.add_column(attribute)

        for i, log in enumerate(database.iterate_logs()):
            columns = []

            columns.append(f"{i+1}")
            metadata = log.get_metadata()
            columns.append(metadata.created_date)
            columns.append(f"[link={log.get_html_path()}]+[/link]")

            for attribute in database.get_attributes():
                data  = log.get(attribute)
                if isinstance(data, float):
                    columns.append(f"{data:.2f}")  # 小数点以下2桁にフォーマット
                else:
                    columns.append(str(data))
            self.add_row(columns)
    
    def notify_keyboard_input(self, key: KeyboardInputs) -> ScreenStatus:
        pass

class Screen:
    def __init__(self) -> None:
        self.result_table = ResultTable()
        self.menu_table = MainMenuTable()
        self.console = Console()
        self.live = None
        self.status = ScreenStatus.MAIN_MENU

    def __enter__(self):
        self.live = Live(console=self.console, refresh_per_second=10, screen=True)
        self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.live.__exit__(exc_type, exc_value, traceback)
    
    def notify_keyboard_input(self, key: KeyboardInputs) -> bool:
        """キーボード入力を通知する

        Args:
            key (KeyboardInputs): キーボード入力

        Returns:
            bool: True: 終了, False: 継続
        """
        status = self.menu_table.notify_keyboard_input(key)
        match status:
            case ScreenStatus.MAIN_MENU:
                self.status = self.menu_table.notify_keyboard_input(key)
            case ScreenStatus.SORT_RESULTS:
                self.status = self.result_table.notify_keyboard_input(key)
            case ScreenStatus.DELETE_RESULT:
                # TODO: 削除処理を追加
                return True
            case ScreenStatus.COMPARE_RESULTS:
                # TODO: 比較処理を追加
                return True
            case ScreenStatus.EXIT:
                return True
            case ScreenStatus.NOT_CHANGED:
                return False
        self.status = status
        return False

    def update(self) -> None:
        # テーブルを更新
        self.result_table.update()
        self.menu_table.update()

        # パネルにテーブルを追加
        result_panel = Panel(self.result_table.get_table(), title="Results")
        menu_panel = Panel(self.menu_table.get_table(), title="Menu")

        # カラムにパネルを追加
        columns = Columns([result_panel, menu_panel])

        # Liveを更新
        self.live.update(columns)
