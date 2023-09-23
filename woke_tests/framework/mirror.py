from typing import Callable, Any, Tuple, TypeVar, List, Hashable, Dict

K = TypeVar("K", bound=Hashable)


class Mirror(Dict[K, Any]):
    """
    A class to mirror data of a remote contract exposed via a public mapping or array.
    Note: This implementation does not support nested mappings.

    Attributes:
        lookup_func: The remote lookup method used to fetch data from the contract.
        K: The type of keys used in the mapping or array.

    Methods:
        bind(LookupMethod: Callable[..., Any])
            Binds the mirror to a remote lookup method with type hints.
        update()
            Updates local keys with remote values using the bound method.
        assert_equals_remote()
            Verifies that local mirror matches remote data for all tracked keys.
        filter(f: Callable[[Tuple[K, Any]], bool]) -> List[Tuple[K, Any]]
            Filters and returns a list of key-value pairs using the given filter function.
    """

    def bind(self, LookupMethod: Callable[..., Any]):
        """
        Bind the mirror to a remote lookup method.

        Args:
            LookupMethod: The remote lookup method.
        """
        self.lookup_func = LookupMethod

    def update(self):
        """
        Update local keys with remote values using the bound method.
        """
        for k in self:
            self[k] = self.lookup_func(k)

    def assert_equals_remote(self):
        """
        Verify that local mirror matches remote data for all tracked keys.

        Raises:
            AssertionError: If any local value does not match its remote counterpart.
        """
        for key in self:
            if self[key] != self.lookup_func(key):
                raise AssertionError(
                    "Local value does not match remote value for key {}".format(key)
                )

    def filter(self, f: Callable[[Tuple[K, Any]], bool]) -> List[Tuple[K, Any]]:
        """
        Filter and return a list of key-value pairs using the given filter function.

        Args:
            f (Callable[[Tuple[K, Any]], bool]): The filter function.

        Returns:
            List[Tuple[K, Any]]: Filtered key-value pairs.
        """
        return [(k, self[k]) for k in self if f((k, self[k]))]
