from loguru import logger
import requests
import base64


def get_encoded_file_content(file_path):
    with open(file_path, "rb") as f:
        encoded_content = base64.b64encode(f.read()).decode('utf-8')
    return encoded_content


def create_content_version(sf_session, file_path, file_title):
    encoded_string = get_encoded_file_content(file_path)
    url = sf_session.base_url + "sobjects/ContentVersion"
    headers = {
        "Authorization": "Bearer " + sf_session.session_id,
        "Content-Type": "application/json"
    }
    data = {
        'Title': file_title,  # You may want to adjust the title accordingly
        'PathOnClient': file_path,
        'VersionData': encoded_string,
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_content_document_id(sf_session, content_version_id):
    url = sf_session.base_url + f"sobjects/ContentVersion/{content_version_id}"
    headers = {
        "Authorization": "Bearer " + sf_session.session_id,
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get('ContentDocumentId')


def create_content_document_link(sf_session, content_document_id, record_id: str):
    url = sf_session.base_url + "sobjects/ContentDocumentLink"
    headers = {
        "Authorization": "Bearer " + sf_session.session_id,
        "Content-Type": "application/json"
    }
    data = {
        'ContentDocumentId': content_document_id,
        'LinkedEntityId': record_id,
        'ShareType': 'V'  # V stands for Viewer access; adjust as per your requirement
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json().get('id')


def attach_file_on_salesforce_sobject_record(sf_session, record_id, file_path, file_title):
    try:
        content_version = create_content_version(sf_session, file_path, file_title)
        content_document_id = get_content_document_id(sf_session, content_version['id'])
        content_document_link_id = create_content_document_link(sf_session, content_document_id, record_id)
        return content_document_link_id
    except requests.exceptions.RequestException as e:
        logger.debug(f"API Request Error: {e}")
        return False
