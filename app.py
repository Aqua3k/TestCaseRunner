from flask import Flask
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/log_table', methods=['GET'])  # /data エンドポイントに対するGETリクエストを処理
def get_data():
    # レスポンスの内容を返す
    return os.getcwd()

if __name__ == '__main__':
    app.run(debug=True)  # デバッグモードでFlaskアプリケーションを実行
