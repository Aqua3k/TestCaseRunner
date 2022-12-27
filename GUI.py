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
                [sg.Button('EDIT SETTINGS')],
                [sg.Button('SHOW LOGS')]
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

meta_datas = [
    "FILE NUMBER",
    "AVERAGE SCORE",
    "MAX SCORE",
    "MIN SCORE",
]
meta_data_headers = [
    "DATE",
    "INPUTS",
    "AVE.",
    "MAX",
    "MIN",
]
log_list = None
def get_results():
    global log_list

    def parse_date(folder):
        """ファイルの名前から'mm/dd xx:yy'の形式に変換する"""
        filename = os.path.split(folder)[1]
        return f"{filename[4:6]}/{filename[6:8]} {filename[8:10]}:{filename[10:12]}"
    
    def get_digits(string):
        ret = ""
        for s in string:
            if "0" <= s <= "9" or s in ".-":
                ret += s
        try:
            return int(ret)
        except:
            return 0

    def get_meta_data(folder):
        html_path = glob.glob(folder + r"\*.html")[0]
        meta_data = []
        date = parse_date(folder)
        meta_data.append(date)
        with open(html_path) as f:
            lines = f.readlines()
            for header in meta_datas:
                for i,line in enumerate(lines):
                    if header in line:
                        break
                meta_data.append(get_digits(lines[i+1]))
        return meta_data

    ret = []
    log_list = glob.glob(r"log\*")
    for folder in log_list:
        meta_data = get_meta_data(folder)
        ret.append(meta_data)
    return ret

def get_log_viewer_window_layout():
    results = get_results()
    layout = [
        [sg.Button('ERASE'), sg.Button('SHOW DETAILS')],
        [sg.Table(
            results,
            headings=meta_data_headers,
            auto_size_columns=False,
            #col_widths=[15, 5, 10, 10, 10],
            justification='left',
            text_color='#000000',
            background_color='#cccccc',
            alternating_row_color='#ffffff',
            header_text_color='#0000ff',
            header_background_color='#cccccc',
            size=(40, 20),
            key="TABLE")]
        ]
    return layout

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
            config_window = sg.Window('Setting Editor', get_config_window_layout())
            while True:
                event, values = config_window.read()
                if event == "__TIMEOUT__":
                    continue
                elif event == "SAVE":
                    save_setting(values)
                elif event == sg.WIN_CLOSED:
                    break
        elif event == 'SHOW LOGS':
            log_viewer = sg.Window('Log Viewer', get_log_viewer_window_layout())
            while True:
                event, values = log_viewer.read()
                if event == "__TIMEOUT__":
                    continue
                elif event == sg.WIN_CLOSED:
                    break
                elif event == "ERASE":
                    if len(values["TABLE"]) == 0:
                        continue
                    idx = values["TABLE"][0]
                    filder = log_list[idx]
                    shutil.rmtree(filder)
                    log_viewer.close()
                    log_viewer = sg.Window('Log Viewer', get_log_viewer_window_layout())
                elif event == "SHOW DETAILS":
                    if len(values["TABLE"]) == 0:
                        continue
                    idx = values["TABLE"][0]
                    path = os.path.join(log_list[idx], "*.html")
                    files = glob.glob(path)
                    assert len(files) == 1
                    html_path = files[0]
                    subprocess.run(["start", html_path], shell=True)
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
