import argparse
import requests
from requests import HTTPError
from requests import ConnectionError
from dotenv import load_dotenv
from os import getenv
from googletrans import Translator


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
    translator_response, *_ = translator.translate(
        phrase,
        src='en',
        dest='ru'
        )
    return translator_response.text


def translate_yandex(phrase):
    translate_key = getenv("YANDEX_IAM_TOKEN")
    folder_id = getenv("FOLDER_ID")
    headers = {"Authorization": "Bearer {}".format(translate_key)}
    params = {
              "texts": phrase,
              "sourceLanguageCode": "en",
              "targetLanguageCode": "ru",
              "folder_id": folder_id
              }
    try:
        response = requests.post(
            "https://translate.api.cloud.yandex.net/translate/v2/translate",
            params=params,
            headers=headers
        )
        response.raise_for_status()
        translations = response.json()["translations"]
    except (ConnectionError, HTTPError):
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
    try:
        translate_service = translate_service_map[service]
        print(translate_service(phrase))
    except (ConnectionError, HTTPError):
        pass
