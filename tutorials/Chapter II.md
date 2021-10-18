# Chapter II

This chapter will dev a smart contract that can be used for crowdfunding with `Algos`. (Not asset yet.)

# Pre

create file called `contract.py`

On the first line, We import pyteal;

And then define a function.
This function will return the contract.

```python
from pyteal import *;

def contract():
    return
```

# Main Application Contract Design

We have lots of method in our smart contract.
So we use `Cond` to judge the different situation.

## Two contract

According to the Algorand contract design.
The stateful contract **cannot** be use as account, but stateless can. So we have to build two smart contract:

- stateful contract (store crowdfunding info)
- stateless contract (store Algos, we call it **escrow**)

And when Interact with contract on some condition, we will use `transaction group` and contract will validate. (By this way we can bind stateful and stateless contracts together.)

## Create application

At the first, we need a 'owner' create a application from contract.

According to [Interact with smart contracts](https://developer.algorand.org/zh-hans/docs/get-details/dapps/smart-contracts/frontend/apps/?from_query=application#create) on algorand when user create application, the `app_id` attribute in the application call will be `0`;

And on the creation we have to store some information on state:

- creator
- goal
- amount

So the target will be pass as parameter.

args format:

- `{Goal}`

And the code on smart contract.

```python3
    on_create = Seq(
        [
            # store the creator
            App.globalPut(Bytes("Creator"), Txn.sender()),
            # valid the args length
            Assert(Txn.application_args.length() == Int(1)),
            # store the goal
            App.globalPut(Bytes("Goal"), Txn.application_args[0]),
            # set amount to zero
            App.globalPut(Bytes("Amount"), Int(0)),
            # return success
            Return(Int(1))
        ]
    )
```

And on the return now:

```python
    return Cond([Txn.application_id() == Int(0),on_create])
```

## Bind the Contracts

How we bind two contract?

We use cross-validation.

When we need iteract with stateless contract

1. we need make a transaction group, first is application call, second is stateless contract transaction
2. application valid the second transaction, the stateless contract valid the first application call.

After create application, it will return app_id.
The stateless contract cannot store state, So we have to embed the app_id in the stateless contract. We use a placeholder `123456` as a optional `app_id` on stateless contract. When we need change it, just replace it to the right.

And after we compile stateless contract we will get the address of stateless contract(**Escrow**), so we have to update the escrow on the application state.

We need a `update` method on the application.

the update method will have args like this:

- `update`
- `{Escrow address}`

So on the code will be this

```python
    update_escrow = Seq([
        # Valid call from the Creator
        Assert(Txn.sender() == App.globalGet(Bytes("Creator"))),
        # valid length
        Assert(Txn.application_args.length() == Int(2)),
        # store escrow
        App.globalPut(Bytes("Escrow"), Txn.application_args[1]),

        Return(Int(1))
    ])
```

And the return will be this

```python
    return Cond(
        [Txn.application_id() == Int(0),on_create],
        [Txn.application_args[0] == Bytes("update")]
        )
```

## User Donate

So we need a method `donate`.

And other people use this method they need group transaction:

- application call `donate`
- payment to escrow

And the application will valid the payment.

and the args

- `donate`

Here's code:

```python
    donate = Seq(
        [
            # Must be a size 2 transaction group
            Global.group_size() == Int(2),
            Gtxn[1].receiver() == App.globalGet(Bytes("Escrow")),
            # Add new donate to total
            App.globalPut(Bytes("Total"), Gtxn[1].amount(
            )+App.globalGet(Bytes("Total"))),

            Return(Int(1))
        ]
    )
```

And here's the return now:

```python
    return Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.application_args[0] == Bytes("update"), update_escrow],
        [Txn.application_args[0] == Bytes("donate"), donate]
    )
```

## Owner claim

After the donate hit the goal, user can claim their crowdfunding. We need a new method called: `claim`

And this method will have two transaction in a group

- Application call.
- Payment from escrow to owner.

Here's args:

- `claim`

Code:

```python
    claim = Seq(
        [
            # Must be a size 2 transaction groups
            Global.group_size() == Int(2),
            # only creator can claim
            Txn.sender() == App.globalGet(Bytes("Creator")),
            # sender must be the escrow
            Gtxn[1].sender() == App.globalGet(Bytes("Escrow")),
            # reset the total count
            App.globalPut(Bytes("Total"), Int(0)),

            Return(Int(1))
        ]
    )
```

The return:

```python
    return Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.application_args[0] == Bytes("update"), update_escrow],
        [Txn.application_args[0] == Bytes("donate"), donate],
        [Txn.application_args[0] == Bytes("claim"), claim],
    )
```

## Delete Application

According to the algorand [smart contract details](https://developer.algorand.org/docs/get-details/dapps/smart-contracts/apps/)

> Accounts may only create 10 smart contracts.

It means the algorand limit user's **max** applications can be created.

Until this tutorial been writen, This number is **10**;

So after clain the donations, we have to delete the application

Here's code:

```python
    delete_app = Seq(
        [
            # valid creator
            Assert(Txn.sender() == App.globalGet(Bytes("Creator"))),
            # valid all donate has been take out.
            Assert(App.globalGet(Bytes("Total")) == Int(0)),

            Return(Int(1))
        ]
    )
```

Return now:

```python
    return Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.application_args[0] == Bytes("update"), update_escrow],
        [Txn.application_args[0] == Bytes("donate"), donate],
        [Txn.application_args[0] == Bytes("claim"), claim],
        [Txn.on_completion() == OnComplete.DeleteApplication, delete_app]
    )
```

# Main Application Contract final view

the final code:

```python
from pyteal import Bytes, App, Cond, Seq, Txn, Int, Assert, Return, Global, Gtxn, OnComplete, TxnType, And, compileTeal, Mode


def contract():
    on_create = Seq(
        [
            # store the creator
            App.globalPut(Bytes("Creator"), Txn.sender()),
            # valid the args length
            Assert(Txn.application_args.length() == Int(1)),
            # store the goal
            App.globalPut(Bytes("Goal"), Txn.application_args[0]),
            # set amount to zero
            App.globalPut(Bytes("Amount"), Int(0)),
            # return success
            Return(Int(1))
        ]
    )

    update_escrow = Seq(
        [
            # Valid call from the Creator
            Assert(Txn.sender() == App.globalGet(Bytes("Creator"))),
            # valid length
            Assert(Txn.application_args.length() == Int(2)),
            # store escrow
            App.globalPut(Bytes("Escrow"), Txn.application_args[1]),

            Return(Int(1))
        ]
    )

    donate = Seq(
        [
            # Must be a size 2 transaction group
            Assert(Global.group_size() == Int(2)),
            # The donate reciever must be the escrow
            Assert(Gtxn[1].receiver() == App.globalGet(Bytes("Escrow"))),
            # Add new donate to total
            App.globalPut(Bytes("Total"), Gtxn[1].amount(
            )+App.globalGet(Bytes("Total"))),

            Return(Int(1))
        ]
    )

    claim = Seq(
        [
            # Must be a size 2 transaction groups
            Assert(Global.group_size() == Int(2)),
            # only creator can claim
            Assert(Txn.sender() == App.globalGet(Bytes("Creator"))),
            # sender must be the escrow
            Assert(Gtxn[1].sender() == App.globalGet(Bytes("Escrow"))),
            # reset the total count
            App.globalPut(Bytes("Total"), Int(0)),

            Return(Int(1))
        ]
    )

    delete_app = Seq(
        [
            # valid creator
            Assert(Txn.sender() == App.globalGet(Bytes("Creator"))),
            # valid all donate has been take out.
            Assert(App.globalGet(Bytes("Total")) == Int(0)),

            Return(Int(1))
        ]
    )

    return Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.application_args[0] == Bytes("update"), update_escrow],
        [Txn.application_args[0] == Bytes("donate"), donate],
        [Txn.application_args[0] == Bytes("claim"), claim],
        [Txn.on_completion() == OnComplete.DeleteApplication, delete_app]
    )

```

# Clear contract

When we create a application smart contract, we must have a clear program.

The clear program this project needed is so simple.

```python
def clear():
    return Return(Int(1))
```

# Escrow (Stateless smart contract)

As we say on the **bind the contracts** we need embed the app_id on escrow, and we use a place holder 123456.

And user's interact with the escrow must interact with application at one group, so the escrow will valid the `transaction[0]` is the application call. And the app_id must same as the app_id embed in the escrow.

Here's Code:

```python
def escrow():
    # The appid will be edit in the TEAL with backend.
    is_two_tx = Global.group_size() == Int(2)
    is_appcall = Gtxn[0].type_enum() == TxnType.ApplicationCall
    # here's the appid placeholder
    is_appid = Gtxn[0].application_id() == Int(123456)
    acceptable_app_call = Gtxn[0].on_completion() == OnComplete.NoOp
    no_rekey = And(
        Gtxn[0].rekey_to() == Global.zero_address(),
        Gtxn[1].rekey_to() == Global.zero_address()
    )
    return And(
        is_two_tx,
        is_appcall,
        is_appid,
        acceptable_app_call,
        no_rekey,
    )
```

# Compile Them

We have to compile three contract:

- main application contract
- escrow contract
- clear contract

```python
with open('build/contract.teal', 'w') as f:
    compiled = compileTeal(contract(), Mode.Application, version=4)
    f.write(compiled)

with open('build/clear.teal', 'w') as f:
    compiled = compileTeal(clear(), Mode.Application, version=4)
    f.write(compiled)

with open('build/escrow.teal', 'w') as f:
    compiled = compileTeal(escrow(), Mode.Application, version=4)
    f.write(compiled)
```

And you will get three file under the `contract/build` folder, these are the smart contract.
