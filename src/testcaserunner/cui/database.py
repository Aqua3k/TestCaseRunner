from abc import ABC, abstractmethod
from typing import Any

from ..parallel_executor import RunnerLog, LogManager
from ..debug import Logger

Data = int|float|str

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
        self.df = log.get_dataframe()
        self.metadata = log.get_metadata()
    
    def get(self, attribute: str) -> Data|None:
        """指定した属性の値を取得する"""
        if attribute in self.df.columns:
            data = self.df[attribute]
            if isinstance(data, (int, float, str)):
                return data
            else:
                Logger.info(f"データ型が不正です: {type(data)}")
                return None
        return None
    
    def analyze(self):
        """ログを解析する"""
        pass

    def get_stats(self) -> dict[str, Any]:
        """統計情報を取得する"""
        return {
            "created_date": self.metadata.created_date,
            "attributes": self.metadata.attributes,
        }

class Database(Singleton):
    def first_init(self):
        self.attributes: list[str] = []
        self.__load_logs()
    
    def __load_logs(self) -> None:
        """データをロードする"""
        log_manager = LogManager()
        runner_logs = log_manager.get_log()
        self.attributes: list[str] = []
        atts: set[str] = set()
        for log in runner_logs:
            for att in log.get_metadata().attributes:
                atts.add(att)
        self.attributes = list(atts)
        self.logs = [LogStats(log) for log in runner_logs]
        print(self.attributes)
    
    def sort(self, key):
        """データをソートする"""
        pass

    def delete(self, index):
        """データを削除する"""
        pass

    def compare(self, index1, index2):
        """データを比較する"""
        pass
