import os
from algosdk import v2client,mnemonic
from algosdk.future.transaction import ApplicationCreateTxn, ApplicationDeleteTxn, OnComplete, StateSchema
import dotenv
import base64
from time import sleep

dotenv.load_dotenv()

A = os.environ.get("ACCOUNT_A")
B = os.environ.get("ACCOUNT_B")
private_key_a = mnemonic.to_private_key(A)
address_a = mnemonic.to_public_key(A)

private_key_b = mnemonic.to_private_key(B)
address_b = mnemonic.to_public_key(B)

algod_address = "http://localhost:4001"
algod_token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

client = v2client.algod.AlgodClient(algod_token, algod_address)

print("client created")

apps = client.account_info(address_a)["created-apps"]
sp = client.suggested_params()

args = ["delete"]

for app in apps:
    app_id = app["id"]
    print(app_id)
    delete_txn = ApplicationDeleteTxn(address_a, sp, app_id,args)
    client.send_transaction(delete_txn.sign(private_key_a))









