import time
import subprocess
import random

from testcaserunner import (
    run,
    ResultStatus,
    TestCaseResult,
    TestCase,
    )

def run_program(testcase: TestCase):
    """プログラムを走らせる処理をここに書く
    
    Args:
        testcase(TestCases): TestCaseクラス
    
    Returns:
        TestCaseResult: テストケースの結果
    
    TestCaseResultのattributesメンバにDict[str, Union[int, float]]で値を書いておくと
    結果として出力されるHTMLファイルに結果が載る
    
    keyとして`score`があると、スコアの平均/最大値/最小値がHTMLファイルに載る
    """
    cmd = f"python main.py < {testcase.input_file}"
    start_time = time.time()
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    erapsed_time = time.time() - start_time
    err_stat = ResultStatus.AC
    score = random.randint(0, 100)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        err_stat = ResultStatus.RE
    attribute = {
        "score": score,
        "time": erapsed_time,
    }
    return TestCaseResult(err_stat, proc.stdout, proc.stderr, attribute)

if __name__ == "__main__":
    target = [
        "main.py",  # 存在するファイル
        "hoge.py",  # 存在しないファイル
        "in",       # ファイルではなくディレクトリ
    ]
    runner = run(run_program, copy_target_files=target)
