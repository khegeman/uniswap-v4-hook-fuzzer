"""
Example usage of the V4 Hook Test Framework.  This tests the FullRange hook from the V4-periphery.
"""

from woke_tests.common import *
from woke_tests.framework.v4test.V4Test import *
from collections import defaultdict
from pytypes.contracts.FullRangeImplementation import FullRangeImplementation
from pytypes.contracts.FullRange import FullRange
from woke_tests.framework import snapshot_and_revert_fix
from dataclasses import dataclass, field


@dataclass
class UserData:
    """holds user data for one sequence"""

    pool_id_2_balance: Dict[bytes32, int] = field(
        default_factory=lambda: defaultdict(int)
    )


@dataclass
class State:
    """holds state for one sequence"""

    user_2_liquidity: Dict[Account, UserData] = field(
        default_factory=lambda: defaultdict(UserData)
    )


@dataclass
class RemoveLiquidityInput:
    params: FullRange.RemoveLiquidityParams
    user: Account


@dataclass
class AmountInput:
    amount_desired: int
    amount_min: int


@dataclass
class UserLiquidity:
    pool_id: bytes32
    user: Account
    liquidity: int


def random_amount_input(min: int, max: int) -> AmountInput:
    # enforce that amount_min is <= amount_desired
    amount_desired = random_int(min, max)
    return AmountInput(
        amount_desired=amount_desired, amount_min=random_int(min, amount_desired)
    )


class FullRangeTest(V4Test):
    """This class represents a test suite for a Full Range liquidity provision on a decentralized exchange. It extends the base class V4Test, and holds a state object that represents the overall state of the exchange at any given point. The class contains methods to add and remove liquidity, as well as utility functions to generate random test cases. It also defines a set of invariants and checks to validate the behavior of the liquidity provision, and to ensure that the actions performed are legal according to the rules of the decentralized exchange.

    The state is managed through the State object, which contains a mapping of users to their liquidity in various pools, among other data. The class also defines several methods which interact with the smart contract implementation to perform actions such as adding and removing liquidity.

    Methods included in the class are:
        - `random_user_with_liquidity`: Randomly selects a user with liquidity in a pool and returns the user's details.
        - `random_add_liquidity`: Generates random parameters for adding liquidity to a pool.
        - `random_remove_liquidity`: Generates random parameters for removing liquidity from a pool.
        - `get_hook_impl`: Returns the deployed hook implementation.
        - `_hook_deploy`: Deploys the hook, initializes the state, sets the implementation address and approves users.
        - `should_initialize_revert`: Determines if a revert should occur during initialization based on the exception, pool key, and user account provided.
        - `add_liquidity`: Attempts to add liquidity to a pool based on the provided parameters, specific to this hook implementation.
        - `remove_liquidity`: Attempts to remove liquidity from a pool for a given user, based on the input parameters provided.
        - `remove_all`: This invariant checks if all users can remove all liquidity without any failures.

    """

    state: State

    def __init__(self):
        super().__init__()

    def random_user_with_liquidity(self) -> UserLiquidity:
        """
        Randomly selects a user with liquidity in a pool.

        This method randomly picks a user from the stored state who has liquidity
        in at least one pool. It then randomly selects one of those pools and
        returns the associated pool ID, user, and amount of liquidity.

        If no user with liquidity is found, it returns a UserLiquidity object with
        default values (i.e., a zero bytes32 pool ID, a random user, and zero liquidity).

        Returns:
            UserLiquidity: An object containing the pool ID, user, and amount of liquidity.
        """
        if len(self.state.user_2_liquidity) > 0:
            user = random.choice(list(self.state.user_2_liquidity.keys()))
            userData = self.state.user_2_liquidity[user]
            if len(userData.pool_id_2_balance) > 0:
                pool_id = random.choice(list(userData.pool_id_2_balance.keys()))
                liquidity = userData.pool_id_2_balance[pool_id]
                return UserLiquidity(pool_id=pool_id, user=user, liquidity=liquidity)

        return UserLiquidity(bytes32(), self.random_user(), 0)

    def random_add_liquidity(self) -> FullRange.AddLiquidityParams:
        """
        Generates random parameters for adding liquidity to a pool.

        This method selects an initialized pool and a random user, then generates
        random amounts of tokens to add as liquidity to the pool.

        Returns:
            FullRange.AddLiquidityParams: The generated parameters for adding liquidity.
        """
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

    def random_remove_liquidity(self) -> RemoveLiquidityInput:
        """
        Generates random parameters for removing liquidity from a pool.

        This method selects a random user with liquidity in a pool, then generates
        random parameters for removing liquidity. If no such user is found, it
        generates invalid parameters for a random user and pool, which should cause
        a failure when used to remove liquidity.

        Returns:
            RemoveLiquidityInput: The generated parameters for removing liquidity.
        """

        user_data = self.random_user_with_liquidity()
        pool_key = self._pools_keys.get(user_data.pool_id, None)
        if pool_key is not None:
            return RemoveLiquidityInput(
                user=user_data.user,
                params=FullRange.RemoveLiquidityParams(
                    pool_key.currency0,
                    pool_key.currency1,
                    3000,
                    random_int(0, user_data.liquidity),
                    MAX_DEADLINE,
                ),
            )
        else:
            # invalid data, should fail
            return RemoveLiquidityInput(
                user=self.random_user(),
                params=FullRange.RemoveLiquidityParams(
                    self.random_token(),
                    self.random_token(),
                    3000,
                    random_int(0, to_wei(5, "ether")),
                    MAX_DEADLINE,
                ),
            )

    def get_hook_impl(self) -> IHooks:
        """
        Returns the deployed hook implementation.

        Returns:
            IHooks: The deployed hook implementation instance.
        """
        return self.impl

    def _hook_deploy(self):
        """
        Deploys the hook, initializes the state, sets the implementation address and approves users.

        This method first initializes a new state, sets the FullRange address with required flags,
        deploys the FullRangeImplementation contract, and approves users for the implementation.
        """
        self.state = State()
        fullRangeAddress = Address(
            uint160(
                BEFORE_INITIALIZE_FLAG | BEFORE_MODIFY_POSITION_FLAG | BEFORE_SWAP_FLAG
            )
        )

        self.impl = FullRangeImplementation.deploy(
            self.manager, fullRangeAddress, from_=self.paccs[0]
        )

        self.approve_users(self.impl)

    def should_initialize_revert(
        self, e: Exception, key: PoolKey, user: Account
    ) -> bool:
        """
        Determines if a revert should occur during initialization based on the exception, pool key, and user account provided.

        This function maps different exception types to corresponding validation functions that check
        specific conditions related to the exception. It then calls the validation function for the
        exception type provided, if one exists, and returns the result.

        Parameters:
            self: The instance of the class
            e (Exception): The exception that occurred.
            key (PoolKey): The pool key associated with the action that caused the exception.
            user (Account): The user account associated with the action that caused the exception.

        Returns:
            bool: True if a revert should occur, False otherwise.
        """

        def check_tick_spacing_not_default():
            """Checks if tick spacing is not set to the default value."""
            return key.tickSpacing != 60

        # Map exception types to validation functions
        exception_checkers = {
            FullRange.TickSpacingNotDefault: check_tick_spacing_not_default,
            # Add other exception types and their respective check functions here
            # OtherExceptionType: check_other_condition,
        }

        # Get the validation function for the exception type
        check_func = exception_checkers.get(type(e))

        # If there's a validation function for the exception type, call it
        if check_func:
            return check_func()

        return False  # Default case if exception type isn't handled

    @flow()
    def add_liquidity(self, random_add_liquidity: FullRange.AddLiquidityParams):
        """
        Attempts to add liquidity to a pool based on the provided parameters, specific to this hook implementation.

        This flow generates a pool key from the input parameters, then checks if the pool associated with the key exists.
        If the pool doesn't exist, the addition of liquidity should revert.

        It then attempts to add liquidity to the pool. If the liquidity addition succeeds, it updates the user's
        balance to reflect the newly added liquidity. Exceptions are caught and checked to ensure they are thrown
        under the correct conditions, like if the pool isn't initialized or if there's excessive slippage.

        Parameters:
            random_add_liquidity (FullRange.AddLiquidityParams): The input data for liquidity addition, containing
                                                                 currency details and other necessary parameters.

        Raises:
            Pool.PoolNotInitialized: If the pool to which liquidity is being added is not initialized.
            FullRange.PoolNotInitialized: If the pool to which liquidity is being added is not initialized, thrown from
                                           FullRange contract.
            FullRange.TooMuchSlippage: If the slippage during liquidity addition is excessive.
        """
        key = self.createPoolKey(
            random_add_liquidity.currency0,
            random_add_liquidity.currency1,
            self.impl,
            spacing=TICK_SPACING,
        )
        pool_id = self.PoolKeyToID(key)
        should_revert = not (pool_id in self._pools_keys)
        try:
            tx = self.impl.addLiquidity(
                random_add_liquidity, from_=random_add_liquidity.to
            )
            self.state.user_2_liquidity[random_add_liquidity.to].pool_id_2_balance[
                pool_id
            ] += tx.return_value
        except Pool.PoolNotInitialized as e:
            assert should_revert
        except FullRange.PoolNotInitialized as e:
            assert should_revert
        except FullRange.TooMuchSlippage as e:
            ...

    @flow()
    def remove_liquidity(self, random_remove_liquidity: RemoveLiquidityInput):
        """
        Attempts to remove liquidity from a pool for a given user, based on the input parameters provided.

        This flow first creates a pool key from the input currencies and other parameters. It then checks if the pool exists,
        and whether the requested liquidity removal will overdraw the user's balance or if the liquidity removal amount is zero.
        It also checks whether the pool is initialized. If any of these conditions are met, the liquidity removal should revert.

        It then attempts to remove the liquidity. If the liquidity removal succeeds and is non-zero, it updates the user's
        balance. It catches various exceptions that could be thrown during the removal, and asserts that these exceptions
        are thrown under the correct conditions.

        Parameters:
            random_remove_liquidity (RemoveLiquidityInput): The input data for liquidity removal, containing user information,
                                                             pool currency details, and the liquidity amount to be removed.

        Raises:
            Pool.PoolNotInitialized: If the pool from which liquidity is being removed is not initialized.
            FullRange.PoolNotInitialized: If the pool from which liquidity is being removed is not initialized, thrown from
                                           FullRange contract.
            Position.CannotUpdateEmptyPosition: If the position cannot be updated due to zero liquidity.
            Exception: For other unspecified exceptions, it asserts that they occur due to overdrawing liquidity.
        """
        key = self.createPoolKey(
            random_remove_liquidity.params.currency0,
            random_remove_liquidity.params.currency1,
            self.impl,
            spacing=TICK_SPACING,
        )
        pool_id = self.PoolKeyToID(key)
        should_revert = not (pool_id in self._pools_keys)
        overdraw = (
            random_remove_liquidity.params.liquidity
            > self.state.user_2_liquidity[
                random_remove_liquidity.user
            ].pool_id_2_balance.get(pool_id, 0)
        )
        remove_zero = random_remove_liquidity.params.liquidity == 0
        sqrtPx = self.manager.getSlot0(pool_id)[0]
        initialized = sqrtPx != 0
        should_revert |= not initialized
        try:
            tx = self.impl.removeLiquidity(
                random_remove_liquidity.params, from_=random_remove_liquidity.user
            )
            if random_remove_liquidity.params.liquidity:
                self.state.user_2_liquidity[
                    random_remove_liquidity.user
                ].pool_id_2_balance[pool_id] -= random_remove_liquidity.params.liquidity
        except Pool.PoolNotInitialized as e:
            assert should_revert
        except FullRange.PoolNotInitialized as e:
            # ...
            assert (
                should_revert | remove_zero | overdraw
            ), f"not init {pool_id} {sqrtPx} {initialized} {remove_zero}"
        except Position.CannotUpdateEmptyPosition as e:
            assert (
                remove_zero
            ), f"remove 0 liquidity for user {random_remove_liquidity.user} from pool {pool_id}"
        except Exception as e:
            assert overdraw

    @invariant()
    def remove_all(self):
        """
        This invariant checks if all users can remove all liquidity without any failures.

        The method iterates through all user liquidity records and attempts to remove
        liquidity from each pool they are part of. Any failures in removing liquidity are
        collected and asserted to be zero at the end of the method.

        The `snapshot_and_revert_fix` context is used to revert the blockchain state back
        to its original state before the method execution, ensuring that this invariant
        check does not modify the actual blockchain state.

        :raises AssertionError: If there are any failures in removing liquidity for any user.
        """
        fails = []
        with snapshot_and_revert_fix(default_chain):
            for usr, data in self.state.user_2_liquidity.items():
                for pool_id, liquidity in data.pool_id_2_balance.items():
                    key = self._pools_keys.get(pool_id, None)
                    if (liquidity > 0) and (key is not None):
                        try:
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
                        except:
                            fails.append((usr, key, liquidity))
        assert len(fails) == 0, f"remove_all failed for users {fails}"
