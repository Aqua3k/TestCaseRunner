import subprocess
import sys
import shutil
import os
import logging

import pytest

sys.path.append(os.path.join("..", "src"))

from testcaserunner import (
    run,
    TestCaseResult,
    TestCase,
    InvalidPathException,
    NoTestcaseFileException,
    )

# テストコードで使う関数
def no_error_program(testcase: TestCase):
    cmd = f"python main.py < {testcase.input_file_path}"
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    with open(testcase.input_file_path, mode="r") as file:
        line = file.readline().strip()
    n,m = map(int, line.split())
    score = n+m
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        return TestCaseResult({}, proc.stdout, proc.stderr, "Error")
    attribute = {
        "score": score,
        "n": n,
        "m": m,
    }
    return TestCaseResult(attribute, proc.stdout, proc.stderr)

def error_program(testcase: TestCase):
    foo = 1/0 # division by zero.
    return TestCaseResult()

def return_none(testcase: TestCase):
    return None

def no_error_program_attribute(testcase: TestCase):
    basename = os.path.basename(testcase)
    case = os.path.split(basename)[0]
    attrbute = {}
    if int(case) % 2 == 0:
        attrbute["even"] = int(case)
    else:
        attrbute["odd"] = int(case)
    return TestCaseResult(attribute=attrbute)

# フィクスチャ
@pytest.fixture
def setup_normally():
    """logフォルダを消してno_filesフォルダを作る"""
    if os.path.exists("log"):
        shutil.rmtree("log")
    if os.path.exists("no_files"):
        shutil.rmtree("no_files")
    os.mkdir("no_files")

# テストコード
def test_arguments_are_valid1(caplog, setup_normally):
    # 警告なしで正常に処理が終わる
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in")
    assert len(caplog.records) == 0

def test_arguments_are_valid2(caplog, setup_normally):
    # 登録したハンドラの中でエラーがあっても正常終了する
    run(testcase_handler=error_program, input_file_path="in")

def test_arguments_are_valid3(caplog, setup_normally):
    # attributeへ情報を登録することができる
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program_attribute, input_file_path="in")
    assert len(caplog.records) == 0

def test_arguments_are_valid4(caplog, setup_normally):
    # 戻り値Noneは許される
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=return_none, input_file_path="in")
    assert len(caplog.records) == 0

def test_no_error_no_warning_case13(caplog, setup_normally):
    # すべての引数に値を設定する
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in",\
             parallel_processing_method="single", repeat_count=2)
    assert len(caplog.records) == 0

def test_2nd_argument_is_invalid1(setup_normally):
    # 第二引数へ存在しないパスを入れたらInvalidPathException
    with pytest.raises(InvalidPathException):
        run(testcase_handler=no_error_program, input_file_path="foo")

def test_2nd_argument_is_invalid2(setup_normally):
    # 第二引数で指定されたフォルダでファイルがなければNoTestcaseFileException
    with pytest.raises(NoTestcaseFileException):
        run(testcase_handler=no_error_program, input_file_path="no_files")

def test_3rd_argument_is_invalid(setup_normally):
    # 第三引数で負の数を指定したらエラー
    with pytest.raises(ValueError):
        run(testcase_handler=no_error_program, input_file_path="no_files", repeat_count=-1)

def test_4th_arguments_is_valid(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", copy_target_files=["main.py"])
    assert len(caplog.records) == 0

def test_4th_argument_is_invalid1(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", copy_target_files=["not_exist"])
    assert len(caplog.records) == 1

def test_4th_argument_is_invalid2(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", copy_target_files=["in"])
    assert len(caplog.records) == 1

def test_5th_argument_is_valid1(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", parallel_processing_method="process")
    assert len(caplog.records) == 0

def test_5th_argument_is_valid2(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", parallel_processing_method="PROCESS")
    assert len(caplog.records) == 0

def test_5th_argument_is_valid3(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", parallel_processing_method="thread")
    assert len(caplog.records) == 0

def test_5th_argument_is_valid4(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", parallel_processing_method="THREAD")
    assert len(caplog.records) == 0

def test_5th_argument_is_valid5(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", parallel_processing_method="single")
    assert len(caplog.records) == 0

def test_5th_argument_is_valid6(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", parallel_processing_method="SINGLE")
    assert len(caplog.records) == 0

def test_5th_argument_is_invalid(setup_normally):
    with pytest.raises(ValueError):
        run(testcase_handler=no_error_program, input_file_path="in", parallel_processing_method="test")

def test_6th_argument_is_valid1(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", time_limit=10)
    assert len(caplog.records) == 0

def test_6th_argument_is_valid2(caplog, setup_normally):
    with caplog.at_level(logging.WARNING):
        run(testcase_handler=no_error_program, input_file_path="in", time_limit=3.14)
    assert len(caplog.records) == 0

def test_debug_message(caplog, setup_normally):
    # デバッグメッセージが出力される
    with caplog.at_level(logging.DEBUG):
        run(testcase_handler=no_error_program, input_file_path="in", _debug=True)
    assert len(caplog.records) != 0
