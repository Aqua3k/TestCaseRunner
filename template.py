HTMLLinkStr = '<a href="{path}">{string}</a><br>'

#後でcssの体裁整えるときのため削除じゃなくてコメントアウト
#cssLink   = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/kognise/water.css@latest/dist/light.min.css">'
cssLink    = '<link rel="stylesheet" href="SortTable.css">'
scriptLink = '<script type="text/javascript" src="Table.js"></script>'

TableHeading     = '<table id="sortTable">{body}</table>'
TableLine        = '<tr>{text}</tr>'
TableCellHeading = '<th cmanSortBtn>{text}</th>'
TableCell        = '<td>{text}</td>'
TableColoredCell = '<th bgcolor={color}>{text}</th>'

HTMLText = '''
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>
'''

import copy
from typing import Any
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
