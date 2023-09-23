from .b_helpers import *

from pytypes.contracts.MockERC20 import MockERC20
from pytypes.lib.v4periphery.lib.v4core.contracts.PoolManager import PoolManager
from pytypes.contracts.FullRangeImplementation import FullRangeImplementation
from pytypes.lib.v4periphery.lib.v4core.contracts.libraries.Hooks import Hooks


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

    #            vm.etch(address(fullRange), address(impl).code);
    #
    #            key = createPoolKey(token0, token1);
    #            id = key.toId();
    #
    #            key2 = createPoolKey(token1, token2);
    #            id2 = key.toId();
    #
    #            keyWithLiq = createPoolKey(token0, token2);
    #            idWithLiq = keyWithLiq.toId();
    #
    #            modifyPositionRouter = new PoolModifyPositionTest(manager);
    #            swapRouter = new PoolSwapTest(manager);
    #
    #            token0.approve(address(fullRange), type(uint256).max);
    #            token1.approve(address(fullRange), type(uint256).max);
    #            token2.approve(address(fullRange), type(uint256).max);
    #            token0.approve(address(swapRouter), type(uint256).max);
    #            token1.approve(address(swapRouter), type(uint256).max);
    #            token2.approve(address(swapRouter), type(uint256).max);
    #
    #            manager.initialize(keyWithLiq, SQRT_RATIO_1_1, ZERO_BYTES);
    #            fullRange.addLiquidity(
    #                FullRange.AddLiquidityParams(
    #                    keyWithLiq.currency0,
    #                    keyWithLiq.currency1,
    #                    3000,
    #                    100 ether,
    #                    100 ether,
    #                    99 ether,
    #                    99 ether,
    #                    address(this),
    #                    MAX_DEADLINE
    #                )
    #            );

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
