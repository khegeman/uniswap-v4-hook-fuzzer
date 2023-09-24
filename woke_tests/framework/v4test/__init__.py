from pytypes.contracts.MockERC20 import MockERC20
from dataclasses import dataclass


@dataclass
class KeyParameters:
    token0: MockERC20
    token1: MockERC20
    spacing: int
