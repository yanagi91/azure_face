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


image = 'image/14.ga.jpg'
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
    first_image_face_ID = detected_faces[0].face_id
    return detected_faces, first_image_face_ID

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
def face_find_az(detected_faces2, first_image_face_ID):
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

if __name__ == '__main__':
    single_face_image_url = image
    single_image_name = os.path.basename(single_face_image_url)
    single_face_data = open(image, 'rb')
    detected_faces, first_image_face_ID = face_detected(single_face_data, single_image_name)
    """face_rectangle_az(single_face_image_url, detected_faces) """
    multi_face_image_url = 'image/sample20.jpg'
    multi_image_name = os.path.basename(multi_face_image_url)
    multi_face_data = open(multi_face_image_url, 'rb')
    detected_faces2, multi_image_face_ID = face_detected(multi_face_data, multi_image_name)
    face_info = face_find_az(detected_faces2, first_image_face_ID)
    face_rectangle_az(multi_face_image_url, [face_info])
