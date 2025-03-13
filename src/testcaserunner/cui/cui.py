from rich import print
import msvcrt
from enum import Enum, auto

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

from ..debug import Logger
from ..defines import InternalError
from .database import Database

class KeyboardInputs(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    QUIT = auto()
    ENTER = auto()
    OTHER = auto()

class Screen:
    def __init__(self) -> None:
        self.result_table = Table(title="Test Results")
        self.menu_table = Table(show_header=True, header_style="bold magenta")

    def update_result_table(self) -> Table:
        database = Database()

        # テーブルの列をクリア
        self.result_table.columns.clear()
        self.result_table.rows.clear()

        self.result_table.add_column("ID")
        self.result_table.add_column("Created Date")
        self.result_table.add_column("Link")

        for attribute in database.get_attributes():
            self.result_table.add_column(attribute)

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
            self.result_table.add_row(*columns)
        return self.result_table

    def update_main_menu(self) -> Table:
        options = [
            "1. View All Results",
            "2. Sort Results",
            "3. Delete Result",
            "4. Compare Results",
            "5. Exit",
        ]
        selected = 0

        # テーブルの列をクリア
        self.menu_table.columns.clear()
        self.menu_table.rows.clear()

        self.menu_table.add_column("Select", justify="center")
        self.menu_table.add_column("Menu")

        for i, option in enumerate(options):
            marker = ">" if i == selected else ""
            self.menu_table.add_row(marker, option)

        return self.menu_table

    def display(self, live: Live) -> None:
        # テーブルを更新
        result_table = self.update_result_table()
        main_menu_table = self.update_main_menu()

        # パネルにテーブルを追加
        result_panel = Panel(result_table, title="Results")
        menu_panel = Panel(main_menu_table, title="Menu")

        # カラムにパネルを追加
        columns = Columns([result_panel, menu_panel])

        # Liveを更新
        live.update(columns)

class CUI:
    def __init__(self):
        pass
    
    def handle_keybord_input(self) -> KeyboardInputs:
        key = msvcrt.getch()
        if key == b"\xe0": # arrow key
            key = msvcrt.getch()
            match key:
                case b'H':  # 上キー
                    return KeyboardInputs.UP
                case b'P':  # 下キー
                    return KeyboardInputs.DOWN
                case b'K':  # 左キー
                    return KeyboardInputs.LEFT
                case b'M':  # 右キー
                    return KeyboardInputs.RIGHT
                case b'q':  # 'q' キー
                    return KeyboardInputs.QUIT
                case b'\r':  # Enterキー
                    return KeyboardInputs.ENTER
        return KeyboardInputs.OTHER
    
    def main_loop(self) -> None:
        screen = Screen()
        console = Console()
        with Live(console=console, refresh_per_second=10, screen=True) as live:
            while True:
                screen.display(live)
                key = self.handle_keybord_input()
                if key == KeyboardInputs.QUIT or key == KeyboardInputs.OTHER:
                    break

    def activate(self) -> None:
        try:
            self.main_loop()
        except KeyboardInterrupt:
            pass
        print("bye!")

def run_cui(_debug: bool = False) -> None:
    if _debug:
        Logger.enable_debug_mode()
    cui = CUI()
    cui.activate()
