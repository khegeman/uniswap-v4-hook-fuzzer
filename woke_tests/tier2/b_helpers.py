from .a_init import *


class Helpers(Init):
    def random_user(s) -> Account:
        return random.choice(s.users)


    def _deploy(s):
        s.token0 = MockERC20.deploy("TestA", "A", 18, 2**128, from_=s.paccs[0])
        s.token1 = MockERC20.deploy("TestA", "B", 18, 2**128, from_=s.paccs[0])
        s.token2 = MockERC20.deploy("TestA", "C", 18, 2**128, from_=s.paccs[0])


        s.manager = PoolManager.deploy(500000, from_=s.paccs[0])

        fullRangeAddress = Address(
            uint160(
                BEFORE_INITIALIZE_FLAG
                | BEFORE_MODIFY_POSITION_FLAG
                | BEFORE_SWAP_FLAG
            )
        )

   
        s.impl = FullRangeImplementation.deploy(
            s.manager, fullRangeAddress, from_=s.paccs[0]
        )

        s.key = s.createPoolKey(s.token0, s.token1, s.impl)
     
        ID = ToID.deploy(from_=s.paccs[0])

        id = ID.toId(s.key)
  
        s.key2 = s.createPoolKey(s.token1, s.token2, s.impl)
        #
        id2 = ID.toId(s.key2)
        #
        s.keyWithLiq = s.createPoolKey(s.token0, s.token2, s.impl)
        idWithLiq = ID.toId(s.keyWithLiq)

        s.modifyPositionRouter = PoolModifyPositionTest.deploy(
            s.manager, from_=s.paccs[0]
        )
        s.token0.approve(s.impl, UINT_MAX, from_=s.paccs[0])
        s.token1.approve(s.impl, UINT_MAX, from_=s.paccs[0])
        s.token2.approve(s.impl, UINT_MAX, from_=s.paccs[0])

        s.swapRouter = PoolSwapTest.deploy(s.manager, from_=s.paccs[0])

        s.token0.approve(s.swapRouter, UINT_MAX, from_=s.paccs[0])
        s.token1.approve(s.swapRouter, UINT_MAX, from_=s.paccs[0])


        s.manager.initialize(s.keyWithLiq, SQRT_RATIO_1_1, bytes(), from_=s.paccs[0])

        s.impl.addLiquidity(
            FullRange.AddLiquidityParams(
                s.keyWithLiq.currency0,
                s.keyWithLiq.currency1,
                3000,
                to_wei(100, "ether"),  # ether,
                to_wei(100, "ether"),  # ether,
                to_wei(99, "ether"),  # ether,
                to_wei(99, "ether"),  # ether,
                s.paccs[0],
                MAX_DEADLINE,
            ),
            from_=s.paccs[0],
        )

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
