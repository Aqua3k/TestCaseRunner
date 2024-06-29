class CustomException(Exception):
    """ライブラリ内で使う例外の基底クラス"""
    pass

class InvalidPathException(CustomException):
    """与えられたパスが正しくない場合の例外"""
    def __init__(self, message):
        super().__init__(message)

class NoTestcaseFileException(CustomException):
    """テストケースファイルが1つもない場合の例外"""
    def __init__(self, message):
        super().__init__(message)

# 公開するメンバーを制御する
__all__ = [
    "InvalidPathException",
    "NoTestcaseFileException",
]
