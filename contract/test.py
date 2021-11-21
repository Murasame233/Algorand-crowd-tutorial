import os
from algosdk import encoding, v2client
from algosdk.future.transaction import ApplicationCallTxn, LogicSig, ApplicationCreateTxn, ApplicationDeleteTxn, ApplicationNoOpTxn, ApplicationOptInTxn, LogicSigTransaction, OnComplete, PaymentTxn, StateSchema, assign_group_id
import dotenv
import base64
from time import sleep

import msgpack

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
e = encoding.msgpack_encode(create_txn);
c:ApplicationCallTxn = encoding.future_msgpack_decode(e);

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

print("Now update the escrow")

# update the escrow
compiled_escrow = LogicSig(base64.b64decode(client.compile(
    open(base + "/build/escrow.teal").read().replace("123456", str(app_id)))["result"]))
escrow = compiled_escrow.address()

print(escrow)

client.send_transaction(ApplicationNoOpTxn(
    address_a,
    sp,
    app_id,
    [
        "update",
        encoding.decode_address(escrow)
    ]
).sign(private_key_a))

print("wait for 10 sec to comfirm the txn.")
sleep(10)

# update end

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
            100000
        )
    ]
)

client.send_transactions(
    [donate[0].sign(private_key_b), donate[1].sign(private_key_b)])

print("wait for 10 sec to comfirm the txn.")
sleep(10)

# claim

claim = assign_group_id(
    [
        ApplicationNoOpTxn(
            address_a,
            sp,
            app_id,
            ["claim"]
        ),
        PaymentTxn(
            escrow,
            sp,
            address_a,
            0,
            address_a
        )
    ]
)

client.send_transactions([
    claim[0].sign(private_key_a),
    LogicSigTransaction(claim[1], compiled_escrow)
])

print("wait for 10 sec to comfirm the txn.")
sleep(10)

# Delete App
delete_txn = ApplicationDeleteTxn(address_a, sp, app_id)
client.send_transaction(delete_txn.sign(private_key_a))
