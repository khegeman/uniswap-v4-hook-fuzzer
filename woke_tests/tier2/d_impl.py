from .c_hooks import *


class Impl(Hooks):
    def impl_random_int(s, x: int):
        # ===== Effects =====
        # ===== Checks  =====
        assert x >= 0
        assert x <= 10
