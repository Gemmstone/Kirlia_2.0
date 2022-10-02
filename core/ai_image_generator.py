import requests
import base64
from os.path import exists

def image(prompt):
    url = "https://backend.craiyon.com/generate"
    s = requests.Session()
    payload = {
        "prompt": prompt
    }
    res = s.post(url, json=payload)
    return res.content


def ai_image(prompt):
    # try:
    image_urls = str(image(prompt))
    image_urls = image_urls.replace('\\\\n', '')
    end_index = int(image_urls.index('],"version') - 1)
    image_urls = image_urls[14:end_index]
    image_list = image_urls.split('","')

    filenames = []
    for i in range(9):
        chosen_image = image_list[i]
        imgdata = base64.b64decode(chosen_image)
        filename = f'output_ai.jpg'
        count = 0
        while exists(filename):
            filename = f'output_ai_{count}.jpg'
            count += 1

        with open(filename, 'wb') as f:
            f.write(imgdata)
        filenames.append(filename)
    return filenames
    # except BaseException as err:
    #     print(err)
    #     return []
