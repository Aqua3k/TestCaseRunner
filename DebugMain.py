import sys
import glob
import time
import os
import traceback
from typing import Any

from mysrc.settings import *
from mysrc.MyLib import *
from mysrc.HTMLtemplate import *
from mysrc.Output import InitAll, MakeAllResult
from mysrc.VisualizerLib import GetScoreFromVisualizer

####################################
def DebugPrint(*arg: Any, **keys: Any) -> None:
    """Debug用の出力"""
    f = open(os.path.join(resultFilePath, os.path.basename(File.GetFileName())), 'a')
    print(*arg, **keys, file=f)
    f.close()

def DebugInput() -> str:
    """Debug用の入力"""
    return str(File.GetFileContentsLine())

####################################
def ExacProg() -> ResultInfo:
    """プログラムを実行して結果を返す"""
    t_start = time.time()
    errMessage = ""
    name = os.path.basename(File.GetFileName())
    errFlg = False
    score = ""
    try:
        import main
        main.print = DebugPrint
        main.input = DebugInput
        _score = main.main()
        if type(_score) is int or type(_score) is float:
            score = _score
        else:
            score = "None"
    except:
        errFlg = True
        print("error in ", name)
        errMessage = traceback.format_exc()
        DebugPrint("------------------------------")
        DebugPrint(errMessage)
        score = "RE"
    t_end = time.time()

    if useVisualizer and not errFlg:
        score = GetScoreFromVisualizer(name)

    lis = []
    for val in statisticsInfoArray:
        try:    cont = str(getattr(main, val))
        except: cont = "None"
        lis.append(cont)

    #Pythonは自動でimportガードがついてるので一度モジュールを削除する
    if 'main' in sys.modules: del sys.modules["main"]

    return ResultInfo(name, score, t_end-t_start, errFlg, errMessage, lis)

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

if __name__ == "__main__":
    main()
