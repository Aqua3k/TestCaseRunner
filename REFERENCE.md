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
        testcase_handler: Callable[[TestCase], TestCaseResult|None],
        input_file_path: str,
        repeat_count: int = 1,
        copy_target_files: list[str] = [],
        parallel_processing_method: str = "process",
        time_limit: int|float|None = None,
        _debug: bool = False,
        ) -> None:
```

**普通に使う分には第一引数`testcase_handler`と第二引数`input_file_path`を設定するだけで十分です  
詳細な設定を知りたい方のみ、第三引数以降のオプション引数の説明を参照してください**  

引数`testcase_handler`には並列実行させたい関数を渡します。  
`testcase_handler`へ登録する関数は[TestCase](#testcase)クラスを引数にもち、[TestCaseResult](#testcaseresult)クラスもしくは`None`を戻り値に持つ関数です。  
[TestCaseResult](#testcaseresult)クラスを戻り値にすると、クラスの情報がHTMLファイルに載ります。   
`None`型を戻り値にすると、HTMLファイルへ追加の情報は載りません。  
（追加の情報が載らないだけで、HTMLファイルの作成は行われます）  

引数`input_file_path`にはテストケースファイルがあるディレクトリへのパスを渡します。  
`input_file_path`で渡されたディレクトリパス直下のすべてのファイルに対して`testcase_handler`を実行します。  
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

引数`time_limit`は実行制限時間の上限を設定します。  
オプション引数で、デフォルト値は`None`です。  
設定値`None`は`float(inf)`と同じふるまいをします。  
`testcase_handler`を実行したときの実行時間がこの値以上だった場合、実行時間エラー(TLE)が記録されます。  
**現時点では、実行時間を超過したプログラムの強制終了はしません。**  
実行時間を超過したプログラムの強制終了機能は今後実装予定です。  

| 引数 | 説明 |
| --- | --- |
| `"process"` | [ProcessPoolExecutor](https://docs.python.org/ja/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor)を使ってプロセスを並列化します。<br>CPUバウンドな処理を行う場合に適しています。<br>詳しくはリンク先のドキュメントを参照してください。 |
| `"thread"`  | [ThreadPoolExecutor](https://docs.python.org/ja/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor)を使ってスレッドを並列化します。<br>I/Oバウンドな処理を行う場合に適しています。<br>詳しくはリンク先のドキュメントを参照してください。 |
| `"single"`  | 並列化を行いません。 |

引数`_debug`はデバッグ用の出力の有無を切り替えます。  
オプション引数で、デフォルト値は`False`です。  
開発用の使用を想定しており、それ以外でこの引数を`True`に設定するメリットはありません。    

## Classes

### TestCaseResult  

個別のテストケースの実行結果を管理するクラスです。  
[run](#run)関数の戻り値として使用します。  

メンバ`attribute`には結果ファイルにカスタマイズして載せたい情報を辞書型で指定します。  
詳しくはサンプルコードを参照してください。  

文字列を`stdout`へ指定すると、内容がファイルに出力されHTMLファイルからリンクとして参照できます。    
`stdout`がデフォルト引数`None`のままの場合、ファイルに何も出力しません。  

文字列を`stderr`へ指定すると、内容がファイルに出力されHTMLファイルからリンクとして参照できます。    
`stderr`がデフォルト引数`None`のままの場合、ファイルに何も出力しません。  

メンバ`error_status`は[ResultStatus](#resultstatus)クラスで、テストケースの実行結果ステータスを記録します。  

```python
@dataclass
class TestCaseResult:
    """テストケースの結果をまとめて管理するクラス"""
    attribute: dict[str, int | float] \
        = field(default_factory=dict)    # 結果ファイルに乗せたい情報の一覧
    stdout: str|None = None              # 標準出力(なければ空文字でいい)
    stderr: str|None = None              # 標準エラー出力(なければ空文字でいい)
    error_status: str|None = None        # エラーステータス
    result_description: str|None = None  # 実行結果の詳細な説明(任意)
```

### TestCase

個別のテストケースの入出力ファイルを管理するクラスです。  
[run](#run)関数で渡す関数`testcase_handler`の引数で使用します。  

メンバ`testcase_name`は入力されるテストケースファイルのファイル名です。  

メンバ`input_file_path`は入力テストケースファイルへのパスです。  
[run](#run)関数で渡す関数`testcase_handler`では、`input_file_path`の内容に対する処理を書いてください。  

メンバ`stdout_file_path`は標準出力の内容を記録するファイルへのパスです。  

メンバ`stderr_file_path`は標準エラー出力の内容を記録するファイルへのパスです。  

メンバ`testcase_index`は0以上(入力ファイル) * (repeat_count) - 1以下の整数です。  
各ケースに対して固有の値であることが保証されます。  
個別のテストケースに対してシード値を固定したい場合に使用することを想定しています。  

```python
@dataclass(frozen=True)
class TestCase:
    testcase_name: str
    input_file_path: str
    stdout_file_path: str
    stderr_file_path: str
    testcase_index: int
```

## Exceptions

### InvalidPathException  

[run](#run)関数の第二引数のパスが正しくなかったときに使われる例外です。

### NoTestcaseFileException

[run](#run)関数の第二引数のパスで指定されたディレクトリにファイルが1つも存在しなかったときに使われる例外です。
