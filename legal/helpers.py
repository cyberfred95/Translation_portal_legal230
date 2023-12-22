from google.oauth2 import service_account
from google.cloud import automl
from google.cloud.translate_v3 import TranslationServiceAsyncClient, TranslationServiceClient, TranslateDocumentRequest
from google.cloud.translate_v3.types import DocumentInputConfig
from google.cloud import translate_v2 as translate
import html
import requests
import ast
from datetime import datetime
from azure.core.credentials import AzureKeyCredential, AccessToken
from azure.ai.translation.document import DocumentTranslationClient
from azure.storage.blob import ContainerClient, \
    BlobServiceClient, PublicAccess, generate_blob_sas, BlobSasPermissions, generate_container_sas, \
    ContainerSasPermissions
import uuid
import modernmt
from .keys import MS_ACCESS_TOKEN, MS_CONNECTION, MS_ENDPOINT, MS_AZURE_ENDPOINT, FILES_PROCESSING_API_URL
from typing import Tuple
from os.path import basename, splitext
import json
files_processing_api_path_mapping = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "word"
}

class DocumentInfo:
    def __init__(self, document_info: Tuple[str, str]):
        if not document_info[0] in files_processing_api_path_mapping:
            raise ValueError(f"Content type {document_info[0]} not supported")
        self.content_type = document_info[0]
        self.file_path = document_info[1]
        with open(self.file_path, "rb") as temp:
            self.file_content = temp.read()

        self.file_name = basename(self.file_path)
        self.file_extension = splitext(self.file_name)[1].lower()


class MicrosoftCustomProvider:
    micro_url = 'https://api.cognitive.microsofttranslator.com/translate'

    def __init__(self, key, category, source_lang, target_lang):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.__key = key
        print(self.__key)
        self.__category = category
        print(self.__category)

    def translate(self, data):
        micro_headers = {
            'Ocp-Apim-Subscription-Key': self.__key,
            'Ocp-Apim-Subscription-Region': 'global'
        }
        params = {
            'api-version': '3.0',
            'from': self.source_lang,
            'to': self.target_lang,
            'category': self.__category
        }
        body = [{'text': data}]
        print(micro_headers)
        print(body)
        print(params)
        result = requests.post(url=self.micro_url, params=params, headers=micro_headers, json=body)
        result_json = result.json()
        print(result_json)
        print(result_json)
        return html.unescape(result_json[0]['translations'][0]['text'])

    def translate_file(self, file, mime_type):
        container_name = str(uuid.uuid4())

        source_container_client = ContainerClient.from_connection_string(
            MS_CONNECTION,
            container_name=container_name
        )
        source_container_client.create_container()
        target_container_client = ContainerClient.from_connection_string(
            MS_CONNECTION,
            container_name=container_name + '-trans'
        )
        target_container_client.create_container()

        blob_service_client = BlobServiceClient.from_connection_string(
            MS_CONNECTION)
        file_name = container_name + '.' + mime_type
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)

        blob_client.upload_blob(file)
        key = self.__key
        endpoint = MS_AZURE_ENDPOINT
        sourcer_sas = '?' + generate_container_sas(
            'legal230storage',
            container_name=container_name,
            account_key=MS_ACCESS_TOKEN,
            permission=ContainerSasPermissions(read=True, write=True, list=True),
            expiry='2032-05-25T14:35:12Z',
            start='2022-05-25T14:35:12Z'
        )
        target_sas = '?' + generate_container_sas(
            'legal230storage',
            container_name=container_name + '-trans',
            account_key=MS_ACCESS_TOKEN,
            permission=ContainerSasPermissions(read=True, write=True, list=True),
            expiry='2032-05-25T14:35:12Z',
            start='2022-05-25T14:35:12Z'
        )
        sourceUrl = MS_ENDPOINT + container_name + sourcer_sas
        targetUrl = MS_ENDPOINT + container_name + '-trans' + target_sas
        client = DocumentTranslationClient(endpoint, AzureKeyCredential(key))
        poller = client.begin_translation(sourceUrl, targetUrl, self.target_lang, category_id=self.__category)
        poller.result()
        result = target_container_client.download_blob(container_name + '.' + mime_type).readall()
        target_container_client.delete_container()
        source_container_client.delete_container()
        return result


class ModernMTProvider:

    def __init__(self, credentials, source_lang, target_lang):
        self.__api_key = None
        self.__creds = credentials
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.is_user_creds_stock_provider = False
        self.set_credentials()

    def set_credentials(self):
        self.__api_key = self.__creds['key']

    def translate(self, data):
        mmt = modernmt.ModernMT(self.__api_key)
        translated_text = []
        result = mmt.translate(self.source_lang, self.target_lang, data)
        translated_text.append(result.translation)
        return translated_text

    def translate_from_file(self, data):
        mmt = modernmt.ModernMT(self.__api_key)
        translated_text = []
        source_text = [x for x in data if x != '']

        for sentence in source_text:
            result = mmt.translate(self.source_lang, self.target_lang, sentence)
            translated_text.append(result.translation)

        return translated_text

    @staticmethod
    def get_memories_list(api_key: str):
        mmt = modernmt.ModernMT(api_key)
        return mmt.memories.list()


def get_files_processing_api_url(document_content_type):
    return f"{FILES_PROCESSING_API_URL}/api/{files_processing_api_path_mapping[document_content_type]}"


def extract_texts_from_document(document_info: DocumentInfo):
    headers = {
        "Content-Type": document_info.content_type,
        "Content-Disposition": f'attachment; filename="{document_info.file_name}"',
    }

    api_url = get_files_processing_api_url(document_info.content_type)
    r = requests.post(api_url + "/export", data=document_info.file_content, headers=headers)
    return r.json()


def create_translated_document(document_info: DocumentInfo, texts_object, translated_texts):
    for i in range(len(translated_texts)):
        translated_text = translated_texts[i]
        texts_object["texts"][i]["text"] = translated_text

    files = [
        (
            "json",
            (
                "input.json",
                json.dumps(texts_object),
                "application/json",
            ),
        ),
        (
            "file",
            (
                document_info.file_name,
                document_info.file_content,
                document_info.content_type,
            ),
        ),
    ]

    api_url = get_files_processing_api_url(document_info.content_type)
    r = requests.post(api_url + "/create", files=files)
    return r.content


def run_modernmt_file_translation(document, creds, source_language, target_language):
    try:
        document_info = DocumentInfo(document_info=document)
    except ValueError:
        return False

    text_objects = extract_texts_from_document(document_info)
    source_texts: list[str] = [text_object["text"] for text_object in text_objects["texts"]]
    translated_text = ModernMTProvider(credentials=creds,
                                       source_lang=source_language,
                                       target_lang=target_language).translate_from_file(source_texts)

    return create_translated_document(document_info, text_objects, translated_text)