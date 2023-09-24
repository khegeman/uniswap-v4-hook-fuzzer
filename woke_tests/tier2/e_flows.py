from pytypes.lib.v4periphery.lib.v4core.contracts.libraries.Pool import Pool
from .d_impl import *

# from pytypes.contracts.FullRange import TickSpacingNotDefault


class Flows(Impl):
    def random_key(s) -> KeyParameters:
        prob = random.uniform(0, 1)
        spacing = TICK_SPACING if prob < 0.9 else TICK_SPACING + 1
        return KeyParameters(
            token0=random.choice(s.tokens),
            token1=random.choice(s.tokens),
            spacing=spacing,
        )

    def deployed_key(s) -> PoolKey:
        return random.choice(list(s._pools_keys.values()))

    def swap_settings(s) -> IPoolManager.SwapParams:
        return IPoolManager.SwapParams(
            zeroForOne=True,
            amountSpecified=to_wei(1, "ether"),
            sqrtPriceLimitX96=SQRT_RATIO_1_2,
        )

    def test_settings(s) -> PoolSwapTest.TestSettings:
        return PoolSwapTest.TestSettings(withdrawTokens=True, settleUsingTransfer=True)

    def random_add_liquidity(s) -> FullRange.AddLiquidityParams:
        key = s.deployed_key()
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

    #    this is more involved for now.  I think we need to deploy a manager for each pool
    #    @flow()
    #    def manager_initialize(s, random_key: KeyParameters):
    #        key = s.createPoolKey(
    #            random_key.token0,
    #            random_key.token1,
    #            s.impl,
    #            spacing=random_key.spacing,
    #        )
    #        should_revert = random_key.spacing != TICK_SPACING
    #        pool_id = s.PoolKeyToID(key)
    #        should_revert |= pool_id in s._pools_keys
    #        print("initialize", pool_id)
    #        try:
    #            tx = s.manager.initialize(key, SQRT_RATIO_1_1, bytes(), from_=s.paccs[0])
    #            assert should_revert is False
    #            s._pools_keys[pool_id] = key
    #            print("initialize liquidity", pool_id, tx.raw_events)
    #        except FullRange.TickSpacingNotDefault as e:
    #            print("manager_init tick wrong? ", key.tickSpacing, random_key.spacing)
    #            assert should_revert
    #        except Pool.PoolAlreadyInitialized as e:
    #            print("manager_init already initialized", pool_id)
    #            assert should_revert

    @flow()
    def add_liquidity(s, random_add_liquidity: FullRange.AddLiquidityParams):
        key = s.createPoolKey(
            random_add_liquidity.currency0,
            random_add_liquidity.currency1,
            s.impl,
            spacing=TICK_SPACING,
        )
        pool_id = s.PoolKeyToID(key)
        should_revert = not (pool_id in s._pools_keys)
        print("pool id", pool_id, "revert? ", should_revert)
        try:
            s.impl.addLiquidity(random_add_liquidity, from_=random_add_liquidity.to)
        except Pool.PoolNotInitialized as e:
            assert should_revert
        except FullRange.PoolNotInitialized as e:
            assert should_revert

    @flow()
    def swap(
        s,
        random_user: Account,
        deployed_key: PoolKey,
        swap_params: IPoolManager.SwapParams,
        test_settings: PoolSwapTest.TestSettings,
    ):
        s.swapRouter.swap(deployed_key, swap_params, test_settings, from_=random_user)
