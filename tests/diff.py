import subprocess
import sys
sys.path.append(r"..\src")

from testcaserunner import (
    run,
    ResultStatus,
    TestCaseResult,
    TestCase,
    RunnerLogViewer,
    )

def score1(n, m, idx):
    s = n + m
    return s

def score2(n, m, idx):
    s = n + m
    if idx%3 == 0:
        s *= 2
    return s

def run_program1(testcase: TestCase):
    cmd = f"python main.py < {testcase.input_file_path}"
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    err_stat = ResultStatus.AC
    n,m = map(int, next(testcase.read_testcase_lines()).split())
    score = score1(n,m,testcase.testcase_index)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        err_stat = ResultStatus.RE
    attribute = {
        "score": score,
        "n": n,
        "m": m,
    }
    return TestCaseResult(err_stat, proc.stdout, proc.stderr, attribute)

def run_program2(testcase: TestCase):
    cmd = f"python main.py < {testcase.input_file_path}"
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    err_stat = ResultStatus.AC
    n,m = map(int, next(testcase.read_testcase_lines()).split())
    score = score2(n,m,testcase.testcase_index)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        err_stat = ResultStatus.RE
    attribute = {
        "score": score,
        "n": n,
        "m": m,
    }
    return TestCaseResult(err_stat, proc.stdout, proc.stderr, attribute)

if __name__ == "__main__":
    result1 = run(run_program1, "in", _debug=True)
    result2 = run(run_program2, "in", _debug=True)
    viewer = RunnerLogViewer()
    logs = viewer.get_logs()
    diff = viewer.test_diff(logs[0], logs[1])
    print(diff)
