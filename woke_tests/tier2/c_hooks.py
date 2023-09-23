from .b_helpers import *

from eth_utils import to_wei


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

            manager = PoolManager.deploy(500000, from_=s.paccs[0])

            fullRangeAddress = Address(
                uint160(
                    BEFORE_INITIALIZE_FLAG
                    | BEFORE_MODIFY_POSITION_FLAG
                    | BEFORE_SWAP_FLAG
                )
            )

            print(
                "or mask",
                BEFORE_INITIALIZE_FLAG | BEFORE_MODIFY_POSITION_FLAG | BEFORE_SWAP_FLAG,
            )
            print("address is", fullRangeAddress)

            impl = FullRangeImplementation.deploy(
                manager, fullRangeAddress, from_=s.paccs[0]
            )

            key = s.createPoolKey(token0, token1, impl)
            print(key)
            ID = ToID.deploy(from_=s.paccs[0])

            id = ID.toId(key)
            print(id)

            key2 = s.createPoolKey(token1, token2, impl)
            #
            id2 = ID.toId(key2)
            #
            keyWithLiq = s.createPoolKey(token0, token2, impl)
            idWithLiq = ID.toId(keyWithLiq)

            modifyPositionRouter = PoolModifyPositionTest.deploy(
                manager, from_=s.paccs[0]
            )
            token0.approve(impl, UINT_MAX, from_=s.paccs[0])
            token1.approve(impl, UINT_MAX, from_=s.paccs[0])
            token2.approve(impl, UINT_MAX, from_=s.paccs[0])

            swapRouter = PoolSwapTest.deploy(manager, from_=s.paccs[0])

            token0.approve(swapRouter, UINT_MAX, from_=s.paccs[0])
            token1.approve(swapRouter, UINT_MAX, from_=s.paccs[0])
            token2.approve(swapRouter, UINT_MAX, from_=s.paccs[0])

            manager.initialize(keyWithLiq, SQRT_RATIO_1_1, bytes(), from_=s.paccs[0])

            impl.addLiquidity(
                FullRange.AddLiquidityParams(
                    keyWithLiq.currency0,
                    keyWithLiq.currency1,
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
