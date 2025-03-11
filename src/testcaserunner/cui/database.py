from abc import ABC, abstractmethod

from ..parallel_executor import RunnerLog, LogManager

class Result:
    def __init__(self):
        pass

class ResultTable:
    def __init__(self, log: RunnerLog):
        self.log = log

    def add_result(self, result: Result):
        pass

class Singleton(ABC):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[cls] = instance
            if hasattr(instance, "first_init"):  # 初回だけ実行
                instance.first_init()
        return cls._instances[cls]

    @abstractmethod
    def first_init(self):
        pass

class LogStats:
    """RunnerLogをラップしたクラス
    ログの統計情報を提供する
    """
    def __init__(self, log: RunnerLog):
        self.log = log
    
    def analyze(self):
        """ログを解析する"""
        pass

    def get_stats(self):
        """統計情報を取得する"""
        pass

class Database(Singleton):
    def first_init(self):
        log_manager = LogManager()
        runner_logs = log_manager.get_log()
        self.logs = [LogStats(log) for log in runner_logs]

    def sort(self, key):
        """データをソートする"""
        pass

    def delete(self, index):
        """データを削除する"""
        pass

    def compare(self, index1, index2):
        """データを比較する"""
        pass
