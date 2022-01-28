# CrowdFunding Contract Use Python

## Pre requirements

- `Python @latest`
- `Node.js @LTS`
- `CMake`

You'd better have python experience for smart contract dev.

You'd better have nodejs experience for DApp dev.

## folder struct

```
.
├── Makefile // Some fast command
├── README.md
├── Tutorial.md
├── contract // Smart contract folder
│   ├── env // Python venv folder
│   └── requirements.txt // Python installed package

```

# Steps

## PrePare the Python virtual env

```
cd contract
python -m venv env // create the python virtual env
source env/bin/activate // activate the python virtual env

pip install --upgrade pip
pip install pyteal
pip install python-dotenv
```

This will create virtual env on the contract folder, and install the packages we needed.

Needed python package.

- `pyteal`
- `python-dotenv`

From now, when you run the python script, make sure you are under the virtual env.

> when you under virtual env, your shell will be like this:
>
> ```bash
> (env) ~/workfolder/contract ➜
> ```

## Contract - `contract.py`

#### Design

Thanks to [AVM 1.0](https://developer.algorand.org/articles/discover-avm-10/), we can use stateful contract as escrow now.

Our contract have two functions:

- claim
- donate

So we decide to use donate to record the donation.

#### Code

##### Basic Struct

```python
from pyteal import *;

def contract():
    return
```

##### Dispatch call

1. why when application id is 0, we run create?

   > When create application, the id field will be 0.

2. why we dispatch call when we are sure the onComplete is NoOp?
   > When we run on the main cond, we have to sure it's a NoOp call then access the `args[0]`. If not, the `args[0]` will be not exist, will cause the error.

```python
call = Cond(
    [Txn.application_args[0] == Bytes("donate"), donate],
    [Txn.application_args[0] == Bytes("claim"), claim],
)

return Cond(
    [Txn.application_id() == Int(0), on_create],
    [Txn.on_completion() == OnComplete.DeleteApplication, delete_app],
    [Txn.on_completion() == OnComplete.NoOp, call]
)
```

##### Handle the create

The create likes a init function in the OOP. We have to init the state on the create.

And every crowdfunding need a goal, so we use arg to receive it. Before store int from arg, we have to use `Btoi` to convert it because the args are bytes in default.

```python
on_create = Seq([
    # valid the args length
    Assert(Txn.application_args.length() == Int(1)),
    # store the goal
    App.globalPut(Bytes("Goal"), Btoi(Txn.application_args[0])),
    # set amount to zero
    App.globalPut(Bytes("Amount"), Int(0)),
    # return success
    Approve()
])
```

##### Helper Function

We can define helper function for future use, like:

```python
current = Global.current_application_address()
is_creator = Txn.sender() == Global.creator_address()
```

##### Donate and Claim

When we donate, we need two transaction:

- Application Call
- Payment to Escrow

`Log` function only receive bytes parameter, we must convert amount to bytes by `Itob`.

```python
donate = Seq([
    # Must be a size 2 transaction group
    Assert(Global.group_size() == Int(2)),
    # The donate reciever must be the escrow
    Assert(Gtxn[1].receiver() == current),
    # Add new donate to total
    App.globalPut(Bytes("Amount"), Gtxn[1].amount()+App.globalGet(Bytes("Amount"))),
    # Log
    Log(Concat(Txn.sender(), Bytes(' '), Itob(Gtxn[1].amount()))),
    Approve()
])
```

When claim, we will validate the whether the amount reached the goal, and set amount to 0.

- Why transaction amount is `Balance(current) - Int(1000)`
  > Cause we need make sure we have the transaction fee.

The InnerTxnBuild is new add to the teal while the [AVM 1.0](https://developer.algorand.org/articles/discover-avm-10/).
Use `Begin` and `Submit` to construct the transaction and submit it.

```python
claim = Seq([
    # only creator can claim
    Assert(is_creator),
    Assert(App.globalGet(Bytes("Amount")) >= App.globalGet(Bytes("Goal"))),

    InnerTxnBuilder.Begin(),
    InnerTxnBuilder.SetFields({
        TxnField.type_enum: TxnType.Payment,
        TxnField.receiver: Txn.sender(),
        TxnField.amount: Balance(current) - Int(1000),
        TxnField.close_remainder_to: Txn.sender()
    }),
    InnerTxnBuilder.Submit(),

    # reset the total count
    App.globalPut(Bytes("Amount"), Int(0)),

    Approve()
])
```

##### Delete App

We only allow creator delete app.

```python
delete_app = Seq([
    Assert(is_creator),
    Approve()
])
```

##### clear

When we create application from smart contract we also need a clear contract.

```python
def clear():
    return Approve()
```

#### Compile

Use compileTeal to compile contract.

```python
with open('build/contract.teal', 'w') as f:
    compiled = compileTeal(contract(), Mode.Application, version=5)
    f.write(compiled)

with open('build/clear.teal', 'w') as f:
    compiled = compileTeal(clear(), Mode.Application, version=5)
    f.write(compiled)
```

#### Final Code

## Test - `Test.py`

#### Setup Sandbox

Follow [Algorand Sanbox](https://github.com/algorand/sandbox) to setup the sanbox.

#### Export Account

We need to export account for test.
We need two account.

```bash
./sandbox goal account list #check all account
./sandbox goal account export -a {address} # export to mnemonic
```

write to `.env` file like this

```env
ACCOUNT_A="{mnemonic A}"
ACCOUNT_B="{mnemonic B}"
```

#### Code

##### Setup the `algod`

```python
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
## Get this from sandbox

client = v2client.algod.AlgodClient(algod_token, algod_address)

```

##### Compile Contract

```python
base = os.path.dirname(os.path.abspath(__file__))

contract = base64.b64decode(client.compile(
    open(base + "/build/contract.teal").read())["result"])
# the ["result"] is in base64 code.
clear = base64.b64decode(client.compile(
    open(base + "/build/clear.teal").read())["result"])

```

##### Create App

Create with Args: `100000`

```python
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
```

##### Get App_id and Escrow

We can get escrow address from app_id. [Reference](https://developer.algorand.org/docs/get-details/dapps/smart-contracts/apps/#using-a-smart-contract-as-an-escrow)

```python
app_id = client.pending_transaction_info(tx_id)["application-index"]
print(app_id)

escrow = encoding.encode_address(
    encoding.checksum(b'appID' + app_id.to_bytes(8, 'big'))
)
```

##### Donate and claim

```python
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
    ["claim"] # args claim
)

client.send_transaction(claim.sign(private_key_a))

print("wait for 10 sec to comfirm the txn.")
sleep(10)

```
##### Delete
```python
# Delete App
delete_txn = ApplicationDeleteTxn(address_a, sp, app_id)
client.send_transaction(delete_txn.sign(private_key_a))
```

#### Final Code