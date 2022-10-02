import requests
import urllib.request
from imgurpython import ImgurClient
from imgurpython.helpers.error import ImgurClientRateLimitError, ImgurClientError
from os import remove, path, makedirs
from shutil import move
import cv2
from cv2 import dnn_superres


client_id = "aeef3ead2dc56ac"
client_secret = "78f9763e2bf60889920fd87dc7d6e0e51e8e9a6f"


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
                headers={'api-key': 'ce7d8fc1-8aa1-4986-9e24-9534cd6412b0'}
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
    except (ImgurClientRateLimitError, ImgurClientError, requests.exceptions.SSLError) as err:
        response = {"link": None}
    return response['link']


def delete_file(file):
    remove(file)


def archive_file(file, user):
    folder = f'./Archive/{user}'
    makedirs(folder, exist_ok=False)
    move(file, f"{folder}/{file}")
