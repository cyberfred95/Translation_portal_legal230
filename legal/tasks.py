from os.path import basename, splitext
import requests
from . import keys
from typing import Tuple
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


def get_files_processing_api_url(document_content_type):
    return f"{keys.FILES_PROCESSING_API_URL}/api/{files_processing_api_path_mapping[document_content_type]}"


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
