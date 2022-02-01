import copy
from typing import Any

class FileControl:
    """入力させるファイルの情報管理"""
    def __init__(self):
        self.fileName = ""
        self.fileContents = ""
    def SetFileName(self, name: str) -> str:
        """ファイルの名前をSet"""
        self.fileName = name
    def GetFileName(self) -> str:
        """現在Setしてあるファイルの名前を取得"""
        return self.fileName
    def SetFileContents(self: str) -> None:
        """ファイルの中身をSetする"""
        with open(self.fileName) as f:
            self.fileContents = [s.strip() for s in f.readlines()][::-1]
    def GetFileContentsLine(self) -> str:
        """ファイルの中身を1行分Get(inputと同等の動作)"""
        return self.fileContents.pop()

class ResultInfo:
    """実行結果の情報管理用のクラス"""
    def __init__(self, name: str, score: str, time: float, errFlg: bool, errMsg: str, otherList: list[Any]):
        self.name      = name
        self.score     = score
        self.time      = time
        self.errFlg    = errFlg
        self.errMsg    = errMsg
        self.otherList = copy.deepcopy(otherList)
    def GetMember(self) -> list[str]:
        """結果を配列にする"""
        ret = [self.name, self.score, self.time] + copy.deepcopy(self.otherList)
        return ret
    def __lt__(self, other) -> bool:
        """__lt__を定義しておくとクラスのままソートが可能になる"""
        return self.name < other.name

