import subprocess
import sys
import shutil
import os

import pytest

sys.path.append(r"..\src")

from testcaserunner import (
    run,
    ResultStatus,
    TestCaseResult,
    TestCase,
    InvalidPathException,
    NoTestcaseFileException,
    )

def no_error_program(testcase: TestCase):
    cmd = f"python main.py < {testcase.input_file_path}"
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    err_stat = ResultStatus.AC
    n,m = map(int, next(testcase.read_testcase_lines()).split())
    score = n+m
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

@pytest.fixture
def setup_normally():
    """logフォルダを消してno_filesフォルダを作る"""
    if os.path.exists("log"):
        shutil.rmtree("log")
    if os.path.exists("no_files"):
        shutil.rmtree("no_files")
    os.mkdir("no_files")

# 警告も例外も出ない
def test_no_error_no_warning_case0(setup_normally):
    with pytest.warns(None) as warning_info:
        run(handler=no_error_program, input_file_path="in")
    assert len(warning_info) == 0

def test_no_error_no_warning_case1(setup_normally):
    with pytest.warns(None) as warning_info:
        run(handler=no_error_program, input_file_path="in", copy_target_files=["main.py"])
    assert len(warning_info) == 0

def test_no_error_no_warning_case2(setup_normally):
    with pytest.warns(None) as warning_info:
        run(handler=no_error_program, input_file_path="in", stdout_file_output=False)
    assert len(warning_info) == 0

def test_no_error_no_warning_case3(setup_normally):
    with pytest.warns(None) as warning_info:
        run(handler=no_error_program, input_file_path="in", stderr_file_output=False)
    assert len(warning_info) == 0

def test_no_error_no_warning_case4(setup_normally):
    with pytest.warns(None) as warning_info:
        run(handler=no_error_program, input_file_path="in", log_folder_name="test")
    assert len(warning_info) == 0

def test_no_error_no_warning_case5(setup_normally):
    with pytest.warns(None) as warning_info:
        run(handler=no_error_program, input_file_path="in", measure_time=False)
    assert len(warning_info) == 0

# 例外が出る
def test_with_error_case0(setup_normally):
    with pytest.raises(InvalidPathException):
        run(handler=no_error_program, input_file_path="foo")

def test_with_error_case1(setup_normally):
    with pytest.raises(NoTestcaseFileException):
        run(handler=no_error_program, input_file_path="no_files")

def test_with_error_case2(setup_normally):
    with pytest.raises(ValueError):
        run(handler=no_error_program, input_file_path="no_files", repeat_count=-1)

# 警告が出る
def test_with_warning_case0(setup_normally):
    with pytest.warns(None) as warning_info:
        run(handler=no_error_program, input_file_path="in", copy_target_files=["not_exist"])
    assert len(warning_info) == 1

def test_with_warning_case1(setup_normally):
    with pytest.warns(None) as warning_info:
        run(handler=no_error_program, input_file_path="in", copy_target_files=["in"])
    assert len(warning_info) == 1
