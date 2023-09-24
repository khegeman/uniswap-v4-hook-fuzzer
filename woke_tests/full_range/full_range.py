from woke_tests.common import *
from woke_tests.framework.v4test.V4Test import *
from collections import defaultdict
from pytypes.contracts.FullRangeImplementation import FullRangeImplementation
from pytypes.contracts.FullRange import FullRange
from woke_tests.framework import snapshot_and_revert_fix
from dataclasses import dataclass, field

# Hook Specific Deployments, Flows and Invariants


@dataclass
class UserData:
    """holds user data for one sequence"""

    pool_id_2_balance: Dict[bytes32, int] = field(
        default_factory=lambda: defaultdict(int)
    )


@dataclass
class State:
    """holds state for one sequence"""

    user_2_liquidity: Dict[Account, UserData] = field(
        default_factory=lambda: defaultdict(UserData)
    )


@dataclass
class RemoveLiquidityInput:
    params: FullRange.RemoveLiquidityParams
    user: Account


@dataclass
class AmountInput:
    amount_desired: int
    amount_min: int


@dataclass
class UserLiquidity:
    pool_id: bytes32
    user: Account
    liquidity: int


def random_amount_input(min: int, max: int) -> AmountInput:
    # enforce that amount_min is <= amount_desired
    amount_desired = random_int(min, max)
    return AmountInput(
        amount_desired=amount_desired, amount_min=random_int(min, amount_desired)
    )


class FullRangeTest(V4Test):
    state: State

    def __init__(self):
        super().__init__()

    def random_user_with_liquidity(self) -> UserLiquidity:
        if len(self.state.user_2_liquidity) > 0:
            user = random.choice(list(self.state.user_2_liquidity.keys()))
            userData = self.state.user_2_liquidity[user]
            if len(userData.pool_id_2_balance) > 0:
                pool_id = random.choice(list(userData.pool_id_2_balance.keys()))
                liquidity = userData.pool_id_2_balance[pool_id]
                return UserLiquidity(pool_id=pool_id, user=user, liquidity=liquidity)

        return UserLiquidity(bytes32(), self.random_user(), 0)

    def random_add_liquidity(self) -> FullRange.AddLiquidityParams:
        # choose a pool that has been initialized
        key = self.initialized_pool()
        # random user
        user = self.random_user()
        amount0 = random_amount_input(min=0, max=to_wei(5, "ether"))
        amount1 = random_amount_input(min=0, max=to_wei(5, "ether"))

        return FullRange.AddLiquidityParams(
            key.currency0,
            key.currency1,
            3000,
            amount0.amount_desired,
            amount0.amount_min,
            amount1.amount_desired,
            amount1.amount_min,
            user,
            MAX_DEADLINE,
        )

    def random_remove_liquidity(self) -> RemoveLiquidityInput:
        # choose a pool that has been initialized
        # key = self.initialized_pool()
        # random user
        # user = self.random_user()

        user_data = self.random_user_with_liquidity()
        pool_key = self._pools_keys.get(user_data.pool_id, None)
        if pool_key is not None:
            return RemoveLiquidityInput(
                user=user_data.user,
                params=FullRange.RemoveLiquidityParams(
                    pool_key.currency0,
                    pool_key.currency1,
                    3000,
                    random_int(0, user_data.liquidity),
                    MAX_DEADLINE,
                ),
            )
        else:
            # invalid data, should fail
            return RemoveLiquidityInput(
                user=self.random_user(),
                params=FullRange.RemoveLiquidityParams(
                    self.random_token(),
                    self.random_token(),
                    3000,
                    random_int(0, to_wei(5, "ether")),
                    MAX_DEADLINE,
                ),
            )

    def get_hook_impl(self) -> IHooks:
        # return the deployed hook
        return self.impl

    def _hook_deploy(self):
        # deploy the hook here
        self.state = State()
        fullRangeAddress = Address(
            uint160(
                BEFORE_INITIALIZE_FLAG | BEFORE_MODIFY_POSITION_FLAG | BEFORE_SWAP_FLAG
            )
        )

        self.impl = FullRangeImplementation.deploy(
            self.manager, fullRangeAddress, from_=self.paccs[0]
        )

        self.approve_users(self.impl)

        # self.state.user_2_liquidity : Dict[Account, UserData] = field(default_factory=dict)

    def should_initialize_revert(s, e: Exception, key: PoolKey, user: Account) -> bool:
        def check_tick_spacing_not_default():
            return key.tickSpacing != 60

        # Map exception types to validation functions
        exception_checkers = {
            FullRange.TickSpacingNotDefault: check_tick_spacing_not_default,
            # Add other exception types and their respective check functions here
            # OtherExceptionType: check_other_condition,
        }

        # Get the validation function for the exception type
        check_func = exception_checkers.get(type(e))

        # If there's a validation function for the exception type, call it
        if check_func:
            return check_func()

        return False  # Default case if exception type isn't handled

    @flow()
    def add_liquidity(self, random_add_liquidity: FullRange.AddLiquidityParams):
        # this is a hook specific add liquidity method
        key = self.createPoolKey(
            random_add_liquidity.currency0,
            random_add_liquidity.currency1,
            self.impl,
            spacing=TICK_SPACING,
        )
        pool_id = self.PoolKeyToID(key)
        should_revert = not (pool_id in self._pools_keys)
        try:
            tx = self.impl.addLiquidity(
                random_add_liquidity, from_=random_add_liquidity.to
            )
            self.state.user_2_liquidity[random_add_liquidity.to].pool_id_2_balance[
                pool_id
            ] += tx.return_value
        except Pool.PoolNotInitialized as e:
            assert should_revert
        except FullRange.PoolNotInitialized as e:
            assert should_revert
        except FullRange.TooMuchSlippage as e:
            ...

    @flow()
    def remove_liquidity(self, random_remove_liquidity: RemoveLiquidityInput):
        key = self.createPoolKey(
            random_remove_liquidity.params.currency0,
            random_remove_liquidity.params.currency1,
            self.impl,
            spacing=TICK_SPACING,
        )
        pool_id = self.PoolKeyToID(key)
        should_revert = not (pool_id in self._pools_keys)
        overdraw = (
            random_remove_liquidity.params.liquidity
            > self.state.user_2_liquidity[
                random_remove_liquidity.user
            ].pool_id_2_balance.get(pool_id, 0)
        )
        remove_zero = random_remove_liquidity.params.liquidity == 0
        sqrtPx = self.manager.getSlot0(pool_id)[0]
        initialized = sqrtPx != 0
        should_revert |= not initialized
        try:
            tx = self.impl.removeLiquidity(
                random_remove_liquidity.params, from_=random_remove_liquidity.user
            )
            if random_remove_liquidity.params.liquidity:
                self.state.user_2_liquidity[
                    random_remove_liquidity.user
                ].pool_id_2_balance[pool_id] -= random_remove_liquidity.params.liquidity
        except Pool.PoolNotInitialized as e:
            assert should_revert
        except FullRange.PoolNotInitialized as e:
            # ...
            assert (
                should_revert | remove_zero | overdraw
            ), f"not init {pool_id} {sqrtPx} {initialized} {remove_zero}"
        except Position.CannotUpdateEmptyPosition as e:
            assert (
                remove_zero
            ), f"remove 0 liquidity for user {random_remove_liquidity.user} from pool {pool_id}"
        except Exception as e:
            assert overdraw

    @invariant()
    def remove_all(self):
        # all users can remove all liquidity
        fails = []
        with snapshot_and_revert_fix(default_chain):
            for usr, data in self.state.user_2_liquidity.items():
                for pool_id, liquidity in data.pool_id_2_balance.items():
                    key = self._pools_keys.get(pool_id, None)
                    if (liquidity > 0) and (key is not None):
                        try:
                            tx = self.impl.removeLiquidity(
                                FullRange.RemoveLiquidityParams(
                                    key.currency0,
                                    key.currency1,
                                    3000,
                                    liquidity,
                                    MAX_DEADLINE,
                                ),
                                from_=usr,
                            )
                        except:
                            fails.append((usr, key, liquidity))
        assert len(fails) == 0, f"remove_all failed for users {fails}"
