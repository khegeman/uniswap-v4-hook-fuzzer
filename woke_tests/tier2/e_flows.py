from .d_impl import *


class Flows(Impl):
    @flow()
    def flow_random_int(s):
        # ===== Randomize =====
        x = random_int(0, 10)

        # ===== Implement =====
        s.impl_random_int(x)
