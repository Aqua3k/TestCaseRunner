import glob
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future, Executor
from typing import Callable
import time
import hashlib
import json
from enum import IntEnum, auto
from collections import defaultdict
from typing import Any
import shutil
from pathlib import Path
import datetime

from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from .runner_defines import RunnerMetadata, TestCase, TestCaseResult, ResultStatus, NoTestcaseFileException, InvalidPathException
from .runner_logger import RunnerLogger

class RunnerSettings:
    stdout_dir_path = "stdout"
    stderr_dir_path = "stderr"
    log_dir_path = "log"
    logger = RunnerLogger("RunnerSettings")
    def __init__(
        self,
        input_file_path: str,
        repeat_count: int,
        measure_time: bool,
        copy_target_files: list[str],
        parallel_processing_method: str,
        stdout_file_output: bool,
        stderr_file_output: bool,
        log_folder_name: str | None,
        debug: bool,
    ) -> None:
        self.debug = debug
        self.input_file_path: str = input_file_path
        self.repeat_count: int = repeat_count
        self.measure_time: bool = measure_time
        self.copy_target_files: list[str] = copy_target_files
        self.parallel_processing_method: str = parallel_processing_method
        self.stdout_file_output: bool = stdout_file_output
        self.stderr_file_output: bool = stderr_file_output
        self.datetime = datetime.datetime.now()
        self.log_folder_name: str = self.get_log_file_path(log_folder_name)

        if repeat_count <= 0:
            raise ValueError("引数repeat_countの値は1以上の整数である必要があります。")

        if not Path(self.input_file_path).is_dir():
            raise InvalidPathException(f"テストケースファイルへのパス{self.input_file_path}は無効なパスです。")

        if self.log_dir_path not in glob.glob("*"):
            os.mkdir(self.log_dir_path)
        os.mkdir(self.log_folder_name)
        self.stdout_log_path = os.path.join(self.log_folder_name, self.stdout_dir_path)
        os.mkdir(self.stdout_log_path)
        self.stderr_log_path = os.path.join(self.log_folder_name, self.stderr_dir_path)
        os.mkdir(self.stderr_log_path)
        self.input_file_copy_path = os.path.join(self.log_folder_name, "in")
        shutil.copytree(self.input_file_path, self.input_file_copy_path)
        self.fig_dir_path = os.path.join(self.log_folder_name, "fig")
        os.mkdir(self.fig_dir_path)
        for file in self.copy_target_files:
            file_path = Path(file)
            if file_path.is_file():
                shutil.copy(file, self.log_folder_name)
            elif file_path.is_dir():
                self.logger.warning(f"{file}はディレクトリパスです。コピーは行いません。")
            else:
                self.logger.warning(f"{file}が見つかりません。コピーは行いません。")

    @logger.function_tracer
    def get_log_file_path(self, log_folder_name: str | None) -> str:
        if log_folder_name is None:
            log_folder_name = str(self.datetime.strftime('%Y%m%d%H%M%S'))
        name = os.path.join(self.log_dir_path, log_folder_name)
        i = 1
        while os.path.exists(name):
            name = os.path.join(self.log_dir_path, f"{log_folder_name}-{i}")
            i += 1
        return name

class TestCaseRunner:
    logger = RunnerLogger("TestCaseRunner")
    def __init__(self,
                 handler: Callable[[TestCase], TestCaseResult],
                 setting: RunnerSettings,
                 ) -> None:
        self.settings = setting
        if self.settings.debug:
            self.logger.enable_debug_mode()
        self.input_file_path = self.settings.input_file_copy_path
        self.handler = handler
    
    @logger.function_tracer
    def make_testcases(self, files: list[str]) -> list[TestCase]:
        test_cases = []
        testcase_index = 0
        for input_file in sorted(files):
            for rep in range(self.settings.repeat_count):
                if self.settings.repeat_count != 1:
                    name, extension = os.path.splitext(os.path.basename(input_file))
                    basename = f"{name}_{rep+1}{extension}"
                else:
                    basename = os.path.basename(input_file)
                stdout_file = os.path.join(self.settings.stdout_log_path, basename)
                stderr_file = os.path.join(self.settings.stderr_log_path, basename)
                testcase_name = os.path.basename(input_file)
                testcase = TestCase(testcase_name, input_file, stdout_file, stderr_file, testcase_index)
                test_cases.append(testcase)
                testcase_index += 1
        return test_cases

    @logger.function_tracer
    def run(self) -> list[tuple[TestCase, TestCaseResult]]:
        futures:list[Future] = []
        test_cases: list[TestCase] = []
        files = glob.glob(os.path.join(self.input_file_path, "*"))
        if len(files) == 0:
            raise NoTestcaseFileException(f"{self.input_file_path}ディレクトリにファイルが1つもありません。")
        test_cases = self.make_testcases(files)
        executor_class: type[Executor] | None = None
        if self.settings.parallel_processing_method.lower() == "process":
            parallel = True
            executor_class = ProcessPoolExecutor
        elif self.settings.parallel_processing_method.lower() == "thread":
            parallel = True
            executor_class = ThreadPoolExecutor
        elif self.settings.parallel_processing_method.lower() == "single":
            parallel = False
        else:
            raise ValueError("引数parallel_processing_methodの値が不正です。")

        self.logger.debug("start testcase run process.")
        results: list[tuple[TestCase, TestCaseResult]] = []
        if parallel:
            self.logger.debug("paralle")
            assert executor_class is not None, "変数executor_classがNoneだよ"
            with tqdm(total=len(test_cases)) as progress:
                with executor_class() as executor:
                    for testcase in test_cases:
                        future = executor.submit(self.run_testcase, testcase)
                        future.add_done_callback(lambda p: progress.update())
                        futures.append(future)
                
                    for future in futures:
                        results.append(future.result())
        else:
            self.logger.debug("single")
            for testcase in tqdm(test_cases):
                result = self.run_testcase(testcase)
                results.append(result)
        
        return results
    
    def run_testcase(self, testcase: TestCase) -> tuple[TestCase, TestCaseResult]:
        start_time = time.time()
        try:
            test_result: TestCaseResult = self.handler(testcase)
        except Exception as e:
            self.logger.warning(f"テストケース{os.path.basename(testcase.input_file_path)}において、\
                引数で渡された関数の中で例外が発生しました。\n{str(e)}")
            test_result = TestCaseResult(error_status=ResultStatus.IE, stderr=str(e))
        erapsed_time = time.time() - start_time
        if self.settings.measure_time:
            test_result.attribute["time"] = erapsed_time
        if self.settings.stdout_file_output:
            with open(testcase.stdout_file_path, mode='w') as f:
                f.write(test_result.stdout)
        if self.settings.stderr_file_output:
            with open(testcase.stderr_file_path, mode='w') as f:
                f.write(test_result.stderr)
        return testcase, test_result

class HtmlColumnType(IntEnum):
    """HTMLファイルのcolumnの情報
    """
    URL = auto()
    STATUS = auto()
    TEXT = auto()
    METADATA = auto()

class RunnerLog:
    def __init__(self, contents: dict, metadata: dict) -> None:
        self._df = pd.DataFrame(contents)
        self._metadata = metadata
    
    @property
    def df(self) -> pd.DataFrame:
        return self._df

    @property
    def metadata(self) -> dict:
        return self._metadata
    
    def drop(self, column: str) -> None:
        self._df = self._df.drop(columns=[column], errors='ignore')
        self._metadata["attributes"].pop(column, None)
    
    def _df_at(self, column: str, row: int) -> Any:
        return self._df.at[str(row), column]

class RunnerLogManager:
    js_file_path = "js"
    infile_col = "in"
    stdout_col = "stdout"
    stderr_col = "stderr"
    infilename_col = "testcase"
    status_col = "status"
    input_hash_col = "input_hash"
    stdout_hash_col = "stdout_hash"
    stderr_hash_col = "stderr_hash"

    logger = RunnerLogger("RunnerLogManager")
    def __init__(self, results: list[tuple[TestCase, TestCaseResult]], settings: RunnerSettings) -> None:
        self.settings = settings
        if settings.debug:
            self.logger.enable_debug_mode()
        self.results = results
        self.attributes: dict[str, HtmlColumnType] = {
            self.infilename_col: HtmlColumnType.TEXT,
            self.input_hash_col: HtmlColumnType.METADATA,
            self.stdout_hash_col: HtmlColumnType.METADATA,
            self.stderr_hash_col: HtmlColumnType.METADATA,
            self.infile_col: HtmlColumnType.URL,
            self.stdout_col: HtmlColumnType.URL,
            self.stderr_col: HtmlColumnType.URL,
            self.status_col: HtmlColumnType.STATUS,
        }
        self.make_json_file()
        self.make_figure()
        self.base_dir = os.path.split(__file__)[0]
    
    @logger.function_tracer
    def get_log(self) -> RunnerLog:
        return self.runner_log

    json_file_name = "result.json"
    @logger.function_tracer
    def add_attribute(self, key: str, type: HtmlColumnType) -> None:
        self.attributes[key] = type

    histgram_fig_name = 'histgram.png'
    heatmap_fig_name = 'heatmap.png'
    @logger.function_tracer
    def make_figure(self) -> None:
        # ヒストグラムを描画
        self.runner_log.df.hist()
        plt.savefig(os.path.join(self.settings.fig_dir_path, self.histgram_fig_name))
        plt.close()

        # 相関係数のヒートマップ
        corr = self.runner_log.df.corr(numeric_only=True)
        heatmap = sns.heatmap(corr, annot=True)
        heatmap.set_title('Correlation Coefficient Heatmap')
        plt.savefig(os.path.join(self.settings.fig_dir_path, self.heatmap_fig_name))

    @logger.function_tracer
    def make_json_file(self) -> None:
        testcases: list[TestCase] = []
        results: list[TestCaseResult] = []
        for t, r in self.results:
            testcases.append(t)
            results.append(r)

        attributes = dict() # setだと順番が保持されないのでdictにする
        for test_result in results:
            for attribute in test_result.attribute.keys():
                attributes[attribute] = ""
        user_attributes = list(attributes.keys())

        for key in user_attributes:
            self.add_attribute(key, HtmlColumnType.TEXT)

        contents: defaultdict[str, list[Any]] = defaultdict(list)
        for testcase, result in zip(testcases, results):
            contents[self.infilename_col].append(os.path.basename(testcase.input_file_path))
            contents[self.input_hash_col].append(f"{os.path.basename(testcase.input_file_path)}.{self.get_file_hash(testcase.input_file_path)}")
            contents[self.stdout_hash_col].append(f"{self.get_file_hash(testcase.stdout_file_path)}")
            contents[self.stderr_hash_col].append(f"{self.get_file_hash(testcase.stderr_file_path)}")
            contents[self.infile_col].append(os.path.relpath(testcase.input_file_path, self.settings.log_folder_name))
            contents[self.stdout_col].append(os.path.relpath(testcase.stdout_file_path, self.settings.log_folder_name))
            contents[self.stderr_col].append(os.path.relpath(testcase.stderr_file_path, self.settings.log_folder_name))
            contents[self.status_col].append(result.error_status)
            for key in user_attributes:
                value = result.attribute[key] if key in result.attribute else None
                contents[key].append(value)
        
        # jsonデータをそろえるため一度DataFrameにしてからjsonに直す
        contents = json.loads(pd.DataFrame(contents).to_json())
        
        metadata = {
            "library_name": RunnerMetadata.LIB_NAME,
            "created_date": self.settings.datetime.strftime("%Y/%m/%d %H:%M"),
            "testcase_num": len(testcases),
            "attributes": self.attributes,
        }
        self.json_file = {
            "contents": contents,
            "metadata": metadata,
        }
        self.runner_log: RunnerLog = RunnerLog(contents, metadata)
        json_file_path = os.path.join(self.settings.log_folder_name, self.json_file_name)
        with open(json_file_path, 'w') as f:
            json.dump(self.json_file, f, indent=2)
    
    @logger.function_tracer
    def get_file_hash(self, path: str) -> str:
        if os.path.exists(path):
            return self.calculate_file_hash(path)
        else:
            return "" #ファイルが開けないときは空文字にしておく

    @logger.function_tracer
    def calculate_file_hash(self, file_path: str) -> str:
        hash_obj = hashlib.new('sha256')
        with open(file_path, 'rb') as file:
            while chunk := file.read(4096):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

from .html_parser import HtmlParser # 循環import対策

def run(
        handler: Callable[[TestCase], TestCaseResult],
        input_file_path: str,
        repeat_count: int = 1,
        measure_time: bool = True,
        copy_target_files: list[str] = [],
        parallel_processing_method: str = "process",
        stdout_file_output: bool = True,
        stderr_file_output: bool = True,
        log_folder_name: str | None = None,
        _debug: bool = False,
        ) -> None:
    """ランナーを実行する

    Args:
        handler (Callable[[TestCase], TestCaseResult]): 並列実行する関数
        input_file_path (str): 入力ファイル群が置いてあるディレクトリへのパス
        repeat_count (int, optional): それぞれのテストケースを何回実行するか. Defaults to 1.
        measure_time (bool, optional): 処理時間を計測して記録するかどうか. Defaults to True.
        copy_target_files (list[str], optional): コピーしたいファイルパスのリスト. Defaults to [].
        parallel_processing_method (str, optional): 並列化の方法(プロセスかスレッドか). Defaults to 'process'.
        stdout_file_output (bool, optional): 標準出力をファイルで保存するかどうか. Defaults to True.
        stderr_file_output (bool, optional): 標準エラー出力をファイルで保存するかどうか. Defaults to True.
        log_folder_name (str | None, optional): ログフォルダの名前(Noneだと現在時刻'YYYYMMDDHHMMSS'形式になる). Defaults to None.
    """
    setting = RunnerSettings(
        input_file_path,
        repeat_count,
        measure_time,
        copy_target_files,
        parallel_processing_method,
        stdout_file_output,
        stderr_file_output,
        log_folder_name,
        _debug,
    )
    runner = TestCaseRunner(handler, setting)
    result = runner.run()
    log_manager = RunnerLogManager(result, setting)
    html_parser = HtmlParser(log_manager.get_log(), setting.log_folder_name, setting.debug)
    html_parser.make_html()

# 公開するメンバーを制御する
__all__ = [
    "run",
]
