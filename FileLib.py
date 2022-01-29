import DebugLib as dl

fileName = ""
def SetFileName(name: str) -> None:
    """現在の実行中の入力ファイルの名前をセット"""
    global fileName
    fileName = name
def GetFileName() -> str:
    """現在の実行中の入力ファイルの名前をゲット"""
    global fileName
    return fileName

fileContents = ""
def SetFileContents() -> None:
    """ファイルの中身をセットする"""
    global fileContents
    path = GetFileName()
    with open(path) as f:
        fileContents = [s.strip() for s in f.readlines()][::-1]
