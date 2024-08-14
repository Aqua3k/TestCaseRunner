# リファレンス

## import

```python
import testcaserunner
```

## Functions

### run  

テストケースを実行し、結果をHTML形式で`Log`フォルダ内に保存します。  

```python
def run(
        handler: Callable[[TestCase], TestCaseResult],
        input_file_path: str,
        repeat_count: int = 1,
        copy_target_files: list[str] = [],
        parallel_processing_method: str = "process",
        stdout_file_output: bool = True,
        stderr_file_output: bool = True,
        _debug: bool = False,
        ) -> None:
```

**普通に使う分には第一引数`handler`と第二引数`input_file_path`を設定するだけで十分です  
詳細な設定を知りたい方のみ、第三引数以降のオプション引数の説明を参照してください**  

引数`handler`には並列実行させたい関数を渡します。  
`handler`は[TestCase](#testcase)クラスを引数にもち、[TestCaseResult](#testcaseresult)クラスを戻り値に持つ関数です。  

引数`input_file_path`にはテストケースファイルがあるディレクトリへのパスを渡します。  
`input_file_path`で渡されたディレクトリパス直下のすべてのファイルに対して`handler`を実行します。  
現時点では、フォルダ内を再帰的に走査するオプションやファイルの拡張子を限定するオプションはありません。  

引数`repeat_count`にはそれぞれのテストケースを何回実行するかを指定します。  
オプション引数で、デフォルト値は1です。  
使用するアルゴリズムでランダム値を使うなどが理由で結果が一意に定まらない場合に、複数回実行してパフォーマンスを測りたいときに使用することを想定しています。  

引数`copy_target_files`はファイルパスのリストです。  
オプション引数で、デフォルト値は[]です。  
ここで与えられたパスはログディレクトリを作成する際に、HTMLファイルや入力テストケースファイルと一緒にコピーして保存されます。  
与えられたパスのファイルが存在しなかった場合は警告メッセージが出力されます。

引数`parallel_processing_method`は並列処理の実行方法を指定します。  
オプション引数で、デフォルト値は`"process"`です。  
指定可能なオプションは以下の3つです。  

| 引数 | 説明 |
| --- | --- |
| `"process"` | [ProcessPoolExecutor](https://docs.python.org/ja/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor)を使ってプロセスを並列化します。<br>CPUバウンドな処理を行う場合に適しています。<br>詳しくはリンク先のドキュメントを参照してください。 |
| `"thread"`  | [ThreadPoolExecutor](https://docs.python.org/ja/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor)を使ってスレッドを並列化します。<br>I/Oバウンドな処理を行う場合に適しています。<br>詳しくはリンク先のドキュメントを参照してください。 |
| `"single"`  | 並列化を行いません。 |

`stdout_file_output`は標準出力の内容をファイルとして保存するかどうかを指定します。  
オプション引数で、デフォルト値はTrueです。  
この引数がTrueの場合、[TestCaseResult](#testcaseresult)クラスのメンバ`stdout`をファイルに保存します。  

`stderr_file_output`は標準出力の内容をファイルとして保存するかどうかを指定します。  
オプション引数で、デフォルト値はTrueです。  
この引数がTrueの場合、[TestCaseResult](#testcaseresult)クラスのメンバ`stderr`をファイルに保存します。  

## Classes

### ResultStatus  

テストケースの実行結果のステータスを定義するEnum型の定義です。  
[TestCaseResult](#testcaseresult)クラスのメンバ`error_status`で使用します。  


```python
class ResultStatus(IntEnum):
    """テストケースを実行した結果のステータス定義

    結果ファイルに載るだけで特別な処理をするわけではない
    """
    AC = auto()             # Accepted
    WA = auto()             # Wrong Answer
    RE = auto()             # 実行時エラー
    TLE = auto()            # 実行時間制限超過
    IE = auto()             # 内部エラー
```

### TestCaseResult  

個別のテストケースの実行結果を管理するクラスです。  
[run](#run)関数の戻り値として使用します。  

メンバ`error_status`は[ResultStatus](#resultstatus)クラスで、テストケースの実行結果ステータスを記録します。  

メンバ`stdout`には標準出力として記録したい内容を文字列型で指定します。  
[run](run)関数の`stdout_file_output`で`True`を指定していた場合、`stdout`の内容がファイルに保存され、HTMLファイルからリンクとして参照できます。    

メンバ`stderr`には標準エラー出力として記録したい内容を文字列型で指定します。  
[run](run)関数の`stderr_file_output`で`True`を指定していた場合、`stderr`の内容がファイルに保存され、HTMLファイルからリンクとして参照できます。  

メンバ`attribute`には結果ファイルにカスタマイズして載せたい情報を辞書型で指定します。  
詳しくはサンプルコードを参照してください。  

```python
@dataclass
class TestCaseResult:
    """テストケースの結果をまとめて管理するクラス"""
    error_status: ResultStatus = ResultStatus.AC # 終了のステータス
    stdout: str = ""                             # 標準出力(なければ空文字でいい)
    stderr: str = ""                             # 標準エラー出力(なければ空文字でいい)
    attribute: dicg[str, int | float] \
        = field(default_factory=dict)            # 結果ファイルに乗せたい情報の一覧
```

### TestCase

個別のテストケースの入出力ファイルを管理するクラスです。  
[run](#run)関数で渡す関数`handler`の引数で使用します。  

メンバ`testcase_name`は入力されるテストケースファイルのファイル名です。  

メンバ`input_file_path`は入力テストケースファイルへのパスです。  
[run](#run)関数で渡す関数`handler`では、`input_file_path`の内容に対する処理を書いてください。  

メンバ`stdout_file_path`は標準出力の内容を記録するファイルへのパスです。  

メンバ`stderr_file_path`は標準エラー出力の内容を記録するファイルへのパスです。  

メンバ`testcase_index`は0以上(入力ファイル) * (repeat_count) - 1以下の整数です。  
各ケースに対して固有の値であることが保証されます。  
個別のテストケースに対してシード値を固定したい場合に使用することを想定しています。  

メソッド`read_testcase_lines`は1行ずつテストケースの入力ファイルの内容を取得するジェネレータを返す関数です。  

```python
@dataclass(frozen=True)
class TestCase:
    testcase_name: str
    input_file_path: str
    stdout_file_path: str
    stderr_file_path: str
    testcase_index: int

    def read_testcase_lines(self):
        """テストケースファイルの内容を1行ずつ取得するジェネレータ

        Yields:
            str: ファイルの各行の内容
        """
```

## Exceptions

### InvalidPathException  

[run](#run)関数の第二引数のパスが正しくなかったときに使われる例外です。

### NoTestcaseFileException

[run](#run)関数の第二引数のパスで指定されたディレクトリにファイルが1つも存在しなかったときに使われる例外です。
