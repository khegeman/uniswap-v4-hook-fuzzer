from .b_helpers import *


class Hooks(Helpers):
    @override
    def pre_sequence(s):
        # s.tokens = []

        s._deploy()
        for i in range(NUM_TOKENS):
            decimals = random_int(
                # TOKEN_MIN_DECIMALS,
                18,
                # TOKEN_MAX_DECIMALS,
                18,
            )
            total_supply = NUM_USERS * NUM_TOKENS_EACH_USER * 10**decimals
            # token: ERC20 = ERC20.deploy(_totalSupply=total_supply, from_=s.paccs[0])
            # token.label = num_to_letter(i).upper()
            # print(f'Created token {token.label} with {decimals} decimals and {total_supply} total supply')
            # s.tokens.append(token)
            #
            # for j in range(NUM_USERS):
            #     _ = token.transfer(s.users[j], NUM_TOKENS_EACH_USER * 10**decimals, from_=s.paccs[0])

            token0 = MockERC20.deploy("TestA", "A", 18, 2**128, from_=s.paccs[0])
            token1 = MockERC20.deploy("TestA", "B", 18, 2**128, from_=s.paccs[0])
            token2 = MockERC20.deploy("TestA", "C", 18, 2**128, from_=s.paccs[0])

            fullRange = FullRangeImplementation(
                Address(
                    uint160(
                        BEFORE_INITIALIZE_FLAG
                        | BEFORE_MODIFY_POSITION_FLAG
                        | BEFORE_SWAP_FLAG
                    )
                )
            )

            manager = PoolManager.deploy(500000, from_=s.paccs[0])

            impl = FullRangeImplementation.deploy(manager, fullRange, from_=s.paccs[0])

            key = s.createPoolKey(token0, token1, fullRange)
            print(key)
            ID = ToID.deploy(from_=s.paccs[0])

            id = ID.toId(key)
            print(id)

            key2 = s.createPoolKey(token1, token2, fullRange)
            #
            id2 = ID.toId(key2)
            #
            keyWithLiq = s.createPoolKey(token0, token2, fullRange)
            idWithLiq = ID.toId(keyWithLiq)

            modifyPositionRouter = PoolModifyPositionTest.deploy(
                manager, from_=s.paccs[0]
            )
            token0.approve(fullRange, UINT_MAX, from_=s.paccs[0])
            token1.approve(fullRange, UINT_MAX, from_=s.paccs[0])
            token2.approve(fullRange, UINT_MAX, from_=s.paccs[0])

            swapRouter = PoolSwapTest.deploy(manager, from_=s.paccs[0])

            token0.approve(swapRouter, UINT_MAX, from_=s.paccs[0])
            token1.approve(swapRouter, UINT_MAX, from_=s.paccs[0])
            token2.approve(swapRouter, UINT_MAX, from_=s.paccs[0])

        # manager.initialize(keyWithLiq, SQRT_RATIO_1_1, bytes(), from_=s.paccs[0])
        #

    #        #            manager.initialize(keyWithLiq, SQRT_RATIO_1_1, ZERO_BYTES);
    #        fullRange.addLiquidity(
    #            FullRange.AddLiquidityParams(
    #                keyWithLiq.currency0,
    #                keyWithLiq.currency1,
    #                3000,
    #                100,  # ether,
    #                100,  # ether,
    #                99,  # ether,
    #                99,  # ether,
    #                s.paccs[0],
    #                MAX_DEADLINE
    #            ), from_=s.paccs[0]
    #        )

    @override
    def pre_flow(s, flow: Callable[..., None]):
        with open(csv, "a") as f:
            _ = f.write(f"{s.sequence_num},{s.flow_num},{flow.__name__}\n")

    @override
    def post_sequence(s):
        ...
        # s.tokens = None  # pyright: ignore [reportGeneralTypeIssues]
        # s.factory = None  # pyright: ignore [reportGeneralTypeIssues]
        # s.pairs = None  # pyright: ignore [reportGeneralTypeIssues]
