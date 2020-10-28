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


image = 'image/aragaki1_person_group.jpg'
save_path = 'image/dtc/test.jpg'

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
    """face_detected(face_data, image_name
        return detected_faces, image_face_ID"""
    # We use detection model 2 because we are not retrieving attributes.
    detected_faces = face_client.face.detect_with_stream(image=face_data, detectionModel='detection_02')
    if not detected_faces:
        raise Exception('No face detected from image {}'.format(image_name))

    # Display the detected face ID in the first single-face image.
    # Face IDs are used for comparison to faces (their IDs) detected in other images.
    print('Detected face ID from', image_name, ':')
    for face in detected_faces: print (face.face_id)
    print()

    # Save this ID for use in Find Similar
    print(detected_faces)
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
    img = Image.open(face_image_url)

    # For each face returned use the face rectangle and draw a red box.
    print('Drawing rectangle around face... see popup for results.')
    draw = ImageDraw.Draw(img)
    for face in detected_faces:
        draw.rectangle(getRectangle(face), outline='red')

    # Display the image in the users default image browser.
    img.show()
    img.save(save_path)

# 似た顔の検索
def face_find_az(detected_faces2, first_image_face_ID, multi_image_name):
    # Search through faces detected in group image for the single face from first image.
    # First, create a list of the face IDs found in the second image.
    second_image_face_IDs = list(map(lambda x: x.face_id, detected_faces2))
    # Next, find similar face IDs like the one detected in the first image.
    similar_faces = face_client.face.find_similar(face_id=first_image_face_ID, face_ids=second_image_face_IDs)
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
    print(face_info)
    return face_info


def similar_face_rectangle():
    single_face_image_url = image # 画像のパス
    single_image_name = os.path.basename(single_face_image_url) # ファイル名の取得
    single_face_data = open(image, 'rb') # 画像の読み込み
    _, first_image_face_ID = face_detected(single_face_data, single_image_name) # 顔の検出
    """face_rectangle_az(single_face_image_url, detected_faces) # 検出した顔を枠で囲う"""
    multi_face_image_url = 'image/sample20.jpg' # 複数人の画像のパス
    multi_image_name = os.path.basename(multi_face_image_url) # ファイル名の取得
    multi_face_data = open(multi_face_image_url, 'rb') # 画像の読み込み
    detected_faces2, _ = face_detected(multi_face_data, multi_image_name) # 顔の検出
    face_info = face_find_az(detected_faces2, first_image_face_ID, multi_image_name) # 似た顔の検出
    face_rectangle_az(multi_face_image_url, [face_info]) # 似た顔を枠で囲う


# Used in the Person Group Operations and Delete Person Group examples.
# You can call list_person_groups to print a list of preexisting PersonGroups.
# SOURCE_PERSON_GROUP_ID should be all lowercase and alphanumeric. For example, 'mygroupname' (dashes are OK).
PERSON_GROUP_ID = str('mygroupname') # assign a random ID (or name it anything)

# Used for the Delete Person Group example.
TARGET_PERSON_GROUP_ID = str('mygroupname') # assign a random ID (or name it anything)


def face_traning():
    '''
    Create the PersonGroup
    '''
    # Create empty Person Group. Person Group ID must be lower case, alphanumeric, and/or with '-', '_'.
    print('Person group:', PERSON_GROUP_ID)
    face_client.person_group.create(person_group_id=PERSON_GROUP_ID, name=PERSON_GROUP_ID)

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
    # Identify faces
    results = face_client.face.identify(face_ids, PERSON_GROUP_ID)
    print('Identifying faces in {}'.format(os.path.basename(image.name)))
    result_faces = []
    result_name_id = []
    if not results:
        print('No person identified in the person group for faces from {}.'.format(os.path.basename(image.name)))
    for person in results:
        if len(person.candidates) > 0:
            #result_faces.append(detected_faces3.face_id[person.face_id])
            for detected in detected_faces3:
                if detected.face_id == person.face_id:
                    result_faces.append(detected)
                    result_name_id.append(person.candidates[0].person_id)
                    
            print('Person for face ID {} is identified in {} with a confidence of {}.'.format(person.face_id, os.path.basename(image.name), person.candidates[0].confidence)) # Get topmost confidence score
        else:
            print('No person identified for face ID {} in {}.'.format(person.face_id, os.path.basename(image.name)))
    #print(result_name)
    return result_faces, result_name_id


if __name__ == '__main__':
    #face_traning()
    test_image = 'image/sample17.jpg'
    test_image_name = os.path.basename(test_image) # ファイル名の取得
    test_face_data = open(test_image, 'rb')
    print('Pausing for 60 seconds to avoid triggering rate limit on free account...')
    #time.sleep (60)
    detected_faces3, image_face_ID = face_detected(test_face_data, test_image_name)
    result_faces, result_name_id = identify_faces(test_face_data, image_face_ID, detected_faces3)
    print(result_faces)
    face_rectangle_az(test_image, result_faces)
