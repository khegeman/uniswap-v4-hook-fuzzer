from .full_range import *

# pyright: basic

import random

random.seed(44)


def on_revert_handler(e: TransactionRevertedError):
    if e.tx is not None:
        print(e.tx.call_trace)
        print("reverted", e.tx.console_logs)


def make_tx_callback(range_test):
    def tx_callback(tx: TransactionAbc):
        if range_test.inside_invariant:
            # don't print logs for invariant transactions
            return

        print("\n")
        print(
            f"Executed transaction in block #{tx.block_number}\nFrom: {tx.from_}\nTo: {tx.to}\nReturn value: {tx.return_value}"
        )
        events = []
        try:
            events = tx.events
        except:
            # Woke bug with IHooks in an event
            ...

        print(f"Trasaction events: {events}")
        print(events)
        print(f"Trasaction console logs: {tx.console_logs}")
        print(tx.console_logs)
        print(tx.call_trace)
        print("\n")

        with open(csv, "a") as f:
            f.write(
                f',,,{tx.block_number},{tx.from_},{tx.to},{tx.return_value},"{events}","{tx.console_logs}"\n'
            )

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
