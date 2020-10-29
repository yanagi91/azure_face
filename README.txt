AzureのFaceAPIを使って逃げ恥の顔判定

<概要>
アップロードした画像に選択した人物が写っているか判定します。

写っていた場合は判定した顔を四角で囲い表示します。
判定できない場合は　"検出できませんでした"　と表示されます。

画像が小さすぎたり顔が正面を向いていないと上手く認識できないことがあります。

<azure_face.py>
    (入力必須)
        # 環境変数の入力
            19　os.environ['FACE_SUBSCRIPTION_KEY'] = ""
            20　os.environ['FACE_ENDPOINT'] = ""
        # similar 用の画像のパス
            23　single_face_image_url = 'image/' # 画像のパス
            24　multi_face_image_url = 'image/' # 複数人の画像のパス

        # 学習したモデルの確認用の画像のパス
            28　test_image = 'image/'

    (各関数)
        ・similar_face_rectangle():
            実行結果の画像は
            image/dst/test.jpg に保存される。上書き保存されるので注意

        ・face_traning():
            実行する際は
            imageフォルダに学習用の画像を保存しファイル名の頭文字を
            新垣結衣：a
            星野源：h
            真野恵里菜：m
            として保存する。
            PERSON_GROUP_IDを変えたい場合は
            151 PERSON_GROUP_ID
            154 TARGET_PERSON_GROUP_ID 
            を変更する。モデルを変える場合などは同じPERSON_GROUP_IDで出来ないのでその時にここを変える。

        ・start_identify_faces(image, select_name)：
            学習したモデルを使って顔の判定を行う。
            判定後の画像は
            static/dst/identify_faces.jpg　に保存される。上書き保存するので注意

<app.py>
    Flask
    判定前のアップロードした画像は
    static/uploads に保存される。
    判定後の画像は
    static/dst/identify_faces.jpg に保存される。上書き保存するので注意