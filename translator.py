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
    translate_key = getenv("YANDEX_API_KEY")
    params = {
              "key": translate_key,
              "text": phrase,
              "lang": "en-ru"
              }
    response = requests.get(
        "https://translate.yandex.net/api/v1.5/tr.json/translate",
        params=params
    )
    response.raise_for_status()
    content = dict(response.json())
    return ''.join(content.get("text"))


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
