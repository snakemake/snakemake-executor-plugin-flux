from typing import Optional
import snakemake.common.tests


class TestWorkflowsBase(snakemake.common.tests.TestWorkflowsBase):
    __test__ = True

    def get_executor(self) -> str:
        return "flux"

    def get_default_remote_provider(self) -> Optional[str]:
        # Return name of default remote provider if required for testing,
        # otherwise None.
        ...

    def get_default_remote_prefix(self) -> Optional[str]:
        # Return default remote prefix if required for testing,
        # otherwise None.
        ...
