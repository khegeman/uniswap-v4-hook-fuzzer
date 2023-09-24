from woke_tests.common import *

from pytypes.contracts.MockERC20 import MockERC20
from pytypes.lib.v4periphery.lib.v4core.contracts.PoolManager import PoolManager

from pytypes.lib.v4periphery.lib.v4core.contracts.libraries.Hooks import Hooks
from pytypes.lib.v4periphery.lib.v4core.contracts.types.PoolKey import PoolKey
from pytypes.lib.v4periphery.lib.v4core.contracts.types.Currency import CurrencyLibrary
from pytypes.contracts.PoolID import ToID
from pytypes.contracts.PoolModifyPositionTest import PoolModifyPositionTest
from pytypes.contracts.PoolSwapTest import PoolSwapTest
from pytypes.lib.v4periphery.lib.v4core.contracts.libraries.Position import Position
from pytypes.lib.v4periphery.lib.v4core.contracts.libraries.Pool import Pool
from eth_utils import to_wei
from woke_tests.framework import get_address
from woke_tests.framework.generators.random import fuzz_test
from pytypes.lib.v4periphery.lib.v4core.contracts.PoolManager import IPoolManager
from pytypes.lib.v4periphery.lib.v4core.contracts.interfaces.IHooks import IHooks
from abc import abstractmethod
from dataclasses import dataclass
from . import KeyParameters


class V4Test(fuzz_test.FuzzTest):
    chain: Chain
    paccs: Tuple[Account, ...]
    users: Tuple[Account, ...]
    state: State  # pyright: ignore [reportUninitializedInstanceVariable]

    @abstractmethod
    def get_hook_impl() -> IHooks:
        ...

    @abstractmethod
    def _hook_deploy(self):
        ...

    def __init__(self):
        # ===== Initialize accounts =====
        super().__init__()
        self.inside_invariant = False
        self.chain = default_chain
        self.paccs = tuple(self.chain.accounts[i] for i in range(NUM_PACCS))
        self.users = self.chain.accounts[NUM_PACCS : NUM_PACCS + NUM_USERS]

        # ===== Add labels =====
        for idx, usr in enumerate(self.users):
            usr.label = crypto_names[idx]

    def random_user(self) -> Account:
        return random.choice(self.users)

    @override
    def pre_invariant(self, i):
        self.inside_invariant = True

    @override
    def post_invariant(self, i):
        self.inside_invariant = False

    @override
    def pre_sequence(self):
        self._pools_keys = {}
        self._deploy()

    @override
    def pre_flow(self, flow: Callable[..., None], **kwargs):
        with open(csv, "a") as f:
            _ = f.write(f"{self.sequence_num},{self.flow_num},{flow.__name__}\n")

    def _deploy(self):
        self.tokens = [
            MockERC20.deploy(f"Test{i}", f"{i}", 18, 2**128, from_=self.paccs[0])
            for i in range(3)
        ]

        self.manager = PoolManager.deploy(500000, from_=self.paccs[0])

        self.modifyPositionRouter = PoolModifyPositionTest.deploy(
            self.manager, from_=self.paccs[0]
        )
        self.swapRouter = PoolSwapTest.deploy(self.manager, from_=self.paccs[0])
        ID = ToID.deploy(from_=self.paccs[0])
        self.PoolKeyToID = ID.toId

        for user in self.users:
            for token in self.tokens:
                token.transfer(user, to_wei(200, "ether"), from_=self.paccs[0])
                token.approve(self.swapRouter, UINT_MAX, from_=user)

        self._hook_deploy()

    def approve_users(self, contract):
        for user in self.users:
            for token in self.tokens:
                token.approve(contract, UINT_MAX, from_=user)

    def createPoolKey(
        s,
        tokenA: MockERC20,
        tokenB: MockERC20,
        hook: IHooks,
        spacing: int = TICK_SPACING,
    ) -> PoolKey:
        (t0, t1) = (
            (tokenA, tokenB)
            if get_address(tokenA) < get_address(tokenB)
            else (tokenB, tokenA)
        )
        return PoolKey(get_address(t0), get_address(t1), 3000, spacing, hook)

    def random_key(self) -> KeyParameters:
        prob = random.uniform(0, 1)
        spacing = TICK_SPACING if prob < 0.9 else TICK_SPACING + 1
        return KeyParameters(
            token0=random.choice(self.tokens),
            token1=random.choice(self.tokens),
            spacing=spacing,
        )

    def initialized_pool(self) -> PoolKey:
        # returns a random intialized pool
        return (
            random.choice(list(self._pools_keys.values()))
            if len(self._pools_keys.values()) > 0
            else PoolKey()
        )

    def swap_params(self) -> IPoolManager.SwapParams:
        zeroForOne = random.uniform(0, 1) > 0.5
        return IPoolManager.SwapParams(
            zeroForOne=zeroForOne,
            amountSpecified=random_int(0, to_wei(3, "ether")),
            sqrtPriceLimitX96=SQRT_RATIO_1_2 if zeroForOne else SQRT_RATIO_1_1,
        )

    def test_settings(self) -> PoolSwapTest.TestSettings:
        return PoolSwapTest.TestSettings(withdrawTokens=True, settleUsingTransfer=True)

    def should_initialize_revert(
        self, e: Exception, key: PoolKey, user: Account
    ) -> bool:
        # this calls into the hook to see if the hook expected the revert exception to occur
        # for the given parameters
        return False

    @flow()
    def manager_initialize(self, random_key: KeyParameters, random_user: Account):
        key = self.createPoolKey(
            random_key.token0,
            random_key.token1,
            self.get_hook_impl(),
            spacing=random_key.spacing,
        )
        should_revert = random_key.spacing != TICK_SPACING
        pool_id = self.PoolKeyToID(key)
        should_revert |= pool_id in self._pools_keys
        try:
            tx = self.manager.initialize(
                key, SQRT_RATIO_1_1, bytes(), from_=random_user
            )
            assert should_revert is False
            self._pools_keys[pool_id] = key
        except Pool.PoolAlreadyInitialized as e:
            assert should_revert, f"Pool.PoolAlreadyInitialized id={pool_id}"

        except Exception as e:
            should_revert = self.should_initialize_revert(e, key, random_user)
            assert should_revert, f"Unexpected revert for {key} with user {random_user}"

    @flow()
    def swap(
        self,
        random_user: Account,
        initialized_pool: PoolKey,
        swap_params: IPoolManager.SwapParams,
        test_settings: PoolSwapTest.TestSettings,
    ):
        try:
            self.swapRouter.swap(
                initialized_pool, swap_params, test_settings, from_=random_user
            )
        except Exception as e:
            # how do we check if it should revert?
            print("swap error is ", e)
