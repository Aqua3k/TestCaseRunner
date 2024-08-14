import glob
import os
import shutil
from pathlib import Path
import datetime
from dataclasses import dataclass

from .runner_defines import NoTestcaseFileException, InvalidPathException
from .testccase_executor import TestcaseExecutor, ProcessTestcaseExecutor, ThreadTestcaseExecutor, SingleTestcaseExecutor
from .logger import RunnerLogger

@dataclass
class RunnerSettings:
    input_file_path: str
    repeat_count: int
    copy_target_files: list[str]
    parallel_processing_method: str
    stdout_file_output: bool
    stderr_file_output: bool
    debug: bool
    
    def __post_init__(self) -> None:
        self.logger = RunnerLogger("RunnerSettings")
        self.init_parameters()
        self.init_folders()

    def get_log_file_path(self) -> str:
        log_name = str(datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        name = os.path.join(self.log_dir_path, log_name)
        i = 1
        while os.path.exists(name):
            name = os.path.join(self.log_dir_path, f"{log_name}-{i}")
            i += 1
        return name

    def make_folder(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)

    def copy_folder(self, src: str, dst: str) -> None:
        shutil.copytree(src, dst)

    def copy_file(self, src: str, dst: str) -> None:
        shutil.copy(src, dst)
    
    def copy_files(self) -> None:
        for file in self.copy_target_files:
            file_path = Path(file)
            if file_path.is_file():
                self.copy_file(file, self.log_folder_name)
            elif file_path.is_dir():
                self.logger.warning(f"{file}はディレクトリパスです。コピーは行いません。")
            else:
                self.logger.warning(f"{file}が見つかりません。コピーは行いません。")

    def init_folders(self) -> None:
        self.make_folder(self.log_dir_path)
        self.make_folder(self.log_folder_name)
        self.make_folder(self.stdout_log_path)
        self.make_folder(self.stderr_log_path)
        self.make_folder(self.stdout_log_path)
        self.make_folder(self.fig_dir_path)
        self.copy_folder(self.input_file_path, self.input_file_copy_path)
        self.copy_files()

    def get_executor(self) -> type[TestcaseExecutor]:
        match self.parallel_processing_method.lower():
            case "process":
                return ProcessTestcaseExecutor
            case "thread":
                return ThreadTestcaseExecutor
            case "single":
                return SingleTestcaseExecutor
            case _:
                raise ValueError("引数parallel_processing_methodの値が不正です。")

    def init_parameters(self) -> None:
        self.log_dir_path = "log"
        self.log_folder_name = self.get_log_file_path()
        self.stdout_log_path = os.path.join(self.log_folder_name, "stdout")
        self.stderr_log_path = os.path.join(self.log_folder_name, "stderr")
        self.input_file_copy_path = os.path.join(self.log_folder_name, "in")
        self.fig_dir_path = os.path.join(self.log_folder_name, "fig")
        self.Executor = self.get_executor()

        if self.repeat_count <= 0 or type(self.repeat_count) is not int:
            raise ValueError("引数repeat_countの値は1以上の整数である必要があります。")
        if not Path(self.input_file_path).is_dir():
            raise InvalidPathException(f"テストケースファイルへのパス{self.input_file_path}は無効なパスです。")
        if len(glob.glob(os.path.join(self.input_file_path, "*"))) == 0:
            raise NoTestcaseFileException(f"{self.input_file_path}ディレクトリにファイルが1つもありません。")
