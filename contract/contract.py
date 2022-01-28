from pyteal import Log, Concat, Itob, Bytes, Balance, Approve, MinBalance, App, Cond, Seq, Txn, Int, Assert, TxnType, TxnField, Return, Global, Gtxn, OnComplete, TxnType, compileTeal, Mode, Btoi, InnerTxnBuilder


def contract():
    on_create = Seq(
        [
            # valid the args length
            Assert(Txn.application_args.length() == Int(1)),
            # store the goal
            App.globalPut(Bytes("Goal"), Btoi(Txn.application_args[0])),
            # set amount to zero
            App.globalPut(Bytes("Amount"), Int(0)),
            # return success
            Approve()
        ]
    )

    current = Global.current_application_address()
    is_creator = Txn.sender() == Global.creator_address()

    donate = Seq(
        [
            # Must be a size 2 transaction group
            Assert(Global.group_size() == Int(2)),
            # The donate reciever must be the escrow
            Assert(Gtxn[1].receiver() == current),
            # Add new donate to total
            App.globalPut(Bytes("Amount"), Gtxn[1].amount(
            )+App.globalGet(Bytes("Amount"))),
            Log(Concat(Txn.sender(), Bytes(' '), Itob(Gtxn[1].amount()))),
            Approve()
        ]
    )

    claim = Seq(
        [
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
        ]
    )

    delete_app = Seq(
        [
            Assert(is_creator),
            Approve()
        ]
    )

    call = Cond(
        [Txn.application_args[0] == Bytes("donate"), donate],
        [Txn.application_args[0] == Bytes("claim"), claim],
    )

    return Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, delete_app],
        [Txn.on_completion() == OnComplete.NoOp, call]
    )


def clear():
    return Approve()


with open('build/contract.teal', 'w') as f:
    compiled = compileTeal(contract(), Mode.Application, version=5)
    f.write(compiled)

with open('build/clear.teal', 'w') as f:
    compiled = compileTeal(clear(), Mode.Application, version=5)
    f.write(compiled)
