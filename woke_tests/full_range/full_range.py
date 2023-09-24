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


class FullRangeTest(V4Test):
    state: State

    def __init__(self):
        super().__init__()

    def random_add_liquidity(self) -> FullRange.AddLiquidityParams:
        # choose a pool that has been initialized
        key = self.initialized_pool()
        # random user
        user = self.random_user()

        return FullRange.AddLiquidityParams(
            key.currency0,
            key.currency1,
            3000,
            to_wei(10, "ether"),  # ether,
            to_wei(10, "ether"),  # ether,
            to_wei(9, "ether"),  # ether,
            to_wei(9, "ether"),  # ether,
            user,
            MAX_DEADLINE,
        )

    def random_remove_liquidity(self) -> RemoveLiquidityInput:
        # choose a pool that has been initialized
        key = self.initialized_pool()
        # random user
        user = self.random_user()

        return RemoveLiquidityInput(
            user=user,
            params=FullRange.RemoveLiquidityParams(
                key.currency0,
                key.currency1,
                3000,
                to_wei(10, "ether"),  # ether,
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
            ].pool_id_2_balance[pool_id]
        )
        remove_zero = random_remove_liquidity.params.liquidity == 0
        try:
            tx = self.impl.removeLiquidity(
                random_remove_liquidity.params, from_=random_remove_liquidity.user
            )

            self.state.user_2_liquidity[random_remove_liquidity.user].pool_id_2_balance[
                pool_id
            ] -= random_remove_liquidity.params.liquidity
        except Pool.PoolNotInitialized as e:
            assert should_revert
        except FullRange.PoolNotInitialized as e:
            assert should_revert
        except Position.CannotUpdateEmptyPosition as e:
            assert (
                remove_zero
            ), f"remove 0 liquidity for user {random_remove_liquidity.user} from pool {pool_id}"
        except Exception as e:
            assert overdraw

    @invariant()
    def remove_all(self):
        # all users can remove all liquidity
        with snapshot_and_revert_fix(default_chain):
            for usr, data in self.state.user_2_liquidity.items():
                for pool_id, liquidity in data.pool_id_2_balance.items():
                    key = self._pools_keys[pool_id]
                    if liquidity > 0:
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
