import subprocess
import sys
import shutil
import os
import logging

import pytest

sys.path.append(os.path.join("..", "src"))

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

def error_program(testcase: TestCase):
    foo = 1/0 # division by zero.
    return TestCaseResult()

def no_error_program_attribute(testcase: TestCase):
    basename = os.path.basename(testcase)
    case = os.path.split(basename)[0]
    attrbute = {}
    if int(case) % 2 == 0:
        attrbute["even"] = int(case)
    else:
        attrbute["odd"] = int(case)
    return TestCaseResult(attribute=attrbute)

@pytest.fixture
def setup_normally():
    """logフォルダを消してno_filesフォルダを作る"""
    if os.path.exists("log"):
        shutil.rmtree("log")
    if os.path.exists("no_files"):
        shutil.rmtree("no_files")
    os.mkdir("no_files")

# 警告も例外も出ない
def test_no_error_no_warning_case0(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in")
    assert len(caplog.records) == 0

def test_no_error_no_warning_case1(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", copy_target_files=["main.py"])
    assert len(caplog.records) == 0

def test_no_error_no_warning_case2(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", stdout_file_output=False)
    assert len(caplog.records) == 0

def test_no_error_no_warning_case3(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", stderr_file_output=False)
    assert len(caplog.records) == 0

def test_no_error_no_warning_case4(caplog, setup_normally):
    # 2回同じフォルダに対して走らせることで、カバレッジを埋める
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", log_folder_name="test")
        run(handler=no_error_program, input_file_path="in", log_folder_name="test")
    assert len(caplog.records) == 0

def test_no_error_no_warning_case5(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", measure_time=False)
    assert len(caplog.records) == 0

def test_no_error_no_warning_case6(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", parallel_processing_method="process")
    assert len(caplog.records) == 0

def test_no_error_no_warning_case7(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", parallel_processing_method="PROCESS")
    assert len(caplog.records) == 0

def test_no_error_no_warning_case8(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", parallel_processing_method="thread")
    assert len(caplog.records) == 0

def test_no_error_no_warning_case9(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", parallel_processing_method="THREAD")
    assert len(caplog.records) == 0

def test_no_error_no_warning_case10(caplog, setup_normally):
    run(handler=error_program, input_file_path="in")

def test_no_error_no_warning_case11(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", parallel_processing_method="single")
    assert len(caplog.records) == 0

def test_no_error_no_warning_case11(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", parallel_processing_method="SINGLE")
    assert len(caplog.records) == 0

def test_no_error_no_warning_case13(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program_attribute, input_file_path="in")
    assert len(caplog.records) == 0

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

def test_with_error_case3(setup_normally):
    with pytest.raises(ValueError):
        run(handler=no_error_program, input_file_path="in", parallel_processing_method="test")

# 警告が出る
def test_with_warning_case0(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", copy_target_files=["not_exist"])
    assert len(caplog.records) == 1

def test_with_warning_case1(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=no_error_program, input_file_path="in", copy_target_files=["in"])
    assert len(caplog.records) == 1

def test_with_warning_case2(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(handler=error_program, input_file_path="in", parallel_processing_method="single")
    assert len(caplog.records) != 0

# デバッグメッセージのテスト
def test_with_debugmessage_case0(caplog, setup_normally):
    # デバッグ起動でデバッグメッセージが出る
    with caplog.at_level(logging.DEBUG):
        run(handler=no_error_program, input_file_path="in", _debug=True)
    assert len(caplog.records) != 0
