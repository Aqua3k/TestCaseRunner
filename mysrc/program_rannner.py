import time
import os
import subprocess

from mysrc.settings import *
from mysrc.result_classes import *
from mysrc.html_templates import *

def exac_program(next_file) -> ResultInfo:
    """プログラムを実行して結果を返す
    
    Returns:
        ResultInfo: 実行結果の情報
    """
    start_time = time.time()
    score, err_stat, stdout = exac_command(next_file)
    end_time = time.time()

    # 標準出力をファイル出力
    out_file_name = "stdout" + os.path.basename(next_file)
    path = os.path.join(result_file_path, out_file_name)
    with open(path, mode='w') as f:
        f.write(stdout)

    return ResultInfo(os.path.basename(next_file), score, end_time - start_time, err_stat, stdout)

def exac_command(input_file_path: str):
    """プログラムを実行する
    
    Args:
        input_file_path(str): 実行対象の入力ファイルの名前
    
    Returns:
        int, int, str: 得点, 結果のステータス, 標準出力
    """
    err_stat = ResultInfo.AC
    score = ""
    stdout = ""

    basename = os.path.basename(input_file_path)
    out_file_path = os.path.join(result_file_path, basename)

    cmd = command.format(in_file=input_file_path, out_file=out_file_path)
    
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        err_stat = ResultInfo.RE
    
    if err_stat == ResultInfo.AC:
        score = get_score_from_stdout(proc.stdout)
    
    if err_stat == ResultInfo.RE or err_stat == ResultInfo.TLE:
        if err_stat == ResultInfo.RE:
            score = "RE"
            msg = "RE "
        else:
            score = "TLE"
            msg = "TLE"
        print(msg + " in ", basename)
    
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
