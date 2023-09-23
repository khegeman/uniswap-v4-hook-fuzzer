from .b_constants import *

TD = TypeVar("TD")


class duint(Dict[TD, int]):
    """dict of unsigned integers."""

    abs_tol: int
    """"""

    @override
    def __init__(
        s,
        abs_tol: int = DUINT_ABS_TOL,
        *args: Any,
        **kwargs: Any,
    ):
        """Call ancestors' constructors and set `abs_tol`."""
        super().__init__(*args, **kwargs)
        s.abs_tol = abs_tol

    @override
    def __setitem__(self, __key: TD, __value: int) -> None:
        """"""
        assert isinstance(__value, int)
        assert __value >= -self.abs_tol
        return super().__setitem__(__key, max(0, __value))


@dataclass
class State:
    ...


class ResAndExp(NamedTuple):
    res: int
    exp: int
