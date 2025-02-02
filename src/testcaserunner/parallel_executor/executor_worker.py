"""並列処理の実装部分

・それぞれの並列化処理はBaseExecutorを継承して実装する
・tqdmにより、プログレスバーを表示する
・signalにより、KeyboardInterrupt(Ctrl + C)をキャッチして処理を中断する
"""

from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, Future, Executor
from typing import Callable, Self, TypeVar
from abc import ABC, abstractmethod
import signal
import types

from tqdm import tqdm

from ..debug import RunnerLogger

Argument = TypeVar("Argument")
Return = TypeVar("Return")
Handler = Callable[[Argument], Return]
class BaseExecutor(ABC): # pragma: no cover
    """Executorの基底クラス"""
    NOT_START = 0
    STARTED = 1
    SUBMITTED = 2
    FINISHED = 3
    def __init__(self, total: int):
        pass

    @abstractmethod
    def submit(self, handler: Handler, arguments: list[Argument]) -> None:
        pass

    @abstractmethod
    def wait_and_get_results(self) -> list[Return|None]:
        pass

    @abstractmethod
    def __enter__(self) -> Self:
        pass

    @abstractmethod
    def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None,
                 exc_tb: BaseException|None):
        pass

    def notify_catch_keyboard_interrupt(self):
        RunnerLogger.warning("ランナーの実行をキャンセルします。")

class BaseParallelExecutor(BaseExecutor):
    """concurrent.futuresを使用する並列化処理の基底クラス"""
    def __init__(self, total: int):
        self._total = total
        self._status = self.NOT_START
        self._interrupted = False
    
    @abstractmethod
    def get_executor(self) -> Executor:
        raise NotImplementedError

    def submit(self, handler: Handler, arguments: list[Argument]):
        if self._status != self.STARTED:
            raise ValueError("使い方間違ってるよ")
        self._futures: list[Future] = []
        for testcase in arguments:
            future = self._executor.submit(handler, testcase)
            future.add_done_callback(lambda p: self._progress.update())
            self._futures.append(future)
        self._status = self.SUBMITTED
    
    def wait_and_get_results(self) -> list[Return|None]:
        results: list[Return|None] = []
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

    def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None,
                 exc_tb: BaseException|None) -> None:
        self._progress.close()
        self._executor.shutdown()
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    def signal_handler(self, signum: int, frame: None | types.FrameType) -> None:
        self._interrupted = True
        self.notify_catch_keyboard_interrupt()

class ProcessParallelExecutor(BaseParallelExecutor):
    """ProcessPoolExecutorを使用した並列化処理"""
    def get_executor(self) -> Executor:
        return ProcessPoolExecutor()

class ThreadParallelExecutor(BaseParallelExecutor):
    """ThreadParallelExecutorを使用した並列化処理"""
    def get_executor(self) -> Executor:
        return ThreadPoolExecutor()

class SerialExecutor(BaseExecutor):
    """非並列化の処理"""
    def __init__(self, total: int):
        self._total = total
        self._status = self.NOT_START

    def submit(self, handler: Handler, arguments: list[Argument]) -> None:
        if self._status != self.STARTED:
            raise ValueError("使い方間違ってるよ")
        self._handler = handler
        self._testcases = arguments
        self._status = self.SUBMITTED
    
    def wait_and_get_results(self) -> list[Return|None]:
        results: list[Return|None] = []
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

    def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None,
                 exc_tb: BaseException|None) -> None:
        self._progress.close()
