from .a_init import *
from dataclasses import dataclass

from abc import abstractmethod


@dataclass
class KeyParameters:
    token0: MockERC20
    token1: MockERC20
    spacing: int


class Helpers(Init):
    def random_user(s) -> Account:
        return random.choice(s.users)

    @abstractmethod
    def _hook_deploy(s):
        ...

    def _deploy(s):
        s.tokens = [
            MockERC20.deploy(f"Test{i}", f"{i}", 18, 2**128, from_=s.paccs[0])
            for i in range(3)
        ]

        s.manager = PoolManager.deploy(500000, from_=s.paccs[0])

        s.modifyPositionRouter = PoolModifyPositionTest.deploy(
            s.manager, from_=s.paccs[0]
        )
        s.swapRouter = PoolSwapTest.deploy(s.manager, from_=s.paccs[0])
        ID = ToID.deploy(from_=s.paccs[0])
        s.PoolKeyToID = ID.toId

        for user in s.users:
            for token in s.tokens:
                token.transfer(user, to_wei(200, "ether"), from_=s.paccs[0])
                token.approve(s.swapRouter, UINT_MAX, from_=user)

        s._hook_deploy()

    def approve_users(s, contract):
        for user in s.users:
            for token in s.tokens:
                token.approve(contract, UINT_MAX, from_=user)

    def createPoolKey(
        s,
        tokenA: MockERC20,
        tokenB: MockERC20,
        hook: IHooks,
        spacing: int = TICK_SPACING,
    ) -> PoolKey:
        (t0, t1) = (
            (tokenA, tokenB)
            if get_address(tokenA) < get_address(tokenB)
            else (tokenB, tokenA)
        )
        return PoolKey(get_address(t0), get_address(t1), 3000, spacing, hook)
