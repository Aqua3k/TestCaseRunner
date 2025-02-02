
from typing import Callable

from .executor import ParallelExecutor
from .log_builder import LogBuilder
from .testcase import TestCase, TestCaseResult

def start_executor(
        testcase_handler: Callable[[TestCase], TestCaseResult|None],
        input_file_path: str,
        log_folder_name: str,
        repeat_count: int,
        copy_target_files: list[str],
        parallel_processing_method: str,
        time_limit: int|float|None,
        ):
    runner = ParallelExecutor(
        testcase_handler,
        input_file_path,
        log_folder_name,
        repeat_count,
        copy_target_files,
        parallel_processing_method,
        time_limit,
    )
    result = runner.start()
    builder = LogBuilder(result, log_folder_name)
    builder.build()
    return builder.get_log()
