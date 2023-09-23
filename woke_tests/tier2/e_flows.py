from .d_impl import *

# from pytypes.contracts.FullRange import TickSpacingNotDefault


class Flows(Impl):
    @flow()
    def manager_initialize(s):
        wrongKey = s.createPoolKey(s.token0, s.token1, s.impl, spacing=TICK_SPACING + 1)
        try:
            s.manager.initialize(wrongKey, SQRT_RATIO_1_1, bytes(), from_=s.paccs[0])
        except FullRange.TickSpacingNotDefault as e:
            pass
