from .full_range import *

# pyright: basic

import random

random.seed(44)


def on_revert_handler(e: TransactionRevertedError):
    if e.tx is not None:
        print(e.tx.call_trace)
        print(e.tx.console_logs)


def make_tx_callback(range_test):
    def tx_callback(tx: TransactionAbc):
        if range_test.inside_invariant:
            # don't print logs for invariant transactions
            return
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
        except Exception as e:
            print("Exception in tx_callback", e)

    return tx_callback


@default_chain.connect()
@on_revert(on_revert_handler)
def test():
    range_test = FullRangeTest()
    default_chain.tx_callback = make_tx_callback(range_test)
    range_test.run(
        SEQUENCES_COUNT,
        FLOWS_COUNT,
    )
