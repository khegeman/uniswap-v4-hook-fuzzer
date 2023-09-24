from pytypes.lib.v4periphery.lib.v4core.contracts.libraries.Pool import Pool
from .d_impl import *

# flows generic to v4 pools


class Flows(Impl):
    def random_key(s) -> KeyParameters:
        prob = random.uniform(0, 1)
        spacing = TICK_SPACING if prob < 0.9 else TICK_SPACING + 1
        return KeyParameters(
            token0=random.choice(s.tokens),
            token1=random.choice(s.tokens),
            spacing=spacing,
        )

    def initialized_pool(s) -> PoolKey:
        # returns a random intialized pool
        return (
            random.choice(list(s._pools_keys.values()))
            if len(s._pools_keys.values()) > 0
            else PoolKey()
        )

    def swap_params(s) -> IPoolManager.SwapParams:
        zeroForOne = random.uniform(0, 1) > 0.5
        return IPoolManager.SwapParams(
            zeroForOne=zeroForOne,
            amountSpecified=random_int(0, to_wei(3, "ether")),
            sqrtPriceLimitX96=SQRT_RATIO_1_2 if zeroForOne else SQRT_RATIO_1_1,
        )

    def test_settings(s) -> PoolSwapTest.TestSettings:
        return PoolSwapTest.TestSettings(withdrawTokens=True, settleUsingTransfer=True)

    def should_initialize_revert(s, e: Exception, key: PoolKey, user: Account) -> bool:
        return False

    @flow()
    def manager_initialize(s, random_key: KeyParameters, random_user: Account):
        key = s.createPoolKey(
            random_key.token0,
            random_key.token1,
            s.get_hook_impl(),
            spacing=random_key.spacing,
        )
        should_revert = random_key.spacing != TICK_SPACING
        pool_id = s.PoolKeyToID(key)
        should_revert |= pool_id in s._pools_keys
        try:
            tx = s.manager.initialize(key, SQRT_RATIO_1_1, bytes(), from_=random_user)
            assert should_revert is False
            s._pools_keys[pool_id] = key
        except Pool.PoolAlreadyInitialized as e:
            assert should_revert, f"Pool.PoolAlreadyInitialized id={pool_id}"

        except Exception as e:
            #   print("manager_init tick wrong? ", key.tickSpacing, random_key.spacing)
            should_revert = s.should_initialize_revert(e, key, s.paccs[0])
            assert should_revert, f"Unexpected revert for {key} with user {random_user}"

    @flow()
    def swap(
        s,
        random_user: Account,
        initialized_pool: PoolKey,
        swap_params: IPoolManager.SwapParams,
        test_settings: PoolSwapTest.TestSettings,
    ):
        try:
            s.swapRouter.swap(
                initialized_pool, swap_params, test_settings, from_=random_user
            )
        except Exception as e:
            # how do we check if it should revert?
            print("swap error is ", e)
