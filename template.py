HTMLLinkStr = '<a href="{path}">{string}</a><br>'

cssLink = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/kognise/water.css@latest/dist/light.min.css">'

Table = '<table border="{border}">{body}</table>'
TableBody = '<tr><th>{text1}</th><th bgcolor={color}>{text2}</th><th>{text3}</th></tr>'
TableLine = '<tr>{text}</tr>'
TableCell = '<th>{text}</th>'

HTMLFont = '<font size="{size}" >{text}</font>'

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
class ResultInfo:
    def __init__(self, name, score, time, errFlg, errMsg, otherList):
        self.name      = name
        self.score     = score
        self.time      = time
        self.errFlg    = errFlg
        self.errMsg    = errMsg
        self.otherList = copy.deepcopy(otherList)
    def GetMember(self):
        """結果を配列にする"""
        ret = [self.name, self.score, self.time] + copy.deepcopy(self.otherList)
        return ret
    def __lt__(self, other) -> bool:
        """__lt__を定義しておくとクラスのままソートが可能になる"""
        return self.name < other.name
