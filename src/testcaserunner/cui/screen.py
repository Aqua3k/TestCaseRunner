from enum import Enum, auto
from abc import ABC, abstractmethod

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

from .database import Database

class KeyboardInputs(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    QUIT = auto()
    ENTER = auto()
    OTHER = auto()

class ScreenTableBase(ABC):
    def __init__(self, title: str = "") -> None:
        self.table = Table(title=title)

    def clear(self) -> None:
        self.table.columns.clear()
        self.table.rows.clear()

    def add_row(self, columns: list[str]) -> None:
        self.table.add_row(*columns)

    def add_column(self, name: str, **kwargs) -> None:
        self.table.add_column(name, **kwargs)

    def get_table(self) -> Table:
        return self.table

    @abstractmethod
    def update(self) -> None:
        pass

class MainMenuTable(ScreenTableBase):
    def __init__(self) -> None:
        super().__init__(title="Menu")

    options = [
        "1. View All Results",
        "2. Sort Results",
        "3. Delete Result",
        "4. Compare Results",
        "5. Exit",
    ]

    def update(self):
        selected = 0  # TODO: 選択された項目を保持する変数を追加する

        # テーブルの列をクリア
        self.clear()

        self.add_column("Select", justify="center")
        self.add_column("Menu")

        for i, option in enumerate(self.options):
            marker = ">" if i == selected else ""
            self.add_row([marker, option])

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

class Screen:
    def __init__(self) -> None:
        self.result_table = ResultTable()
        self.menu_table = MainMenuTable()
        self.console = Console()
        self.live = None

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
        if key == KeyboardInputs.QUIT or key == KeyboardInputs.OTHER:
            return True
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