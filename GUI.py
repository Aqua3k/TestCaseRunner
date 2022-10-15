import glob
import subprocess
import os
import shutil
import PySimpleGUI as sg
from debug_main import main as runner_main

def get_layout():
# ウィンドウに配置するコンポーネント
    layout = [
                [sg.Button('UPDATE')],
                [sg.Button('RUN SCRIPT')]
    ]
    for folder in glob.glob(r"log\*"):
        layout.append([sg.Text(folder), sg.Button('VIEW RESULT', key=("view", folder)), sg.Button('DELETE', key=("delete", folder))])
    return layout

def run_script():
    runner_main()

def update_window():
    global window
    window.close()
    window = sg.Window('Test Case Runner', get_layout())

window = None
def main():
    global window
    sg.theme('DarkAmber')   # デザインテーマの設定
    # ウィンドウの生成
    window = sg.Window('Test Case Runner', get_layout())

    # イベントループ
    while True:
        event, values = window.read()
        if event == "__TIMEOUT__":
            continue
        elif event == "UPDATE":
            update_window()
        elif event == sg.WIN_CLOSED:
            break
        elif event == 'RUN SCRIPT':
            run_script()
            subprocess.run(["start", "result.html"], shell=True)
            update_window()
        else:
            key, folder = event
            if key == "view":
                path = os.path.join(folder, "*.html")
                files = glob.glob(path)
                assert len(files) == 1
                html_path = files[0]
                subprocess.run(["start", html_path], shell=True)
            elif key == "delete":
                shutil.rmtree(folder)
                update_window()
            else:
                assert 0

    window.close()

if __name__ == "__main__":
    main()
