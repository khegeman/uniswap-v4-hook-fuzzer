from woke_tests.common import *

from pytypes.contracts.MockERC20 import MockERC20
from pytypes.lib.v4periphery.lib.v4core.contracts.PoolManager import PoolManager
from pytypes.contracts.FullRangeImplementation import FullRangeImplementation
from pytypes.lib.v4periphery.lib.v4core.contracts.libraries.Hooks import Hooks
from pytypes.lib.v4periphery.lib.v4core.contracts.types.PoolKey import PoolKey
from pytypes.lib.v4periphery.lib.v4core.contracts.types.Currency import CurrencyLibrary
from pytypes.contracts.PoolID import ToID
from pytypes.contracts.PoolModifyPositionTest import PoolModifyPositionTest
from pytypes.contracts.PoolSwapTest import PoolSwapTest
from pytypes.contracts.FullRange import FullRange

from eth_utils import to_wei


class Init(FuzzTest):
    chain: Chain
    paccs: Tuple[Account, ...]
    users: Tuple[Account, ...]
    state: State  # pyright: ignore [reportUninitializedInstanceVariable]

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
