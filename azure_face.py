import asyncio
import io
import glob
import os
import sys
import time
import uuid
import requests
from urllib.parse import urlparse
from io import BytesIO
# To install this module, run:
# python -m pip install Pillow
from PIL import Image, ImageDraw
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person


os.environ['FACE_SUBSCRIPTION_KEY'] = ""
os.environ['FACE_ENDPOINT'] = ""

# similar_face_rectangle() でのみ使う
single_face_image_url = 'image/' # 画像のパス
multi_face_image_url = 'image/' # 複数人の画像のパス
save_path = 'image/dst/test.jpg'

# traning() 後に行う時に使う
test_image = 'image/' # 画像のパス
select_name = 'AragakiYui' # 結果で表示する際の選択する人物['AragakiYui', 'HoshinoGen', 'ManoErina']

# Set the FACE_SUBSCRIPTION_KEY environment variable with your key as the value.
# This key will serve all examples in this document.
KEY = os.environ['FACE_SUBSCRIPTION_KEY']

# Set the FACE_ENDPOINT environment variable with the endpoint from your Face service in Azure.
# This endpoint will be used in all examples in this quickstart.
ENDPOINT = os.environ['FACE_ENDPOINT']

# Create an authenticated FaceClient.
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))
# Detect a face in an image that contains a single face

# 画像内の顔の検出
def face_detected(face_data, image_name):
    """return detected_faces, image_face_ID
    
    顔の検出"""
    # We use detection model 2 because we are not retrieving attributes.
    detected_faces = face_client.face.detect_with_stream(image=face_data, recognition_model="recognition_03", detectionModel='detection_02')
    if not detected_faces:
        # 顔が検出出来なかった場合の処理
        #raise Exception('No face detected from image {}'.format(image_name))
        return None, None

    # Display the detected face ID in the first single-face image.
    # Face IDs are used for comparison to faces (their IDs) detected in other images.
    print('Detected face ID from', image_name, ':')
    for face in detected_faces: print (face.face_id)
    print()

    # Save this ID for use in Find Similar
    #print(detected_faces)
    #face_IDs = detected_faces[0].face_id
    face_ids = []
    for face in detected_faces:
        face_ids.append(face.face_id)
    return detected_faces, face_ids

# 顔座標の取得
def getRectangle(faceDictionary):
    rect = faceDictionary.face_rectangle
    left = rect.left
    top = rect.top
    right = left + rect.width
    bottom = top + rect.height
    return ((left, top), (right, bottom))

# 顔をフレームに収める
def face_rectangle_az(face_image_url, detected_faces):
    """検出した顔を枠で囲う"""
    img = Image.open(face_image_url)

    # For each face returned use the face rectangle and draw a red box.
    print('Drawing rectangle around face... see popup for results.')
    draw = ImageDraw.Draw(img)
    outline_color = ['red', 'green', 'blue']
    i = 0
    for face in detected_faces:
        draw.rectangle(getRectangle(face), outline=outline_color[i])
        i += 1
        if i > 2:
            i = 0

    # Display the image in the users default image browser.
    #img.show()
    img.save(save_path)

# 似た顔の検索
def face_find_az(detected_faces2, first_image_face_ID, multi_image_name):
    """return face_info

    似た画像の検索、同一人物でなくてもヒットする"""
    # Search through faces detected in group image for the single face from first image.
    # First, create a list of the face IDs found in the second image.
    
    second_image_face_IDs = list(map(lambda x: x.face_id, detected_faces2))
    # Next, find similar face IDs like the one detected in the first image.
    similar_faces = face_client.face.find_similar(face_id=first_image_face_ID[0], face_ids=second_image_face_IDs)
    if not similar_faces[0]:
        print('No similar faces found in', multi_image_name, '.')

    # 一致するものを出力
    # Print the details of the similar faces detected
    print('Similar faces found in', multi_image_name + ':')
    for face in similar_faces:
        first_image_face_ID = face.face_id
        # The similar face IDs of the single face image and the group image do not need to match, 
        # they are only used for identification purposes in each image.
        # The similar faces are matched using the Cognitive Services algorithm in find_similar().
        face_info = next(x for x in detected_faces2 if x.face_id == first_image_face_ID)
        if face_info:
            print('  Face ID: ', first_image_face_ID)
            print('  Face rectangle:')
            print('    Left: ', str(face_info.face_rectangle.left))
            print('    Top: ', str(face_info.face_rectangle.top))
            print('    Width: ', str(face_info.face_rectangle.width))
            print('    Height: ', str(face_info.face_rectangle.height))
    #print(face_info)
    return face_info


# クイックスタートの似た画像の検出を実行する関数
def similar_face_rectangle():
    # 元になる画像の処理

    single_image_name = os.path.basename(single_face_image_url) # ファイル名の取得
    single_face_data = open(single_face_image_url, 'rb') # 画像の読み込み
    _, first_image_face_ID = face_detected(single_face_data, single_image_name) # 顔の検出
    # 検索する画像の処理
    multi_image_name = os.path.basename(multi_face_image_url) # ファイル名の取得
    multi_face_data = open(multi_face_image_url, 'rb') # 画像の読み込み
    detected_faces2, _ = face_detected(multi_face_data, multi_image_name) # 顔の検出
    # 似た顔の検出
    face_info = face_find_az(detected_faces2, first_image_face_ID, multi_image_name)
    face_rectangle_az(multi_face_image_url, [face_info]) # 似た顔を枠で囲う


# Used in the Person Group Operations and Delete Person Group examples.
# You can call list_person_groups to print a list of preexisting PersonGroups.
# SOURCE_PERSON_GROUP_ID should be all lowercase and alphanumeric. For example, 'mygroupname' (dashes are OK).
PERSON_GROUP_ID = str('mygroupname') # assign a random ID (or name it anything)

# Used for the Delete Person Group example.
TARGET_PERSON_GROUP_ID = str('mygroupname') # assign a random ID (or name it anything)

# 学習
def face_traning():
    """学習する顔のグループの作成、学習を行う"""
    '''
    Create the PersonGroup
    '''
    # Create empty Person Group. Person Group ID must be lower case, alphanumeric, and/or with '-', '_'.
    print('Person group:', PERSON_GROUP_ID)
    face_client.person_group.create(person_group_id=PERSON_GROUP_ID, name=PERSON_GROUP_ID, recognition_model="recognition_03")

    # Define aragaki friend
    aragaki = face_client.person_group_person.create(PERSON_GROUP_ID, "AragakiYui")
    # Define hoshino friend
    hoshino = face_client.person_group_person.create(PERSON_GROUP_ID, "HoshinoGen")
    # Define mano friend
    mano = face_client.person_group_person.create(PERSON_GROUP_ID, "ManoErina")

    '''
    Detect faces and register to correct person
    '''
    # Find all jpeg images of friends in working directory
    aragaki_images = [file for file in glob.glob('image/*.jpg') if file.startswith("image\\a")]
    hoshino_images = [file for file in glob.glob('image/*.jpg') if file.startswith("image\\h")]
    mano_images = [file for file in glob.glob('image/*.jpg') if file.startswith("image\\m")]

    #print(aragaki_images)
    # Add to a aragaki person
    for image in aragaki_images:
        a = open(image, 'r+b')
        face_client.person_group_person.add_face_from_stream(PERSON_GROUP_ID, aragaki.person_id, a)

    # Add to a hoshino person
    for image in hoshino_images:
        h = open(image, 'r+b')
        face_client.person_group_person.add_face_from_stream(PERSON_GROUP_ID, hoshino.person_id, h)

    # Add to a mano person
    for image in mano_images:
        m = open(image, 'r+b')
        face_client.person_group_person.add_face_from_stream(PERSON_GROUP_ID, mano.person_id, m)

    '''
    Train PersonGroup
    '''
    print()
    print('Training the person group...')
    # Train the person group
    face_client.person_group.train(PERSON_GROUP_ID)

    while (True):
        training_status = face_client.person_group.get_training_status(PERSON_GROUP_ID)
        print("Training status: {}.".format(training_status.status))
        print()
        if (training_status.status is TrainingStatusType.succeeded):
            break
        elif (training_status.status is TrainingStatusType.failed):
            sys.exit('Training the person group has failed.')
        time.sleep(5)


def identify_faces(image, face_ids, detected_faces3):
    """return result_faces, result_name, rates

    学習した顔のグループと入力された画像を比較し一致するものを返す"""
    # Identify faces
    results = face_client.face.identify(face_ids, PERSON_GROUP_ID)
    print('Identifying faces in {}'.format(os.path.basename(image.name)))
    # 作成するリストの初期化
    result_faces = []
    result_name = []
    rates = []
    if not results:
        print('No person identified in the person group for faces from {}.'.format(os.path.basename(image.name)))
    for person in results:
        if len(person.candidates) > 0:
            #result_faces.append(detected_faces3.face_id[person.face_id])
            for detected in detected_faces3:
                if detected.face_id == person.face_id:
                    # 検索する画像からface_groupと一致した顔だけをリストに格納するための処理
                    result_faces.append(detected) # face_groupと一致したデータをリストに格納
                    # 一致したデータのnameのIDを取得
                    result_name_id = face_client.person_group_person.get(PERSON_GROUP_ID, person.candidates[0].person_id)
                    #print(result_name_id)
                    result_name.append(result_name_id.name) # nameのIDから名前をリストに格納
                    rates.append(person.candidates[0].confidence) # 確率をリストに格納
                    
            print('Person for face ID {} is identified in {} with a confidence of {}.'.format(result_name_id.name, os.path.basename(image.name), person.candidates[0].confidence)) # Get topmost confidence score
        else:
            print('No person identified for face ID {} in {}.'.format(person.face_id, os.path.basename(image.name)))
    #print(result_name)
    return result_faces, result_name, rates


def start_identify_faces(image, select_name):
    """return str(rates * 100)

    確率のみを返す（文字列型）。見つからない場合、Falseを返す"""
    global save_path
    # 画像の保存場所
    save_path = 'static/dst/identify_faces.jpg'

    # 入力画像の加工
    input_image = image
    input_image_name = os.path.basename(input_image)
    input_image_data = open(input_image, 'rb')
    #print("recognition:")
    #print(face_client.person_group.get(PERSON_GROUP_ID))
    # 顔の検出
    detected_faces, image_face_ID = face_detected(input_image_data, input_image_name)
    if detected_faces == None:
        # 顔を検出出来なかった場合の処理
        print('noface')
        return False

    # 顔の判定
    result_faces, result_name, rates = identify_faces(input_image_data, image_face_ID, detected_faces)

    try:
        # 判定した顔から選択した人物のインデックスを取得
        i = int(result_name.index(select_name))
    except:
        # 判定した顔の中に選択した人物がいない場合の処理
        return False
    # 選択した人物を枠で囲う
    face_rectangle_az(input_image,[result_faces[i]])
    return str(rates[i] * 100)


if __name__ == '__main__':
    similar_face_rectangle()
    face_traning()
    rates = start_identify_faces(test_image, select_name)

