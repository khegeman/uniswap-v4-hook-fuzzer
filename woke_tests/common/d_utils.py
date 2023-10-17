from .c_types import *

# pyright: basic


def adjusted_scientific_notation(val, num_decimals=2, exponent_pad=2):
    # https://stackoverflow.com/a/62561794/4204961
    exponent_template = "{:0>%d}" % exponent_pad
    mantissa_template = "{:.%df}" % num_decimals

    order_of_magnitude = math.floor(math.log10(abs(val)))
    nearest_lower_third = 3 * (order_of_magnitude // 3)
    adjusted_mantissa = val * 10 ** (-nearest_lower_third)
    adjusted_mantissa_string = mantissa_template.format(adjusted_mantissa)
    adjusted_exponent_string = "+-"[nearest_lower_third < 0] + exponent_template.format(
        abs(nearest_lower_third)
    )
    return adjusted_mantissa_string + "E" + adjusted_exponent_string


def format_int(x: int) -> str:
    if abs(x) < 10**5:
        return f"{x:_}"
    # no_of_digits = int(math.log10(abs(x))) + 1
    # if x % 10 ** (no_of_digits - 3) == 0:
    #     return f'{x:.2e}'
    # return f'{x:.2E} ({x:_})'
    return f"{adjusted_scientific_notation(x)} ({x:_})"


def num_to_letter(num: int) -> str:
    """converts a number to a lower-case letter
    e.g. 0 -> a, 1 -> b, 2 -> c, etc.
    """
    # there are 26 letters in the English alphabet
    assert num >= 0 and num <= 25
    return chr(ord("a") + num)


def deploy_at_address(contract : Contract, address : Address,chain : Chain = default_chain, **kwargs) -> Account:
    """
    Deploys a contract and copies its state and code to a deterministic address.

    This function deploys runs deploy twice on the contract once to get the access list of storage slots used by the constructor
    and a second time to get the actual contract instance. It then copies the deployed contract to a deterministic 
    address, copying over the contract's code.  Additionally, it copies the state of any slots in the access list from the deployed contract 
    to the deterministic one.

    Parameters:
    -----------
    contract : Contract
        The contract to be deployed.

    address : Address
        The deterministic address where the contract's state and code will be copied.

    chain : Chain, optional
        The blockchain interface to operate on. Defaults to `default_chain`.

    **kwargs : 
        Additional keyword arguments to be passed to the contract's deploy method.

    Returns:
    --------
    Account
        Returns an account instance representing the contract 
        at the deterministic address with the state and code of the deployed contract.

    """    
    access_list = contract.deploy(request_type="access_list",
        **kwargs
    )
    impl = contract.deploy(
        **kwargs
    )

    deterministic = contract(address, chain=chain)
    deterministic.code = impl.code
    slots = access_list[0].get(str(impl.address), [])
    for slot in slots:
        chain.chain_interface.set_storage_at(str(address),slot,chain.chain_interface.get_storage_at(str(impl.address),slot) )
    return deterministic



T = TypeVar('T', bound='Contract')  

def patch_deploy_at_address(cls: Type[T]) -> None:
    """
    Patches a given Contract class to include a `deploy_at_address` method.

    This function adds a new class method `deploy_at_address` to the provided Contract class `cls`.
    This new method functions similarly to the usual `deploy` method but allows for specification of
    a deterministic address where the contract will be deployed.

    Parameters:
    -----------
    cls : Type[T]
        The Contract class to be patched with the `deploy_at_address` method.

    Example:
    --------
    >>> patch_deploy_at_address(MyContract)
    >>> contractInstance = MyContract.deploy_at_address(address=my_address, chain=my_chain, arg1=val1)

    """
    
    @classmethod
    def deploy_at_address_class(cls: Type[T], address: Address, chain: Chain = default_chain, **kwargs) -> T:
        """
        Deploys the contract at a specific address.

        This method deploys the contract to a given deterministic address, rather than a randomly generated one.
        All other deployment behaviors and arguments are identical to the regular `deploy` method.

        Parameters:
        -----------
        address : Address
            The deterministic address at which the contract should be deployed.

        chain : Chain, optional
            The blockchain interface to operate on. Defaults to `default_chain`.

        **kwargs : 
            Additional keyword arguments to be passed to the contract's deployment process.

        Returns:
        --------
        T
            An instance of the contract deployed at the specified address.
        """
        return cls(deploy_at_address(cls, address, chain, **kwargs))
    
    cls.deploy_at_address = deploy_at_address_class
