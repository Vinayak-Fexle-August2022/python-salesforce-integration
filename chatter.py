from simple_salesforce import Salesforce
import requests
import json

def get_chatter_body(message: str) -> dict:
    text = message # Your chatter message

    body = {
        "messageSegments": [
            {
                "type": "Text",
                "text": "Hi "
            }, {
                "type": "Text",
                "text": ",\n"
            }, {
                "type": "Text",
                "text": text
            }, {
                "type": "Text",
                "text": "."
            }, {
                "type": "Text",
                "text": '\nThanks.'
            }
        ]
    }

    return body


def send_chatter(prod_conn: Salesforce):

    s_object_record_id = "s_object_record_id"


    body = get_chatter_body(
        message = "Your chatter message"
    )

    req_body = {
        "body": body,
        "feedElementType": "FeedItem",
        "subjectId": s_object_record_id
    }

    auth = {
        'Authorization': 'Bearer ' + prod_conn.session_id,
        'content-type': 'application/json'
    }

    req_url = prod_conn.base_url + 'chatter/feed-elements'

    chatter = requests.post(
        url=req_url,
        data=json.dumps(req_body),
        headers=auth
    )
    return chatter.status_code
