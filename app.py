import os

from flask import Flask, render_template, request, url_for, send_from_directory, redirect, flash
from werkzeug.utils import secure_filename

import azure_face as az


app = Flask(__name__)

UPLOAD_FOLDER = './static/uploads' # 入力画像の保存場所
ALLOWED_EXTENSIONS = set(['jpg','png']) # 拡張子の設定 ここで設定したものしか読み込まない
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.urandom(24)


@app.context_processor
def override_url_for():
    """staticの画像の更新用"""
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    # 判定後の画像の保存を上書きしているためhtmlの画像を更新する処理
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


def allwed_file(filename):
    # ファイルの拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        # ファイルのチェック
        if 'file' not in request.files:
            flash('ファイルがありません', 'error')
            return redirect('/')
        file = request.files['file'] # ファイルの取得
        if file.filename == '':            
            flash('ファイルがありません', 'error')
            return redirect('/')

        # 拡張子のチェック
        if not allwed_file(file.filename):
            flash('拡張子が対応していません', 'error')
            return redirect('/')

        # ファイルの保存
        filename = secure_filename(file.filename) # ファイル名を取得
        file_save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename) # ファイルの保存するパスの取得
        file.save(file_save_path) # 画像を保存

        # 選択した人物の名前を取得
        select_name = request.form['select_name']
        
        # 選択した人物がいるか判定
        rate = az.start_identify_faces(file_save_path, select_name)
        if not rate:
            # 選択した人物が画像から見つからなかった時の処理
            flash(select_name + 'は')
            flash('検出できませんでした', 'error')
            return redirect('/')
        else:
            # 選択した人物が画像から見つかった時の処理
            flash(select_name, 'success')
            flash(rate + '%', 'success')
            dst_img = 'dst/identify_faces.jpg' # 判定後の画像のパス
            return render_template('index.html', dst_img=dst_img)

    return render_template('index.html')
        

if __name__ == '__main__':
    app.run(debug=True)