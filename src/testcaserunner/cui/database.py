from abc import ABC, abstractmethod
from typing import Any, Generator
from enum import Enum, auto
import os

import pandas as pd

from ..parallel_executor import RunnerLog, LogManager, Metadata
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

class EvaluationMethod(Enum):
    MEAN = auto()
    MEDIAN = auto()
    MIN = auto()
    MAX = auto()

class LogStats:
    """RunnerLogをラップしたクラス
    ログの統計情報を提供する
    """
    def __init__(self, log: RunnerLog):
        self.df = log.get_dataframe()
        self.metadata = log.get_metadata()
    
    def __evaluate(self, series: pd.Series, method: EvaluationMethod) -> Data|None:
        """指定した評価方法でデータを評価する"""
        match method:
            case EvaluationMethod.MEAN:
                result = series.mean()
            case EvaluationMethod.MEDIAN:
                result = series.median()
            case EvaluationMethod.MIN:
                result = series.min()
            case EvaluationMethod.MAX:
                result = series.max()
            case _:
                Logger.info(f"評価方法が不正です: {method}")
                return None

        if isinstance(result, float):
            if result.is_integer():
                return int(result)
            else:
                return float(result)
        if isinstance(result, int):
            return int(result)
        Logger.info(f"結果の型が不正です: {type(result)}")
        return None
    
    def get(self, attribute: str, method: EvaluationMethod=EvaluationMethod.MEAN) -> Data|None:
        """指定した属性の値を取得する"""
        if attribute in self.df.columns:
            series = self.df[attribute]
            if isinstance(series, pd.Series):
                return self.__evaluate(series, method)
            else:
                Logger.info(f"データ型が不正です: {type(series)}")
                return None
        Logger.info(f"属性が存在しません: {attribute}")
        return None
    
    def get_metadata(self) -> Metadata:
        return self.metadata
    
    def analyze(self):
        """ログを解析する"""
        pass

    def get_stats(self) -> dict[str, Any]:
        """統計情報を取得する"""
        return {
            "created_date": self.metadata.created_date,
            "attributes": self.metadata.attributes,
        }
    
    def get_html_path(self) -> str:
        """ログファイルまでの絶対パスを取得する

        Returns:
            str: ログフォルダまでの絶対パス
        """
        path = os.path.join(self.metadata.log_folder_path, "result.html")
        return os.path.abspath(path)

class Database(Singleton):
    def first_init(self):
        self.attributes: list[str] = []
        self.__load_logs()
    
    def __load_logs(self) -> None:
        """データをロードする"""
        log_manager = LogManager()
        runner_logs = log_manager.get_log()
        self.attributes: list[str] = []
        atts: dict[str, None] = {}
        for log in runner_logs:
            for att in log.get_metadata().attributes:
                atts[att] = None
        self.attributes = list(atts.keys())
        self.logs = [LogStats(log) for log in runner_logs]
    
    def sort(self, key: str):
        """データをソートする"""
        pass

    def delete(self, index: int):
        """データを削除する"""
        pass

    def compare(self, index1: int, index2: int) -> dict[str, Any]:
        """データを比較する"""
        pass

    def get_attributes(self) -> list[str]:
        """属性を取得する"""
        return self.attributes

    def iterate_logs(self) -> Generator[LogStats, None, None]:
        """logsを順番にyieldする"""
        for log in self.logs:
            yield log
