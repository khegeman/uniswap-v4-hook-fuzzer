# Eth Global 2023

## Overview

The goal of our project is to create a framework to make it easier for UniswapV4 hook developers to test their hooks using stateful fuzz tests.  The framework builds upon the fuzz testing capabilities of  [Woke](https://github.com/Ackee-Blockchain/woke) , a Python package for testing Solidity smart contracts.  



[Kyle Hegeman](https://github.com/khegeman)

[Omachonu Ogali](https://github.com/oogali)





## Design

There is a class called `V4Test` that provides common functionality that will be useful for most hook developers. 

- Deploy a pool manager

- Deploy test tokens

- Deploy a swap router

- Randomized Swaps

- Randomized Pool Initialization



To test a hook, the user inherits from this class and implements functionality specific to that hook.  

-  Deploy the hook inside `_hook_deploy`

- Return the deployed hook inside `get_hook_impl`

- Implement "flows", which are calls into the public interface of the hook.  Full range has two methods on it's interface that need to be implemented `addLiquidity` and `removeLiquidity` 

- Define invariants that will be validated after each flow is called
  
  

For example, here are the methods implemented in the FullRange hook test.

```python
class FullRangeTest(V4Test):
 
    def get_hook_impl(self) -> IHooks:
        # return the deployed hook
        return self.impl

    def _hook_deploy(self):
        # deploy the hook here
        ...
    @flow()
    def add_liquidity(self, random_add_liquidity: FullRange.AddLiquidityParams):
            ...

    @flow()
    def remove_liquidity(self, random_remove_liquidity: FullRange.RemoveLiquidityParams):
            ...

    @invariant():
    def removal_run(self):
        #all users can remove all deposits to the pool
        ...
```



Once this interface is implemented, the woke fuzz testing engine will run a stateful fuzz test that will call the implemented flows on the hook and the common flows (swap, initialize pool) in a randomized order, with randomized inputs.  







## Setup

Uniswap V4 Hook Testing Framework.  

Recursive clone with all submodules

```
git clone --recurse-submodules https://github.com/khegeman/uniswapv4-hook-test-framework.git
```

Install woke and dependencies into a venv

```
pip install -r requirements
```

Init pytypes for solidity contracts

```
woke init pytypes
```

Run the tests

```
woke test 
```



## References

- [Woke.](https://github.com/Ackee-Blockchain/woke)