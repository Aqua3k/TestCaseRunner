class BaseException(Exception):
    """ライブラリ内で使う例外の基底クラス"""
    pass

class InternalError(BaseException):
    """ライブラリ内部のバグ"""
    def __init__(self, message) -> None:
        super().__init__(message)

class InvalidPathException(BaseException):
    """与えられたパスが正しくない場合の例外"""
    def __init__(self, message) -> None:
        super().__init__(message)

class NoTestcaseFileException(BaseException):
    """テストケースファイルが1つもない場合の例外"""
    def __init__(self, message) -> None:
        super().__init__(message)
