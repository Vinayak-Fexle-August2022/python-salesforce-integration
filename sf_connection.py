from simple_salesforce import Salesforce
import requests
import json
from loguru import logger


def connect_instance(instance_url: str, access_token: str) -> Salesforce:
    """
    Creates a sandbox login session using refresh_token
    """
    return Salesforce(
        session_id=access_token,
        instance_url=instance_url,
    )


def update_token(
        url: str, refresh_token: str, client_id: str, client_secret: str
) -> str:
    headers = {
        "Cookie": "BrowserId=HDgNcbENEe2E_Fv37y8_5g; CookieConsentPolicy=0:1; LSKey-c$CookieConsentPolicy=0:1"
    }
    url = url + "/services/oauth2/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return json.loads(response.content).get("access_token")


def connect_org(
        username: str, password: str, security_token: str, domain: str = "test"
) -> Salesforce:
    """
    Creates an org connection.
    """
    try:
        return Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain=domain,
        )
    except Exception as exc:
        logger.debug(str(exc))









