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



### Flows

A flow is a method that takes inputs and calls a function(s) on a smart contract that is under test. A simple example is shown below.  The necessary data to call addLiquidity is passed in to the function. 

```python
    @flow()
    def add_liquidity(self, random_add_liquidity: FullRange.AddLiquidityParams):
        # this is a hook specific add liquidity method

        tx = self.impl.addLiquidity(
            random_add_liquidity, from_=random_add_liquidity.to
        )
  
```

### Generating Random Data

This framework makes use of a design similar to that of Hypothesis.  If the name of one of the parameters corresponds to a callable function, that function will be used to generate the random data for that parameter.  



A simple example of data generation is shown below, this function chooses a random amount desired, then constrains the amount_min to ensure that `amount_min <= amount_desired`

```python
@dataclass 
class AmountInput:
    amount_desired : int
    amount_min : int

def random_amount_input(min : int, max:int) -> AmountInput:
    # enforce that amount_min is <= amount_desired
    amount_desired = random_int(min , max)
    return AmountInput(amount_desired=amount_desired, amount_min=random_int(min,amount_desired))

```

These functions can be composed to create more expressive examples.  Below, we use a function `initialized_pool` that returns the key of a pool that was initialized in the PoolManager and the `random_amount_input` from above to create parameters for calling the `addLiquidity` method on the `FullRange` hook.  

```python
    def random_add_liquidity(self) -> FullRange.AddLiquidityParams:
        # choose a pool that has been initialized
        key = self.initialized_pool()
        # random user
        user = self.random_user()
        amount0 = random_amount_input(min=0, max=to_wei(5, "ether"))
        amount1 = random_amount_input(min=0, max=to_wei(5, "ether"))

        return FullRange.AddLiquidityParams(
            key.currency0,
            key.currency1,
            3000,
            amount0.amount_desired,
            amount0.amount_min,
            amount1.amount_desired,
            amount1.amount_min,
            user,
            MAX_DEADLINE,
        )
```







### Invariants

An invariant in woke can execute transactions itself.  This can be useful for validating that a user can perform an action.  For example, below is an invariant that validates that all users can remove all their liquidity from the hook.  The method `snapshot_and_revert` takes a snapshot before the inner section is run and then reverts all the transactions after it exits scope.  In this way, this invariant doesn't modify the state of the block chain, but simply verifies that this condition holds.  



```python
    @invariant()
    def remove_all(self):
        # all users can remove all liquidity
        with snapshot_and_revert_fix(default_chain):
            for usr, data in self.state.user_2_liquidity.items():                
                for pool_id, liquidity in data.pool_id_2_balance.items():                    
                    key = self._pools_keys.get(pool_id,None)
                    if (liquidity > 0) and (key is not None):
                        tx = self.impl.removeLiquidity(
                            FullRange.RemoveLiquidityParams(
                                key.currency0,
                                key.currency1,
                                3000,
                                liquidity,
                                MAX_DEADLINE,
                            ),
                            from_=usr,
                        )
```





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