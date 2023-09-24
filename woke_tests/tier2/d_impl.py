from .c_callbacks import *


class Impl(Callbacks):
    def impl_random_int(s, x: int):
        # ===== Effects =====
        # ===== Checks  =====
        assert x >= 0
        assert x <= 10
