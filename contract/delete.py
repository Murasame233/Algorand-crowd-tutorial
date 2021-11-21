import os
from algosdk import v2client
from algosdk.future.transaction import ApplicationCreateTxn, ApplicationDeleteTxn, OnComplete, StateSchema
import dotenv
import base64
from time import sleep

dotenv.load_dotenv()

private_key_a = os.environ.get("ACCOUNT_A_KEY")
address_a = os.environ.get("ACCOUNT_A")

private_key_b = os.environ.get("ACCOUNT_B_KEY")
address_b = os.environ.get("ACCOUNT_B")

endpoint_address = os.environ.get("ALGOD_ADDRESS")
api_key = os.environ.get("TOKEN")

api_header = {'X-Api-key': api_key}

client = v2client.algod.AlgodClient(
    api_key, endpoint_address, headers=api_header)

print("client created")

apps = client.account_info(address_a)["created-apps"]
sp = client.suggested_params()

args = ["delete"]

for app in apps:
    app_id = app["id"]
    print(app_id)
    delete_txn = ApplicationDeleteTxn(address_a, sp, app_id,args)
    client.send_transaction(delete_txn.sign(private_key_a))









