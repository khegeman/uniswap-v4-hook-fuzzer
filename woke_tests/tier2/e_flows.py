from pytypes.lib.v4periphery.lib.v4core.contracts.libraries.Pool import Pool
from .d_impl import *

# from pytypes.contracts.FullRange import TickSpacingNotDefault


class Flows(Impl):
    def manager_initialize_inputs(s) -> InitializeParameters:
        prob = random.uniform(0, 1)
        spacing = TICK_SPACING if prob < 0.9 else TICK_SPACING + 1
        return InitializeParameters(
            token0=random.choice(s.tokens),
            token1=random.choice(s.tokens),
            spacing=spacing,
        )

    @flow()
    def manager_initialize(s, manager_initialize_inputs: InitializeParameters):
        key = s.createPoolKey(
            manager_initialize_inputs.token0,
            s.token1,
            s.impl,
            spacing=manager_initialize_inputs.spacing,
        )
        should_revert = manager_initialize_inputs.spacing != TICK_SPACING
        pool_id = s.PoolKeyToID(key)
        should_revert |= s._pools_init.get(pool_id, False)
        try:
            s.manager.initialize(key, SQRT_RATIO_1_1, bytes(), from_=s.paccs[0])
            assert should_revert is False
            s._pools_init[pool_id] = True
        except FullRange.TickSpacingNotDefault as e:
            assert should_revert
        except Pool.PoolAlreadyInitialized as e:
            assert should_revert
