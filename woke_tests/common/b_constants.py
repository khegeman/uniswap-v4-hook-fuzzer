from .a_imports import *

"""
This file contains all the constants used in the project.
"""

csv = plib.Path("gitignore/flows_and_txns.csv")
# this overwrites the file
_ = csv.write_text(
    "sequence_number,flow_number,flow_name,block_number,from,to,return_value,events,console_logs\n"
)

# when we `from woke.testing import *`, we actually import a generic type T
# this should probably be fixed, but until then, just use different name here
TE = TypeVar("TE")
"""this represents a generic type of something we'll read from the env"""


def get_env(
    var_name: str,
    default_value: TE,
) -> TE:
    """get an environment variable and type cast it, or return a default value if it's not set"""
    value = os.environ.get(var_name)

    if value is None:
        return default_value

    try:
        return type(default_value)(value)
    except ValueError:
        console.print(f"Could not cast {var_name}={value} to {type(default_value)}")
        return default_value


SEQUENCES_COUNT = get_env("WOKE_TESTS_SEQUENCES_COUNT", 1)
FLOWS_COUNT = get_env("WOKE_TESTS_FLOWS_COUNT", 100)

NUM_PACCS = get_env("WOKE_TESTS_NUM_PRIV_ACC", 1)
NUM_USERS = get_env("WOKE_TESTS_NUM_USERS", 3)

NUM_TOKENS = get_env("WOKE_TESTS_NUM_TOKENS", 4)
NUM_TOKENS_EACH_USER = get_env("WOKE_TESTS_NUM_TOKENS", 100)

# region tolerances
DUINT_ABS_TOL = get_env("WOKE_TESTS_DUINT_ABS_TOL", 10_000)
# endregion

# region ignores
# endregion

# region weights
# endregion

crypto_names = [
    # it's visually easier to read if the names are the same length
    "Alice",
    "Brant",
    "Chady",
    "David",
    "Evena",
    "Frank",
    "Georg",
    "Helen",
    "Irene",
    "Johny",
    "Karen",
    "Laura",
    "Mikey",
    "Nancy",
    "Olivi",
    "Paula",
    "Queen",
    "Rachy",
    "Steve",
    "Tommy",
    "Unity",
    "Veron",
    "Wendy",
    "Xavie",
    "Yvonn",
    "Zebra",
]

UINT_MAX = 2**256 - 1

BEFORE_INITIALIZE_FLAG = 1 << 159
AFTER_INITIALIZE_FLAG = 1 << 158
BEFORE_MODIFY_POSITION_FLAG = 1 << 157
AFTER_MODIFY_POSITION_FLAG = 1 << 156
BEFORE_SWAP_FLAG = 1 << 155
AFTER_SWAP_FLAG = 1 << 154
BEFORE_DONATE_FLAG = 1 << 153
AFTER_DONATE_FLAG = 1 << 152


#    /// @dev Min tick for full range with tick spacing of 60
MIN_TICK = -887220
# @dev Max tick for full range with tick spacing of 60
MAX_TICK = -MIN_TICK
TICK_SPACING = 60
LOCKED_LIQUIDITY = 1000
MAX_DEADLINE = 12329839823
MAX_TICK_LIQUIDITY = 11505069308564788430434325881101412
DUST = 30

SQRT_RATIO_1_1 = 79228162514264337593543950336
