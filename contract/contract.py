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


def clear():
    return Return(Int(1))


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


with open('build/contract.teal', 'w') as f:
    compiled = compileTeal(contract(), Mode.Application, version=4)
    f.write(compiled)

with open('build/clear.teal', 'w') as f:
    compiled = compileTeal(clear(), Mode.Application, version=4)
    f.write(compiled)

with open('build/escrow.teal', 'w') as f:
    compiled = compileTeal(escrow(), Mode.Application, version=4)
    f.write(compiled)
