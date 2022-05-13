#ファイル関係
inputFilePath = "in"        #入力ファイルの場所
resultFilePath = "out"      #ファイル出力する場所

#log
logFilePath = "log"         #Logファイルを出力するパス

#statistics関係
makeFigure = True
scoreStr   = "score"
statisticsInfoArray = []
statisticsDirec = "statistics"
csvFileName     = "Statistics.csv"

#コマンド関係
#実行コマンド ただし、inFileに入力ファイルパス、outFileに出力ファイルパスが入る
command = "cargo run --release --bin tester python main.py < {inFile} > {outFile}"
