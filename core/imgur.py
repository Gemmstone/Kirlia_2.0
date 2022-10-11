import requests
import urllib.request
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientRateLimitError, ImgurClientError
from os import remove, path, makedirs
from shutil import move
import cv2
from cv2 import dnn_superres
from constants import IMGUR_TOKEN, DEEP_AI_KEY

import numpy as np
from PIL import Image


client_id = IMGUR_TOKEN["client_id"]
client_secret = IMGUR_TOKEN["client_secret"]


def fsr_x2(file, replace=True, times=2):
    sr = dnn_superres.DnnSuperResImpl_create()
    path = "FSRCNN_x2.pb"
    sr.readModel(path)
    sr.setModel("fsrcnn", 2)
    image = cv2.imread(file)
    for i in range(times):
        image = sr.upsample(image)
    if replace:
        cv2.imwrite(file, image)
    else:
        cv2.imwrite("resized.jpeg", image)
        file = "resized.jpeg"
    return file


def download_attachment(bytes, file="local-filename.jpg"):
    with open(file, "wb") as f:
        f.write(bytes.read())


def download_image(url, file="local-filename.jpg"):
    urllib.request.urlretrieve(url, file)


def image_resize(files, online=False):
    for file in files:
        if online:
            r = requests.post(
                "https://api.deepai.org/api/torch-srgan",
                files={
                    'image': open(file, 'rb'),
                },
                headers={'api-key': DEEP_AI_KEY}
            )
            url = r.json()
            if "output_url" in url:
                download_image(url["output_url"])
            else:
                print(url["status"])
        else:
            try:
                fsr_x2(file)
            except BaseException as e:
                print(e)
    return files


def image_upload(file):
    try:
        client = ImgurClient(client_id, client_secret)
        response = client.upload_from_path(file)
    except (ImgurClientRateLimitError, ImgurClientError, requests.exceptions.SSLError, requests.exceptions.ConnectTimeout) as err:
        response = {"link": None}
    return response['link']


def delete_file(file):
    remove(file)


def archive_file_dalle(file, messageid, number):
    folder = f'./ArchiveDalle/{messageid}'
    makedirs(folder, exist_ok=True)
    move(file, f"{folder}/{number}.jpg")


def archive_file(file, user):
    folder = f'./Archive/{user}'
    makedirs(folder, exist_ok=True)
    move(file, f"{folder}/{file}")


def combine_pictures(list_im: list, orientation: bool = 1, filename: str = "combined_pictures.jpg", delete_files=False):
    imgs = [Image.open(i) for i in list_im]
    min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
    imgs_comb = np.hstack((np.asarray(i.resize(min_shape)) for i in imgs))

    if orientation:  # Horizontal orientation
        imgs_comb = Image.fromarray(imgs_comb)
        imgs_comb.save(filename)
    else:  # Vertical orientation
        imgs_comb = np.vstack((np.asarray(i.resize(min_shape)) for i in imgs))
        imgs_comb = Image.fromarray(imgs_comb)
        imgs_comb.save(filename)
    for img in imgs:
        img.close()
    if delete_files:
        for file in list_im:
            delete_file(file)
    return filename


def chunkIt(files: list, num: int = 3):
    avg = len(files) / float(num)
    out = []
    last = 0.0
    while last < len(files):
        out.append(files[int(last):int(last + avg)])
        last += avg
    return list(out)
