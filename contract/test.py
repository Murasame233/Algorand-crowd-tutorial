import os
from algosdk import encoding, v2client,mnemonic
from algosdk.future.transaction import ApplicationCallTxn, LogicSig, ApplicationCreateTxn, ApplicationDeleteTxn, ApplicationNoOpTxn, ApplicationOptInTxn, LogicSigTransaction, OnComplete, PaymentTxn, StateSchema, assign_group_id
import dotenv
import base64
from time import sleep

import msgpack

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

base = os.path.dirname(os.path.abspath(__file__))

contract = base64.b64decode(client.compile(
    open(base + "/build/contract.teal").read())["result"])
clear = base64.b64decode(client.compile(
    open(base + "/build/clear.teal").read())["result"])

print("Contract compiled")

sp = client.suggested_params()

# Create App
create_txn = ApplicationCreateTxn(
    address_a,
    sp,
    OnComplete.NoOpOC,
    contract,
    clear,
    StateSchema(2, 2),
    StateSchema(0, 0),
    [
        100000
    ]
)
e = encoding.msgpack_encode(create_txn)
c: ApplicationCallTxn = encoding.future_msgpack_decode(e)

create_txn_signed = c.sign(private_key_a)

tx_id = create_txn_signed.get_txid()

client.send_transaction(create_txn_signed)

print(tx_id)
print("wait for 10 sec to comfirm the txn.")
sleep(10)

# get App id
app_id = client.pending_transaction_info(tx_id)["application-index"]
print(app_id)
# Create End

escrow = encoding.encode_address(
    encoding.checksum(b'appID' + app_id.to_bytes(8, 'big'))
)

# donate
donate = assign_group_id(
    [
        ApplicationNoOpTxn(
            address_b,
            sp,
            app_id,
            ["donate"]
        ),
        PaymentTxn(
            address_b,
            sp,
            escrow,
            1000000
        )
    ]
)

client.send_transactions(
    [donate[0].sign(private_key_b), donate[1].sign(private_key_b)])

print("wait for 10 sec to comfirm the txn.")
sleep(10)

# claim

claim = ApplicationNoOpTxn(
    address_a,
    sp,
    app_id,
    ["claim"]
)

client.send_transaction(claim.sign(private_key_a))

print("wait for 10 sec to comfirm the txn.")
sleep(10)

# Delete App
delete_txn = ApplicationDeleteTxn(address_a, sp, app_id)
client.send_transaction(delete_txn.sign(private_key_a))
