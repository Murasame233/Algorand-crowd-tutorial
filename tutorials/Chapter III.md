# Chaper III

In this chapter we will test our contract.

# Pre

## Algod Api

install the `algorand sandbox` for algod or use `purestake`'s api.

- [algorand sandbox](https://github.com/algorand/sandbox)
- [Purestake](https://www.purestake.com/technology/algorand-api/)

You will get the algod address and a token.
Write these to the `.env` file.

## Ready two account

The algorand sdk can have generate account, so we generate two account and use [faucet](https://bank.testnet.algorand.network/) to charge it.

```python
import algosdk
private_a, address_a = algosdk.account.generate_account()
private_b, address_b = algosdk.account.generate_account()

print("A:\nprivate key: " + private_a + "\naddress: " + address_a);
print("B:\nprivate key: " + private_b + "\naddress: " + address_b);
```

# Test with Python

Create a file called `test.py`

And we define the api_key, api_address, address and private key in the `.env` file like this:

```
ACCOUNT_A_KEY={}
ACCOUNT_A={}

ACCOUNT_B_KEY={}
ACCOUNT_B={}

ALGOD_ADDRESS={}
TOKEN={}
```

And parse this file into `test.py`.

```
import os
import dotenv

dotenv.load_dotenv()

private_key_a = os.environ.get("ACCOUNT_A_KEY")
address_a = os.environ.get("ACCOUNT_A")

private_key_b = os.environ.get("ACCOUNT_B_KEY")
address_b = os.environ.get("ACCOUNT_B")


endpoint_address = os.environ.get("ALGOD_ADDRESS")
api_key = os.environ.get("TOKEN")
```

## Algod client

All of requests are through the algod api.

So we need a algod client

```python
api_header = {'X-Api-key': api_key}

client = v2client.algod.AlgodClient(
    api_key, endpoint_address, headers=api_header)
```

## Compile the contract

use client to compile the contract

```python
base = os.path.dirname(os.path.abspath(__file__))

contract = base64.b64decode(client.compile(open(base + "/build/contract.teal").read())["result"])
clear = base64.b64decode(client.compile(open(base + "/build/clear.teal").read())["result"])
```

> use conpile function will return a dict have two value:
>
> - hash (escrow address)
> - result (compiled bytes, base64 encoded)
>
> So we need compile it and decode the `result` with base 64.

## Create Application

> When we make transaction, we need to pass the suggest param.
>
> And we can use `client.suggested_params()` to get a suggested param.

We got the compiled contract, now we can deploy it.

According to last chapter. When we create a contract we need pass args to it.

Code:

```python
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
```

And we need to send this transaction after signed and get the app_id.

```python
create_txn_signed = create_txn.sign(private_key_a)

tx_id = create_txn_signed.get_txid()

client.send_transaction(create_txn_signed)

print(tx_id)
print("wait for 10 sec to comfirm the txn.")
sleep(10)

# get App id
app_id = client.pending_transaction_info(tx_id)["application-index"]
print(app_id)
```

## Update the escrow

Use escrow to sign a transaction called logicsign, So we need make a Logicsig by compile the contract.

And the logicsig need the compiled bytes.

The escrow address can be get from `LogicSig.address()`

And we have to replace the placeholder `123456` to our app_id.

Code:

```python
compiled_escrow = LogicSig(base64.b64decode(client.compile(open(base + "/build/escrow.teal").read().replace("123456", str(app_id)))["result"]))

escrow = compiled_escrow.address()

print(escrow)
```

And make a application call to update.

```python
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
```

> when we need pass an address as args into application call, we need to use `encoding.decode_address(address)` to encode the address. Then pass it into the call.

## Donate

All ready has been done. So we can use another account `address_b` to donate this escrow.

```python
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
    [
        donate[0].sign(private_key_b),
        donate[1].sign(private_key_b)
    ]
)

print("wait for 10 sec to comfirm the txn.")
sleep(10)
```

> we can use assign_group_id to make a group transactions.

## claim

The donation has been done, the user a can claim the donate now.

```python
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
```

> use `LogicSigTransaction(Txn,LogicSig)` to sign a txn which need escrow to sign.

## close

Now we can close the application

```python
delete_txn = ApplicationDeleteTxn(address_a, sp, app_id)
client.send_transaction(delete_txn.sign(private_key_a))
```

# final test code

```python
import os
from algosdk import encoding, v2client
from algosdk.future.transaction import LogicSig, ApplicationCreateTxn, ApplicationDeleteTxn, ApplicationNoOpTxn, ApplicationOptInTxn, LogicSigTransaction, OnComplete, PaymentTxn, StateSchema, assign_group_id
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

create_txn_signed = create_txn.sign(private_key_a)

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

```
