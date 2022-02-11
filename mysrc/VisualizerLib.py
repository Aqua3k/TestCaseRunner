import subprocess
import sys
import shutil
import os

from mysrc.settings import *

inFileName  = "in.txt"
outFileName = "out.txt"
cmd = 'cargo run --release --bin vis in.txt out.txt'

def GetScoreFromVisualizer(fileName: str) -> int:
    """ビジュアライザを走らせて得点を取得する"""
    CopyFile(fileName)
    for result in command(cmd): pass
    score = GetScoreFromStandardOutput(result)
    DeleteFile()
    return score

def CopyFile(fileName: str) -> None:
    """inファイルとoutファイルをコピー"""
    path = os.path.join(inputFilePath, fileName)
    shutil.copy(path, inFileName)

    path = os.path.join(resultFilePath, fileName)
    shutil.copy(path, outFileName)

def DeleteFile() -> None:
    """inファイルとoutファイルを削除"""
    os.remove(inFileName)
    os.remove(outFileName)

def command(cmd : str) -> str:
    """コマンドを実行"""
    try:
        result = subprocess.run(cmd, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        for line in result.stdout.splitlines():
            yield line
    except subprocess.CalledProcessError:
        print('Command [' + cmd + '] was failed.', file=sys.stderr)

def GetScoreFromStandardOutput(string: str) -> int:
    """標準出力から得点を取り出す"""
    s = ""
    for t in string:
        if "0" <= t <= "9":
            s += t
    return int(s)
