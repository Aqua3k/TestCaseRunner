time_limit = 2 #実行を打ち切る時間

#ファイル関係
input_file_path = "in"        #入力ファイルの場所
result_file_path = "out"      #ファイル出力する場所

#log
logFilePath = "log"         #Logファイルを出力するパス

#statistics関係
is_make_fig = True
statistics_info_define_array = []
statistics_path = "statistics"
csv_file_name     = "Statistics.csv"

#コマンド関係
#実行コマンド ただし、inFileに入力ファイルパス、outFileに出力ファイルパスが入る
command = "cargo run --release --bin tester python main.py < {in_file} > {out_file}"
