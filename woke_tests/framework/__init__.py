from woke.development.core import Address, Account, Chain


def get_address(a: Account | Address | str) -> Address:
    """if a has an address property, that value is returned
        if not, a is returned.
    Args:
        a (Account | Address | str):

    Returns:
        _type_: _description_
    """
    addr = getattr(a, "address", None)
    if addr is not None:
        return addr
    if isinstance(a, Address):
        return a
    return Address(a)


MAX_UINT = 2**256 - 1


from .collector import JsonCollector


from contextlib import contextmanager


@contextmanager
def look_forward(chain: Chain, blocks: int = 1):
    with chain.snapshot_and_revert():
        chain.mine_many(blocks)
        yield
        block_of_call = chain.blocks["latest"]
    chain.set_next_block_timestamp(block_of_call.timestamp)


@contextmanager
def snapshot_and_revert_fix(chain: Chain):
    # anvil bug, need to put the timestamp back where it was, snapshot_revert doesn't correctly restore ts
    # when this ticket is closed, we can remove this block and just use snapshot_and_revert decorator
    # https://github.com/foundry-rs/foundry/issues/5518
    ts = chain.blocks[-1].timestamp
    with chain.snapshot_and_revert():
        yield
    chain.set_next_block_timestamp(ts + 1)
