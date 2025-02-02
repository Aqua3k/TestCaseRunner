import os
import json
import glob
import datetime

from jsonschema import ValidationError, validate

from ..debug import Logger, call_logger
from ..defines import Metadata
from ..defines import InternalError
from .log import RunnerLog

class LogManager:
    def __init__(self, path: str="log") -> None:
        self.logs: list[RunnerLog] = []
        pattern = os.path.join(path, "**", "*.json")
        for file in glob.glob(pattern, recursive=True):
            self.load_log(file)
    
    @call_logger
    def is_valid(self, data: dict) -> bool:
        try:
            schema_path = os.path.join(os.path.split(__file__)[0], "schemas", "result_schema.json")
            with open(schema_path, 'r') as f:
                schema: dict = json.load(f)
            validate(instance=data, schema=schema)
        except ValidationError as e:
            Logger.info("json schema validation error.")
            return False

        metadata: dict|None = data.get("metadata")
        if metadata is None:
           raise InternalError("変数metadataがNoneだよ。")
        libname = metadata.get("library_name")
        if libname != Metadata.LIBRARY_NAME:
            return False # ライブラリ名が入っていなかったらFalse

        return True

    @call_logger
    def load_log(self, file: str) -> None:
        try:
            with open(file, 'r') as f:
                loaded_data: dict = json.load(f)
        except:
            # ロードできなければ処理しない
            Logger.info(f"{file} のロードでエラーが起きました。")
            return

        if not self.is_valid(loaded_data):
            Logger.info(f"{file} は正しいデータではありませんでした。")
            return
        
        contents = loaded_data.get("contents")
        metadata = loaded_data.get("metadata")
        if contents is None:
            raise InternalError("contentsがNoneだよ")
        if type(contents) is not dict:
            raise InternalError("contentsがdict型ではないよ")
        if metadata is None:
            raise InternalError("metadataがNoneだよ")
        if type(metadata) is dict:
            raise InternalError("metadataがNonedict型ではないよ")

        folder = os.path.split(file)[0]
        self.logs.append(RunnerLog(contents, metadata, os.path.split(folder)[1]))
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
