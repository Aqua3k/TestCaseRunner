from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future, wait, Executor
from typing import Callable
from typing import Self, Optional
from abc import ABC, abstractmethod
import signal
import types
from typing import Any

from tqdm import tqdm

from .runner_defines import TestCase, TestCaseResult
from .logger import RunnerLogger

class TestcaseExecutor(ABC): # pragma: no cover
    logger = RunnerLogger("TestcaseExecutor")
    NOT_START = 0
    STARTED = 1
    SUBMITTED = 2
    FINISHED = 3
    def __init__(self, total: int):
        pass

    @abstractmethod
    def submit(self, testcase_handler: Callable[[TestCase], TestCaseResult], test_cases: list[TestCase]) -> None:
        pass

    @abstractmethod
    def wait_and_get_results(self) -> list[Optional[TestCaseResult]]:
        pass

    @abstractmethod
    def __enter__(self) -> Self:
        pass

    @abstractmethod
    def __exit__(self, exc_type: Optional[type[BaseException]], exc_val: Optional[BaseException],
                 exc_tb: Optional[BaseException]):
        pass

    def notify_catch_keyboard_interrupt(self):
        self.logger.warning("ランナーの実行をキャンセルします。")

class PoolTestcaseExecutor(TestcaseExecutor):
    def __init__(self, total: int):
        self._total = total
        self._status = self.NOT_START
        self._interrupted = False
    
    def get_executor(self) -> Executor:
        return Executor()

    def submit(self, testcase_handler: Callable[[TestCase], TestCaseResult], test_cases: list[TestCase]):
        if self._status != self.STARTED:
            raise ValueError("使い方間違ってるよ")
        self._futures:list[Future] = []
        for testcase in test_cases:
            future = self._executor.submit(testcase_handler, testcase)
            future.add_done_callback(lambda p: self._progress.update())
            self._futures.append(future)
        self._status = self.SUBMITTED
    
    def wait_and_get_results(self) -> list[Optional[TestCaseResult]]:
        results: list[Optional[TestCaseResult]] = []
        if self._status != self.SUBMITTED:
            raise ValueError("使い方間違ってるよ")
        for future in self._futures:
            while not future.done():
                if self._interrupted:
                    break
            if self._interrupted:
                result = None
            else:
                result = future.result()
            results.append(result)
        return results

    def __enter__(self) -> Self:
        self._status = self.STARTED
        self._progress = tqdm(total=self._total)
        self._executor = self.get_executor()
        signal.signal(signal.SIGINT, self.signal_handler)
        return self

    def __exit__(self, exc_type: Optional[type[BaseException]], exc_val: Optional[BaseException],
                 exc_tb: Optional[BaseException]) -> None:
        self._progress.close()
        self._executor.shutdown()
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    def signal_handler(self, signum: int, frame: None | types.FrameType) -> Any:
        self._interrupted = True
        self.notify_catch_keyboard_interrupt()

class ProcessTestcaseExecutor(PoolTestcaseExecutor):
    def get_executor(self) -> Executor:
        return ProcessPoolExecutor()

class ThreadTestcaseExecutor(PoolTestcaseExecutor):
    def get_executor(self) -> Executor:
        return ThreadPoolExecutor()

class SingleTestcaseExecutor(TestcaseExecutor):
    def __init__(self, total: int):
        self._total = total
        self._status = self.NOT_START

    def submit(self, testcase_handler: Callable[[TestCase], TestCaseResult], test_cases: list[TestCase]) -> None:
        if self._status != self.STARTED:
            raise ValueError("使い方間違ってるよ")
        self._handler = testcase_handler
        self._testcases = test_cases
        self._status = self.SUBMITTED
    
    def wait_and_get_results(self) -> list[Optional[TestCaseResult]]:
        results: list[Optional[TestCaseResult]] = []
        if self._status != self.SUBMITTED:
            raise ValueError("使い方間違ってるよ")
        try:
            for testcase in self._testcases:
                results.append(self._handler(testcase))
                self._progress.update()
        except KeyboardInterrupt:
            self.notify_catch_keyboard_interrupt()
            while len(results) < len(self._testcases):
                results.append(None)
        return results

    def __enter__(self) -> Self:
        self._status = self.STARTED
        self._progress = tqdm(total=self._total)
        return self

    def __exit__(self, exc_type: Optional[type[BaseException]], exc_val: Optional[BaseException],
                 exc_tb: Optional[BaseException]) -> None:
        self._progress.close()
