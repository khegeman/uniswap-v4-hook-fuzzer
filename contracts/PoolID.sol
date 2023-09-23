// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.20;

import {PoolId, PoolIdLibrary} from "@uniswap/v4-core/contracts/types/PoolId.sol";
import {PoolKey} from "@uniswap/v4-core/contracts/types/PoolKey.sol";

contract ToID {
    using PoolIdLibrary for PoolKey;

    function toId(PoolKey memory poolKey) external pure returns (PoolId) {
        return poolKey.toId();
    }
}
