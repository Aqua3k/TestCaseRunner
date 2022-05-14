import shutil
import glob
import datetime
import os
import datetime

from mysrc.result_classes import ResultInfoAll
from mysrc.html_templates import *
from mysrc.settings import *

def init_all() -> None:
    """初期化処理のまとめ"""
    init_log()

def make_all_result(resultAll: ResultInfoAll) -> None:
    """ファイルに出力処理のまとめ"""
    resultAll.make_html_file()
    resultAll.make_csv_file()
    if is_make_fig:
        import mysrc.statistics_lib as sl #外部モジュールのimportが必要なのでここに
        sl.statisticsMain()
    make_log()

def init_log() -> None:
    """Logフォルダの初期化"""
    shutil.rmtree(result_file_path, ignore_errors=True)
    os.mkdir(result_file_path)

def make_log() -> None:
    """html, csv, mainファイルをコピーしてlog以下に保存する"""
    timeInfo = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    if logFilePath not in glob.glob("*"): os.mkdir(logFilePath)
    path =  os.path.join(logFilePath, str(timeInfo))
    os.mkdir(path)

    # mainファイルコピー
    shutil.copy("main.py", path)
    # htmlファイルコピー
    shutil.copy("result.html", path)
    # csvファイルコピー
    shutil.copy(os.path.join(statistics_path, csv_file_name), path)
