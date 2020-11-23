import argparse
import requests
from requests import HTTPError
from requests import ConnectionError
from dotenv import load_dotenv
import dotenv
from os import getenv
import os
from googletrans import Translator
import json
import time
import jwt
from jwt.contrib.algorithms.pycrypto import RSAAlgorithm


def get_args():
    script_usage = "python translator.py  <phrase to translate>"
    parser = argparse.ArgumentParser(
        description="How to run translator.py:",
        usage=script_usage
    )
    parser.add_argument(
        "service",
        choices=['yandex', 'google'],
        nargs='+',
        help="Specify the service you will use"
    )
    parser.add_argument(
        "phrase",
        nargs='+',
        help="Specify the phrase to translate"
    )
    args = parser.parse_args()
    return args


def translate_google(phrase):
    translator = Translator()
    while True:
        try:
            translator_response, *_ = translator.translate(
                phrase,
                src='en',
                dest='ru'
                )
            return translator_response.text
        except AttributeError:
            translator = Translator()
        except (ConnectionError, HTTPError):
            return


def get_yandex_iam_token(jwt_token):
    headers = {"Content-Type": "application/json"}
    params = {"jwt": jwt_token}
    try:
        response = requests.post(
                "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                params=params,
                headers=headers
            )
    except (ConnectionError, HTTPError):
        return
    return response.json()["iamToken"]


def generate_yandex_jwt_token():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(script_dir, "key.json")
    with open(key_file, 'r') as file_handler:
        data = json.load(file_handler)
        service_account_id = data["service_account_id"]
        key_id = data["id"]
        private_key = data["private_key"]
    
    now = int(time.time())
    payload = {
        'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        'iss': service_account_id,
        'iat': now,
        'exp': now + 360,
        }
    encoded_token = jwt.encode(
        payload,
        private_key,
        algorithm='PS256',
        headers={'kid': key_id},
        )
    return encoded_token


def update_iam_token(iam_token):
    dotenv_file = dotenv.find_dotenv()
    dotenv.load_dotenv(dotenv_file)
    os.environ["YANDEX_IAM_TOKEN"] = iam_token
    dotenv.set_key(
        dotenv_file,
        "YANDEX_IAM_TOKEN",
        os.environ["YANDEX_IAM_TOKEN"]
        )


def translate_yandex(phrase):
    while True:
        try:
            translate_key = getenv("YANDEX_IAM_TOKEN")
            folder_id = getenv("FOLDER_ID")
            headers = {"Authorization": "Bearer {}".format(translate_key)}
            params = {
                      "texts": phrase,
                      "sourceLanguageCode": "en",
                      "targetLanguageCode": "ru",
                      "folder_id": folder_id
                      }
            response = requests.post(
                "https://translate.api.cloud.yandex.net/translate/v2/translate",
                params=params,
                headers=headers
                )
            response.raise_for_status()
            translations = response.json()["translations"]
        except (ConnectionError, HTTPError):
            if response.json()["code"] == 16:
                jwt_token = generate_yandex_jwt_token()
                iam_token = get_yandex_iam_token(jwt_token)
                update_iam_token(iam_token)
                continue
            else:
                return            
        for translation in translations:
            return translation["text"].replace("+", " ")


if __name__ == '__main__':
    args = get_args()
    load_dotenv()
    phrase = args.phrase
    service = ''.join(args.service)
    translate_service_map = {
        'yandex': translate_yandex,
        'google': translate_google
    }
    translate_service = translate_service_map[service]
    print(translate_service(phrase))
