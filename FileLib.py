class FileControl:
    def __init__(self):
        self.fileName = ""
        self.fileContents = ""
    def SetFileName(self, name: str) -> str:
        self.fileName = name
    def GetFileName(self) -> str:
        return self.fileName
    def SetFileContents(self: str) -> None:
        with open(self.fileName) as f:
            self.fileContents = [s.strip() for s in f.readlines()][::-1]
    def GetFileContentsLine(self) -> str:
        """ファイルの中身を1行分Get(inputと同等の動作)"""
        return self.fileContents.pop()
