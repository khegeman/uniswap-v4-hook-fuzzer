from .f_invariants import *

from pytypes.contracts.FullRangeImplementation import FullRangeImplementation
from pytypes.contracts.FullRange import FullRange

# Hook Specific Deployments, Flows and Invariants


class HooksImpl(Invariants):
    def random_add_liquidity(s) -> FullRange.AddLiquidityParams:
        # choose a pool that has been initialized
        key = s.initialized_pool()
        # random user
        user = s.random_user()

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

    def get_hook_impl(s) -> IHooks:
        # return the deploed hook
        return s.impl

    def _hook_deploy(s):
        # deploy the hook here

        fullRangeAddress = Address(
            uint160(
                BEFORE_INITIALIZE_FLAG | BEFORE_MODIFY_POSITION_FLAG | BEFORE_SWAP_FLAG
            )
        )

        s.impl = FullRangeImplementation.deploy(
            s.manager, fullRangeAddress, from_=s.paccs[0]
        )

        s.approve_users(s.impl)

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
    def add_liquidity(s, random_add_liquidity: FullRange.AddLiquidityParams):
        # this is a hook specific add liquidity method
        key = s.createPoolKey(
            random_add_liquidity.currency0,
            random_add_liquidity.currency1,
            s.impl,
            spacing=TICK_SPACING,
        )
        pool_id = s.PoolKeyToID(key)
        should_revert = not (pool_id in s._pools_keys)
        try:
            s.impl.addLiquidity(random_add_liquidity, from_=random_add_liquidity.to)
        except Pool.PoolNotInitialized as e:
            assert should_revert
        except FullRange.PoolNotInitialized as e:
            assert should_revert
        except FullRange.TooMuchSlippage as e:
            ...
