from .a_init import *


class Helpers(Init):
    def random_user(s) -> Account:
        return random.choice(s.users)

    # def random_token(s) -> ERC20:
    #     return random.choice(s.tokens)

    def _deploy(s):
        ...

    def createPoolKey(
        s, tokenA: MockERC20, tokenB: MockERC20, fullRange: FullRangeImplementation
    ) -> PoolKey:
        (t0, t1) = (
            (tokenA, tokenB) if tokenA.address < tokenB.address else (tokenB, tokenA)
        )
        return PoolKey(t0.address, t1.address, 3000, TICK_SPACING, fullRange)
        ...

    #    if (address(tokenA) > address(tokenB)) (tokenA, tokenB) = (tokenB, tokenA);
    #    return PoolKey(Currency.wrap(address(tokenA)), Currency.wrap(address(tokenB)), 3000, TICK_SPACING, fullRange);
