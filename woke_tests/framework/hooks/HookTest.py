from woke_tests.common import *

from ..v4test.V4Test import *

from abc import abstractmethod
from pytypes.lib.v4periphery.lib.v4core.contracts.interfaces.IHooks import IHooks
from pytypes.lib.v4periphery.lib.v4core.contracts.types.PoolKey import PoolKey

# Hook Specific Deployments, Flows and Invariants


class HookTest(V4Test):
    @abstractmethod
    def get_hook_impl(self) -> IHooks:
        # return the deployed hook
        return None

    def _hook_deploy(self):
        # deploy the hook here

        ...

    def should_initialize_revert(
        self, e: Exception, key: PoolKey, user: Account
    ) -> bool:
        return False
