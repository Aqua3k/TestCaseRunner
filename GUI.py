import glob
import subprocess
import os
import shutil
import PySimpleGUI as sg
from debug_main import main as runner_main
from mysrc.config import get_setting, write_config

def get_layout():
# ウィンドウに配置するコンポーネント
    layout = [
                [sg.Button('UPDATE')],
                [sg.Button('RUN SCRIPT')],
                [sg.Button('EDIT SETTINGS')]
    ]
    for folder in glob.glob(r"log\*"):
        layout.append([sg.Text(folder), sg.Button('VIEW RESULT', key=("view", folder)), sg.Button('DELETE', key=("delete", folder))])
    return layout

def get_default_values():
    settings = get_setting()
    return settings.input_file_path, settings.command

def get_config_window_layout():
    in_default, command_default = get_default_values()
    layout = [
        [sg.Button('SAVE')],
        [sg.Text("入力ファイルを選択してください")],
        [
            sg.InputText(default_text=in_default, enable_events=True, key="folder_select", size=(50, 50)),
            sg.FolderBrowse('Browse', key='input_folder')
        ],
        [sg.Text("")],
        [sg.Text("プログラムを実行するコマンドを入力してください")],
        [sg.Text("※入力ファイル名は in_file, 出力ファイル名は out_file としてください")],
        [sg.Input(default_text=command_default, key="command_select", size=(60, 50))]
    ]
    return layout

def save_setting(values):
    in_path = values["folder_select"]
    command = values["command_select"]
    write_config(in_path, command)

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
            update_window()
        elif event == 'EDIT SETTINGS':
            config_window = sg.Window('Test Case Runner', get_config_window_layout())
            while True:
                event, values = config_window.read()
                if event == "__TIMEOUT__":
                    continue
                elif event == "SAVE":
                    save_setting(values)
                elif event == sg.WIN_CLOSED:
                    break
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
