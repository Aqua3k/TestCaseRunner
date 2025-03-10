import os
import json
import glob
import datetime

from ..debug import Logger, call_logger
from ..defines import LibraryMetadata
from .log import RunnerLog

class LogManager:
    def __init__(self, path: str="log") -> None:
        self.logs: list[RunnerLog] = []
        pattern = os.path.join(path, "**", "*.json")
        for file in glob.glob(pattern, recursive=True):
            self.load_log(file)
    
    @call_logger
    def is_valid(self, contents: dict, metadata: dict) -> bool:
        libname = metadata.get("library_name")
        if libname != LibraryMetadata.LIBRARY_NAME:
            Logger.info("ライブラリ名が一致しませんでした。")
            return False # ライブラリ名が入っていなかったらFalse
        return True
    
    def _load_json(self, file: str) -> tuple[dict, dict]|None:
        try:
            with open(file, 'r') as f:
                loaded_data: dict = json.load(f)
        except FileNotFoundError:
            Logger.info(f"{file} が見つかりませんでした。")
            return None
        except json.JSONDecodeError:
            Logger.info(f"{file} のJSONデコードに失敗しました。")
            return None
        except Exception as e:
            Logger.info(f"{file} のロードでエラーが起きました: {e}")
            return None
        
        contents = loaded_data.get("contents")
        metadata = loaded_data.get("metadata")
        if contents is None:
            Logger.info(f"contentsがNoneでした。")
            return None
        if not isinstance(contents, dict):
            Logger.info(f"contentsがdict型ではありませんでした。")
            return None
        if metadata is None:
            Logger.info(f"metadataがNoneでした。")
            return None
        if not isinstance(metadata, dict):
            Logger.info(f"metadataがdict型ではありませんでした。")
            return None
        return contents, metadata

    @call_logger
    def load_log(self, file: str) -> None:
        result = self._load_json(file)
        if result is None:
            return
        contents, metadata = result
        if not self.is_valid(contents, metadata):
            Logger.info(f"{file} は正しいデータではありませんでした。")
            return
        self.logs.append(RunnerLog(contents, metadata))
        Logger.info(f"{file} を読み込みました。")
    
    @call_logger
    def get_log(self) -> list[RunnerLog]:
        return self.logs

    def get_log_file_path(self) -> str:
        log_name = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_COMPARE"
        path = os.path.join("log", log_name)
        os.makedirs(path, exist_ok=True)
        return path

    # @call_logger
    # def compare(self, log1: RunnerLog, log2: RunnerLog) -> None:
    #     folder = self.get_log_file_path()
    #     builder = DiffHtmlBuilder(os.path.join(folder, "result.html"), [log1, log2], self.debug)
    #     director = DiffDirector(builder)
    #     director.construct()
