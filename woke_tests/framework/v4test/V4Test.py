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
    def get_hook_impl(self) -> IHooks:
        """Gets the hook implementation.

        This method should be overridden by subclasses to provide
        the specific hook implementation.

        Returns:
            IHooks: An instance of a class that implements the IHooks interface.
        """

    @abstractmethod
    def _hook_deploy(self):
        """Deploys the hook.

        This method should be overridden by subclasses to provide
        the specific deployment logic for the hook.
        """

    @abstractmethod
    def should_initialize_revert(
        self, e: Exception, key: PoolKey, user: Account
    ) -> bool:
        """Determines if a pool manager initialize should revert

        This method should be overridden by subclasses to provide
        logic for deciding if a pool manager initialized should revert
        based on the given parameters and exception.

        Args:
            e (Exception): The exception that was raised.
            key (PoolKey): The pool key associated with the operation.
            user (Account): The user account associated with the operation.

        Returns:
            bool: True if a revert is expected for the given data, False otherwise.
        """
        return False

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

    # -----------------------------------
    # SECTION 1: Data generation methods
    # -----------------------------------

    def random_user(self) -> Account:
        """Generates a random user from the available user list.

        Returns:
            Account: A randomly selected user account.
        """
        return random.choice(self.users)

    def random_token(self) -> MockERC20:
        """Generates a random token from the available token list.

        Returns:
            MockERC20: A randomly selected token.
        """
        return random.choice(self.tokens)

    def random_key(self) -> KeyParameters:
        """Generates random key parameters for pool operations.

        A KeyParameters object is generated with random tokens and spacing.
        There's a 90% chance the spacing will be set to TICK_SPACING, and a
        10% chance it will be set to TICK_SPACING + 1.

        Returns:
            KeyParameters: Randomly generated key parameters.
        """
        prob = random.uniform(0, 1)
        spacing = TICK_SPACING if prob < 0.9 else TICK_SPACING + 1
        return KeyParameters(
            token0=random.choice(self.tokens),
            token1=random.choice(self.tokens),
            spacing=spacing,
        )

    def initialized_pool(self) -> PoolKey:
        """Retrieves a random initialized pool or creates a new PoolKey object if none exist.

        Returns:
            PoolKey: A randomly selected initialized pool or a new PoolKey object.
        """
        return (
            random.choice(list(self._pools_keys.values()))
            if len(self._pools_keys.values()) > 0
            else PoolKey(currency0=self.random_token(),currency1=self.random_token(),fee=3000,tickSpacing=TICK_SPACING,hooks=self.get_hook_impl())
        )                    

    def swap_params(self) -> IPoolManager.SwapParams:
        """Generates random swap parameters for pool operations.

        Returns:
            IPoolManager.SwapParams: Randomly generated swap parameters.
        """
        zeroForOne = random.uniform(0, 1) > 0.5
        return IPoolManager.SwapParams(
            zeroForOne=zeroForOne,
            amountSpecified=random_int(0, to_wei(3, "ether")),
            sqrtPriceLimitX96=SQRT_RATIO_1_2 if zeroForOne else SQRT_RATIO_1_1,
        )

    def test_settings(self) -> PoolSwapTest.TestSettings:
        """Generates a test settings object with specified parameters.

        Returns:
            PoolSwapTest.TestSettings: A TestSettings object with withdrawTokens set to True and
                                       settleUsingTransfer set to True.
        """
        return PoolSwapTest.TestSettings(withdrawTokens=True, settleUsingTransfer=True)


    # -----------------------------------
    # SECTION 2: Flows
    # -----------------------------------

    @flow()
    def pool_manager_initialize(self, random_key: KeyParameters, random_user: Account):
        """Initializes a pool with a specified pool key, called by a user account.

        This method first creates a pool key using the given `random_key` and `random_user`.
        It then checks if a revert operation should be initialized based on the key spacing and
        whether the pool ID is already present in the `_pools_keys` dictionary.

        If no exceptions are raised during the initialization of the manager, the `pool_id` and `key`
        are added to the `_pools_keys` dictionary. If a `Pool.PoolAlreadyInitialized` exception is
        raised and a revert was expected, it's handled accordingly. Any other unexpected exceptions
        trigger a check to `should_initialize_revert` to decide if a revert operation should be
        initialized, and raises an AssertionError if a revert was not expected.

        Args:
            random_key (KeyParameters): The parameters used to create a pool key.
            random_user (Account): The user account to call initialize with

        Raises:
            AssertionError: If an unexpected revert occurs or if `should_revert` is False when
                             `Pool.PoolAlreadyInitialized` exception is raised.
        """
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
        """Executes a token swap on the swapRouter with the specified parameters.

        This method attempts to perform a token swap operation using the swapRouter.
        If the swap operation fails, it catches any exception and prints an error message to the console.

        Args:
            random_user (Account): The account executing the swap operation.
            initialized_pool (PoolKey): The pool where the swap operation occurs.
            swap_params (IPoolManager.SwapParams): The parameters for the swap operation.
            test_settings (PoolSwapTest.TestSettings): Additional settings for the swap test.

        Raises:
            Exception: Any exceptions thrown by the swapRouter.swap method are caught - TODO validate error
        """
        try:
            self.swapRouter.swap(
                initialized_pool, swap_params, test_settings, from_=random_user
            )
        except Exception as e:
            # how do we check if it should revert?
            ...


    # -----------------------------------
    # SECTION 3: Callbacks
    # -----------------------------------

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
        with open(create_flow_log(), "a") as f:
            _ = f.write(f"{self.sequence_num},{self.flow_num},{flow.__name__}\n")

    # -----------------------------------
    # SECTION 4: Helpers
    # -----------------------------------

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
