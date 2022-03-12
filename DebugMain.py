import sys
import glob
import time
import os
import shutil
import subprocess
from typing import Any

from mysrc.settings import *
from mysrc.MyLib import *
from mysrc.HTMLtemplate import *
from mysrc.Output import InitAll, MakeAllResult

####################################

inFile = "in.txt"
outFile = "out.txt"

def DebugPrint(*arg: Any, **keys: Any) -> None:
    """Debug用の出力"""
    f = open(os.path.join(resultFilePath, os.path.basename(File.GetFileName())), 'a')
    print(*arg, **keys, file=f)
    f.close()

def DebugInput() -> str:
    """Debug用の入力"""
    return str(File.GetFileContentsLine())

####################################

def GetScoreFromStandardOutput(string: str) -> int:
    """標準出力から得点を取り出す"""
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
    time.sleep(3) # コマンド実行の関係で少し待機させる
    if os.path.isfile(inFile): os.remove(inFile)
    if os.path.isfile(outFile): os.remove(outFile)

####################################
def ExacProg() -> ResultInfo:
    """プログラムを実行して結果を返す"""
    t_start = time.time()
    timeLimit = 2
    errMessage = ""
    name = os.path.basename(File.GetFileName())
    errStatus = ResultInfo.AC
    score = ""

    cmd = command.format(myCmd=myCmd, inFile=inFile, outFile=outFile)

    #inファイルコピー
    path = os.path.join(inputFilePath, name)
    shutil.copy(path, inFile)
    
    try:
        #実行
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,\
             shell=True, text=True, timeout=timeLimit)

        if r.returncode != 0: errStatus = ResultInfo.RE
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
            errMsg = r.stdout
        else:
            score = "TLE"
            msg = "TLE"
            errMsg = "Time Limit Exceeded."
        print(msg + " in ", name)
        DebugPrint("------------------------------")
        DebugPrint(errMsg)
    
    t_end = time.time()

    lis = []
    # TODO: デバッグ用の情報を取得する

    #Pythonは自動でimportガードがついてるので一度モジュールを削除する
    if 'main' in sys.modules: del sys.modules["main"]

    return ResultInfo(name, score, t_end-t_start, errStatus, errMessage, lis)

####################################
#main

File = None
def main() -> None:
    global File
    File = FileControl()
    resultAll = []
    InitAll()
    for filename in glob.glob(os.path.join(inputFilePath, "*")):
        File.SetFileName(filename)
        File.SetFileContents()
        result = ExacProg()
        resultAll.append(result)
    MakeAllResult(resultAll)
    EndProcess()

if __name__ == "__main__":
    main()
