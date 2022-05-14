import sys
import time
import os
import shutil
import subprocess

import psutil

from mysrc.settings import *
from mysrc.result_classes import *
from mysrc.html_templates import *

in_file = "in.txt"
out_file = "out.txt"

def exac_program(next_file) -> ResultInfo:
    """プログラムを実行して結果を返す
    
    Returns:
        ResultInfo: 実行結果の情報
    """
    start_time = time.time()
    name = os.path.basename(next_file)
    
    score, err_stat, stdout = exac_command(name)

    end_time = time.time()

    lis = []
    # TODO: デバッグ用の情報を取得する

    # 標準出力をファイル出力
    out_file_name = "stdout" + name
    path = os.path.join(result_file_path, out_file_name)
    with open(path, mode='w') as f:
        f.write(stdout)

    #Pythonは自動でimportガードがついてるので一度モジュールを削除する
    if 'main' in sys.modules: del sys.modules["main"]

    return ResultInfo(name, score, end_time - start_time, err_stat, stdout, lis)

def kill_process(proc_pid):
    """プロセスをkillする"""
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

def exac_command(name: str):
    """プログラムを実行する
    
    Args:
        name(str): 実行対象の入力ファイルの名前
    
    Returns:
        int, int, str: 得点, 結果のステータス, 標準出力
    """
    err_stat = ResultInfo.AC
    score = ""
    stdout = ""

    cmd = command.format(in_file=in_file, out_file=out_file)

    #inファイルコピー
    path = os.path.join(input_file_path, name)
    shutil.copy(path, in_file)
    
    try:
        #実行
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        result = proc.communicate(timeout=time_limit)

        if proc.returncode != 0: err_stat = ResultInfo.RE
        stdout = result[1]
        score = get_score_from_stdout(stdout)

        #outをコピー
        path = os.path.join(result_file_path, name)
        shutil.copy(out_file, path)

    except: #ここに入るのはTLEしたときだけ
        err_stat = ResultInfo.TLE
        kill_process(proc.pid) #proc.kill()ではうまくいかなかったので
    
    if err_stat == ResultInfo.RE or err_stat == ResultInfo.TLE:
        if err_stat == ResultInfo.RE:
            score = "RE"
            msg = "RE "
        else:
            score = "TLE"
            msg = "TLE"
        print(msg + " in ", name)
    
    return score, err_stat, stdout

def get_score_from_stdout(string: str) -> int:
    """標準出力から得点を取り出す
    
    Args:
        string(str): 得点を取り出す元の文字列
    Returns:
        int: 得点
    """
    u = string.lower()
    if "score" in u:
        idx = u.index("score")
    else:
        idx = 0
    s = ""
    flg = False
    for t in u[idx:]:
        if "0" <= t <= "9":
            s += t
            flg = True
        else:
            if flg: break
    try   : ret = int(s)
    except: ret = 0
    return ret
