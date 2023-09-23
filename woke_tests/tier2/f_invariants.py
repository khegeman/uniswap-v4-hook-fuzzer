from .e_flows import *


class Invariants(Flows):
    @invariant()
    def inv_one_equals_one(s):
        assert 1 == 1
