from .b_helpers import *


class Hooks(Helpers):
    @override
    def pre_sequence(s):
        # s.tokens = []
        s._pools_keys = {}
        s._deploy()

    @override
    def pre_flow(s, flow: Callable[..., None], **kwargs):
        with open(csv, "a") as f:
            _ = f.write(f"{s.sequence_num},{s.flow_num},{flow.__name__}\n")

    @override
    def post_sequence(s):
        ...
        # s.tokens = None  # pyright: ignore [reportGeneralTypeIssues]
        # s.factory = None  # pyright: ignore [reportGeneralTypeIssues]
        # s.pairs = None  # pyright: ignore [reportGeneralTypeIssues]
