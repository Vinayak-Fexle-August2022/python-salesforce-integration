import os
import traceback
from attach_zip_file_on_salesforce_recordt import attach_backup
from chatter import send_chatter
from salesforce_operations_utility import *
from sf_connection import *
from attach_zip_file_on_salesforce_recordt import attach_file_on_salesforce_sobject_record
from chatter import send_chatter

def handler(): 
    try:

        # CONNECTING TO THE SALESFORCE ORG 
        prod_login = connect_instance(
            instance_url= "YOUR ORG INSTANCE URL",
            access_token=update_token(
                url="YOUR ORG INSTANCE URL",
                refresh_token="YOUR REFRESH TOKEN",
                client_id="YOUR CLIENT ID",
                client_secret="YOUR CLIENT_SECRET",
            )
        )

        print("logged into production")
    
        # WRITE YOUR LOGIC HERE
        
    except Exception as err:
        # Print error in detail
        print(traceback.format_exc())