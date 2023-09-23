from .g_issues import *

# pyright: basic


def on_revert_handler(e: TransactionRevertedError):
    if e.tx is not None:
        print(e.tx.call_trace)
        print(e.tx.console_logs)


def tx_callback(tx: TransactionAbc):
    try:
        print("\n")
        print(
            f"Executed transaction in block #{tx.block_number}\nFrom: {tx.from_}\nTo: {tx.to}\nReturn value: {tx.return_value}"
        )
        print(f"Trasaction events: {tx.events}")
        print(tx.events)
        print(f"Trasaction console logs: {tx.console_logs}")
        print(tx.console_logs)
        print("\n")

        with open(csv, "a") as f:
            f.write(
                f",,,{tx.block_number},{tx.from_},{tx.to},{tx.return_value},{tx.events},{tx.console_logs}\n"
            )
    except:
        pass


@default_chain.connect()
# for local anvil chain
# @default_chain.connect(fork="http://127.0.0.1:8545")
@on_revert(on_revert_handler)
def test():
    default_chain.tx_callback = tx_callback
    # print('SEQUENCES_COUNT', SEQUENCES_COUNT)
    # print('FLOWS_COUNT', FLOWS_COUNT)
    Issues().run(
        SEQUENCES_COUNT,
        FLOWS_COUNT,
    )
