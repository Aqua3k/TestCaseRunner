import glob
import os
import shutil
import datetime
from concurrent.futures import ProcessPoolExecutor

from mysrc.settings import *
from mysrc.result_classes import ResultInfoAll
from mysrc.program_rannner import exac_program

def make_results(results: ResultInfoAll) -> None:
    """ファイルに出力処理のまとめ"""
    results.make_html_file()
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
    os.remove("result.html") #ファイル削除
    # inファイルコピー
    shutil.copytree("in", os.path.join(path, "in"))
    # outファイルコピー
    shutil.copytree("out", os.path.join(path, "out"))

def main() -> None:
    """main処理"""

    results = ResultInfoAll()
    init_log()
    futures  = []
    with ProcessPoolExecutor() as executor:
        for filename in glob.glob(os.path.join(input_file_path, "*")):
            future = executor.submit(exac_program, filename)
            futures.append(future)
    
    for future in futures:
        results.add_result(future.result())
    make_results(results)

if __name__ == "__main__":
    main()
