import sys
import glob
import time
import os
import shutil
import subprocess

from mysrc.settings import *
from mysrc.MyLib import *
from mysrc.HTMLtemplate import *
from mysrc.Output import InitAll, MakeAllResult

inFile = "in.txt"
outFile = "out.txt"
nextInputFileName = None #次に実行するケースの名前

def GetScoreFromStandardOutput(string: str) -> int:
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

def EndProcess():
    """プログラム終了の処理"""
    time.sleep(3) # コマンド実行の関係で少し待機させる
    if os.path.isfile(inFile): os.remove(inFile)
    if os.path.isfile(outFile): os.remove(outFile)

def ExacProg() -> ResultInfo:
    """プログラムを実行して結果を返す
    
    Returns:
        ResultInfo: 実行結果の情報
    """
    t_start = time.time()
    name = os.path.basename(nextInputFileName)
    
    score, errStatus, stdOut = ExacCommand(name)

    t_end = time.time()

    lis = []
    # TODO: デバッグ用の情報を取得する

    # 標準出力をファイル出力
    outFileName = "stdout" + name
    path = os.path.join(resultFilePath, outFileName)
    with open(path, mode='w') as f:
        f.write(stdOut)

    #Pythonは自動でimportガードがついてるので一度モジュールを削除する
    if 'main' in sys.modules: del sys.modules["main"]

    return ResultInfo(name, score, t_end-t_start, errStatus, stdOut, lis)

def ExacCommand(name: str):
    """プログラムを実行する
    
    Args:
        name(str): 実行対象の入力ファイルの名前
    
    Returns:
        int, int, str: 得点, 結果のステータス, 標準出力
    """
    timeLimit = 2
    errStatus = ResultInfo.AC
    score = ""
    stdOut = ""

    cmd = command.format(inFile=inFile, outFile=outFile)

    #inファイルコピー
    path = os.path.join(inputFilePath, name)
    shutil.copy(path, inFile)
    
    try:
        #実行
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,\
             shell=True, text=True, timeout=timeLimit)

        if r.returncode != 0: errStatus = ResultInfo.RE
        stdOut = r.stdout
        score = GetScoreFromStandardOutput(r.stdout)

        #outをコピー
        path = os.path.join(resultFilePath, name)
        shutil.copy(outFile, path)

    except: #ここに入るのはTLEしたときだけのはず
        errStatus = ResultInfo.TLE
    
    if errStatus == ResultInfo.RE or errStatus == ResultInfo.TLE:
        if errStatus == ResultInfo.RE:
            score = "RE"
            msg = "RE "
        else:
            score = "TLE"
            msg = "TLE"
        print(msg + " in ", name)
    
    return score, errStatus, stdOut

def main() -> None:
    """main処理"""
    global nextInputFileName
    resultAll = []
    InitAll()
    for filename in glob.glob(os.path.join(inputFilePath, "*")):
        nextInputFileName = filename
        result = ExacProg()
        resultAll.append(result)
    MakeAllResult(resultAll)
    EndProcess()

if __name__ == "__main__":
    main()
