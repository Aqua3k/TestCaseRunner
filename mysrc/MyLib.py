import copy
from typing import Any

class ResultInfo:
    """実行結果の情報管理用のクラス"""
    AC = 0
    RE = 1
    TLE = 2
    def __init__(self, name: str, score: str, time: float, errStatus: int, stdOut: str, otherList: list[Any]):
        self.name      = name
        self.score     = score
        self.time      = time
        self.errStatus = errStatus
        self.otherList = copy.deepcopy(otherList)
        self.stdOut    = stdOut
    def GetMember(self) -> list[str]:
        """結果を配列にする"""
        ret = [self.name, self.score, self.time] + copy.deepcopy(self.otherList)
        return ret
    def __lt__(self, other) -> bool:
        """__lt__を定義しておくとクラスのままソートが可能になる"""
        return self.name < other.name

