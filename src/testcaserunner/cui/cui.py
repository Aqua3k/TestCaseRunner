from rich import print

from ..debug import Logger
from ..defines import InternalError
from .screen import BaseScreen, ScreenStatus, MainScreen

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

def run_cui(_debug: bool = False) -> None:
    if _debug:
        Logger.enable_debug_mode()
    screens = construct_screens()
    cui = CUI(screens)
    cui.activate(ScreenStatus.MAIN_SCREEN)
