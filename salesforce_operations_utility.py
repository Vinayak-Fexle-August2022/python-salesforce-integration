import json
from simple_salesforce import Salesforce
import os
import zipfile
from datetime import datetime
import xmltodict
import ast
import time
import xml.dom.minidom
import requests
from loguru import logger


def update_s_object_record(prod_login: Salesforce, record_id: str):
    update_payload = {
        "field__c": "value",
    }

    prod_login.Deployment_Track__c.update(record_id, update_payload)
    return True


def retrieve_metadata(sf_session: Salesforce, metadata: dict, api_version: str) -> tuple:
    """
    Triggers metadata retrieval
    returns:
    :asyncProcessId process I'd returned by salesforce to keep track of the retrieval
    """
    logger.debug(f'api_version: {api_version}')
    return sf_session.mdapi.retrieve(
        api_version=api_version,
        unpackaged=metadata
    )


def check_retrieve_status(sf_session: Salesforce, async_process_id: str) -> str:
    """
    Returns status of a retrieval process
    returns:
    :boolean value indicating whether the retrieval was successful or not.
    """
    status, _, _ = sf_session.mdapi.check_retrieve_status(async_process_id)

    while status != "Succeeded":
        status, _, _ = sf_session.mdapi.check_retrieve_status(async_process_id)
        if status == "Failed":
            return status
        time.sleep(5)
    return status


def check_deploy_status(sf_session: Salesforce, async_process_id: str, test_type: str) -> str:
    """
    Check Deployment Status
    """

    test_type_with_sleep_time_interval = {
        'NoTestRun': 10,
        'RunSpecifiedTests': 180,
        'RunLocalTests': 300,
        'RunAllTestsInOrg': 300
    }

    status = sf_session.checkDeployStatus(async_process_id)
    while status != "Succeeded":
        status = sf_session.checkDeployStatus(async_process_id).get("state")
        if status in ("Canceled", "Failed"):
            return status
        time.sleep(test_type_with_sleep_time_interval.get(test_type, 10))

    return status





def create_metadata_zip_retrieve_case(retrieved_file, file_path: str):
    """
    Store retrieved zip file from source sandbox
    """
    temp_file_path = file_path
    with open(file_path, "wb") as f:
        f.write(retrieved_file)

    return temp_file_path


def create_metadata_zip(sf_session: Salesforce, async_process_id: str, file_path: str) -> str:
    """
    Store retrieved zip file from source sandbox
    """
    retrieved_file = sf_session.mdapi.retrieve_zip(async_process_id)
    temp_file_path = file_path
    with open(file_path, "wb") as f:
        f.write(retrieved_file[-1])

    return temp_file_path


def start_deployment(sf_session: Salesforce, sandbox: bool = True, file_path: str = "metadata.zip",
                     deployment_config: dict = {}) -> dict:
    """
    Starts deployment to target sandbox
    :returns

    """
    logger.debug('file_path in start_deployment: {file_path}')

    deploy_options = {
        "checkOnly": deployment_config.get('checkOnly', False),
        "testLevel": deployment_config.get('testLevel'),
        "tests": deployment_config.get('tests', []),
        "ignoreWarnings": deployment_config.get('ignoreWarnings', True),
        "allowMissingFiles": deployment_config.get('allowMissingFiles', True),
        "autoUpdatePackage": deployment_config.get('autoUpdatePackage', True),
        "performRetrieve": deployment_config.get('performRetrieve', False),
        "purgeOnDelete": deployment_config.get('purgeOnDelete', False),
        "rollbackOnError": deployment_config.get('rollbackOnError', True),
    }

    logger.debug(f'deployment_config: {deployment_config}')

    return sf_session.deploy(file_path, sandbox=sandbox, **deploy_options)


def create_delete_package(file_path: str = "metadata.zip", mods: dict = {}) -> str:
    try:
        destructive_xml = """<?xml version="1.0" encoding="UTF-8"?><Package xmlns="http://soap.sforce.com/2006/04/metadata">"""
        package_xml = """<?xml version="1.0" encoding="UTF-8"?><Package xmlns="http://soap.sforce.com/2006/04/metadata">"""
        for key in mods:
            name = f"<name>{key}</name>"
            members = ""
            for j in mods[key]:
                members += f"<members>{j}</members>"
            destructive_xml += f"<types>{members}{name}</types>"

        destructive_xml += """<version>58.0</version></Package>"""
        package_xml += """<version>58.0</version></Package>"""

        with open('destructiveChanges.xml', 'w') as f:
            f.write(destructive_xml)
        with open('package.xml', 'w') as f:
            f.write(package_xml)
        with zipfile.ZipFile(file_path, mode='w') as zip_file:
            zip_file.write('destructiveChanges.xml')
            zip_file.write('package.xml')

        return file_path
    except Exception as exc:
        logger.debug(str(exc))


def create_destructive_xml(filepath='post_destructiveChanges.xml', mods: dict = {}) -> str:
    try:
        destructive_xml = """<?xml version="1.0" encoding="UTF-8"?><Package xmlns="http://soap.sforce.com/2006/04/metadata">"""
        for key in mods:
            name = f"<name>{key}</name>"
            members = ""
            for j in mods[key]:
                members += f"<members>{j}</members>"
            destructive_xml += f"<types>{members}{name}</types>"

        destructive_xml += """<version>58.0</version></Package>"""
        temp = xml.dom.minidom.parseString(destructive_xml)
        formatted_destructive_xml = temp.toprettyxml()
        with open(filepath, 'w') as f:
            f.write(formatted_destructive_xml)

        return filepath
    except Exception as exc:
        logger.debug(str(exc))


def get_retrieval_logs(source_login: Salesforce, async_process_id: str) -> str:
    try:
        attributes = {
            'client': 'simple_salesforce_metahelper',
            'sessionId': source_login.session_id,
            'asyncProcessId': async_process_id,
            'includeZip': 'false',  # we cant use both zip and details in xml
            'includeDetails': 'true'
        }
        RETRIEVE_LOG_MSG = \
            """<soapenv:Envelope
        xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:met="http://soap.sforce.com/2006/04/metadata">
           <soapenv:Header>
              <met:CallOptions>
                 <met:client>{client}</met:client>
              </met:CallOptions>
              <met:SessionHeader>
                 <met:sessionId>{sessionId}</met:sessionId>
              </met:SessionHeader>
           </soapenv:Header>
           <soapenv:Body>
              <met:checkRetrieveStatus>
                 <met:asyncProcessId>{asyncProcessId}</met:asyncProcessId>
                 <met:includeDetails>{includeDetails}</met:includeDetails>
              </met:checkRetrieveStatus>
           </soapenv:Body>
        </soapenv:Envelope>"""
        mt_request = RETRIEVE_LOG_MSG.format(**attributes)
        headers = {
            'Content-type': 'text/xml', 'SOAPAction': 'checkRetrieveStatus'
        }

        from simple_salesforce.util import call_salesforce
        res = call_salesforce(
            url=source_login.metadata_url + 'deployRequest/' + async_process_id,
            method='POST',
            session=source_login.session,
            headers=source_login.headers,
            additional_headers=headers,
            data=mt_request)

        return res.text

    except Exception as exc:
        logger.debug(str(exc))


def update_report(prod_conn: Salesforce, record_id, report_id: str = ""):
    report_details = prod_conn.restful('analytics/reports/{}'.format(report_id), method='GET')
    filter_details = {"reportMetadata": {"reportFilters": []}}
    # Modify the filter parameters
    for i, filter_item in enumerate(report_details['reportMetadata']['reportFilters']):
        if filter_item['column'] == 'SFDC_Change_Request__c.Name':
            # Modify the filter value as needed
            filter_item['value'] = record_id
            filter_details['reportMetadata']['reportFilters'].append(filter_item)
            break

    filter_details = json.dumps(filter_details)

    # Update the report with modified filter parameters
    response = prod_conn.restful('analytics/reports/{}'.format(report_id), method='PATCH', data=filter_details)


def delete_attached_backup(sf_conn: Salesforce, record_id: str):


    # update query according to your need
    query = f"""SELECT Id, ContentDocumentId 
                FROM ContentDocumentLink 
                WHERE LinkedEntityId = '{record_id}' 
                AND LinkedEntity.Type = 'S_Object_name__c' 
                ORDER BY ContentDocument.LastModifiedDate 
                """
    attached_documents = sf_conn.query_all(query)

    document_ids_to_delete = []

    for document in attached_documents['records']:
        document_ids_to_delete.append({'Id': document['ContentDocumentId']})

    if document_ids_to_delete:
        try:
            response = sf_conn.bulk.ContentDocument.delete(document_ids_to_delete, batch_size=200)
        except Exception as e:
            logger.debug(f"Error occurred: {e}")
    else:
        logger.debug("No AttachedContentDocument records found for deletion.")
