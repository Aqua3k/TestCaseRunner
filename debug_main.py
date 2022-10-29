import glob
import os
import shutil
import datetime

from mysrc.settings import *
from mysrc.result_classes import ResultInfoAll
from mysrc.program_rannner import exac_program

def make_results(results: ResultInfoAll) -> None:
    """ファイルに出力処理のまとめ"""
    results.make_html_file()
    results.make_csv_file()
    if is_make_fig:
        import mysrc.statistics_lib as sl #外部モジュールのimportが必要なのでここに
        sl.statisticsMain()
    make_log()

def init_log() -> None:
    """Logフォルダの初期化"""
    shutil.rmtree(result_file_path, ignore_errors=True)
    os.mkdir(result_file_path)

def make_log() -> None:
    """html, csv, main, in, outファイルをコピーしてlog以下に保存する"""
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
    # inファイルコピー
    shutil.copytree("in", os.path.join(path, "in"))
    # outファイルコピー
    shutil.copytree("out", os.path.join(path, "out"))

def main() -> None:
    """main処理"""

    results = ResultInfoAll()
    init_log()
    for filename in glob.glob(os.path.join(input_file_path, "*")):
        result = exac_program(filename)
        results.add_result(result)
    make_results(results)

if __name__ == "__main__":
    main()
