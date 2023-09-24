from woke_tests.common import *

from pytypes.contracts.MockERC20 import MockERC20
from pytypes.lib.v4periphery.lib.v4core.contracts.PoolManager import PoolManager

from pytypes.lib.v4periphery.lib.v4core.contracts.libraries.Hooks import Hooks
from pytypes.lib.v4periphery.lib.v4core.contracts.types.PoolKey import PoolKey
from pytypes.lib.v4periphery.lib.v4core.contracts.types.Currency import CurrencyLibrary
from pytypes.contracts.PoolID import ToID
from pytypes.contracts.PoolModifyPositionTest import PoolModifyPositionTest
from pytypes.contracts.PoolSwapTest import PoolSwapTest

from pytypes.lib.v4periphery.lib.v4core.contracts.libraries.Pool import Pool
from eth_utils import to_wei
from woke_tests.framework import get_address
from woke_tests.framework.generators.random import fuzz_test
from pytypes.lib.v4periphery.lib.v4core.contracts.PoolManager import IPoolManager
from pytypes.lib.v4periphery.lib.v4core.contracts.interfaces.IHooks import IHooks
from abc import abstractmethod


class Init(fuzz_test.FuzzTest):
    chain: Chain
    paccs: Tuple[Account, ...]
    users: Tuple[Account, ...]
    state: State  # pyright: ignore [reportUninitializedInstanceVariable]

    @abstractmethod
    def get_hook_impl() -> IHooks:
        ...

    # put your contracts here
    # tokens: List[ERC20]

    def __init__(s):
        # ===== Initialize accounts =====
        super().__init__()
        s.chain = default_chain
        s.paccs = tuple(s.chain.accounts[i] for i in range(NUM_PACCS))
        s.users = s.chain.accounts[NUM_PACCS : NUM_PACCS + NUM_USERS]

        # ===== Add labels =====
        for idx, usr in enumerate(s.users):
            usr.label = crypto_names[idx]
