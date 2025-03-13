from rich import print
import msvcrt

from ..debug import Logger
from .screen import KeyboardInputs, Screen

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
        with Screen() as screen:
            while True:
                screen.update()
                key = self.handle_keybord_input()
                if screen.notify_keyboard_input(key):
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
