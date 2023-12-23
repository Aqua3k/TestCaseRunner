import time
import subprocess

from runner_.runner import run, ResultStatus, TestCaseResult

def run_program(input, output):
    """プログラムを走らせる処理をここに書く
    
    Args:
        input(str): 入力ファイルへのパス
        
        output(str):
            出力ファイルへのパス
            このパスに結果を出力する必要はないが、念のため引数として渡している
    
    Returns:
        TestCaseResult: テストケースの結果
    
    TestCaseResultのattributesメンバにDict[str, Union[int, float]]で値を書いておくと
    結果として出力されるHTMLファイルに結果が載る
    
    keyとして`score`があると、スコアの平均/最大値/最小値がHTMLファイルに載る
    """
    cmd = f"cargo run --release --bin tester python main.py < {input}"
    start_time = time.time()
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    erapsed_time = time.time() - start_time
    err_stat = ResultStatus.AC
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        err_stat = ResultStatus.RE
    score = 0
    attribute = {
        "score": score,
        "time": erapsed_time,
    }
    return TestCaseResult(err_stat, proc.stdout, proc.stderr, attribute)

if __name__ == "__main__":
    run(run_program)
