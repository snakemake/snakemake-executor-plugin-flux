from dataclasses import dataclass
from typing import Optional

from argparse_dataclass import _add_dataclass_options
from snakemake.executors import CPUExecutor
from snakemake.logging import logger

from snakemake_executor_flux.version import __version__

from .executor import FluxExecutor

# This will only be available with snakemake v7.28.4
try:
    import snakemake.plugins as plugins
except ImportError:
    logger.error("A minimum version of snakemake v7.28.4 is required to use plugins.")

assert __version__

# Common plugin interfaces to get the executor classes
# These could be functions if the import needs to happen locally
local_executor = CPUExecutor
executor = FluxExecutor

# This is the minimum version of snakemake that the plugin is compatible with
snakemake_minimum_version = "7.3.4"

# You can create a Dataclass that will translate to an argument group
# It is recommended to namespace the arguments with your group
# identifier, e.g.,
# GROUP_IDENTIFIER = plugins.get_plugin_name(__file__)


@dataclass
class ExecutorParameters:
    flux_help: Optional[str] = None
    flux_description: Optional[str] = None


# Common plugin interfaces for custom argument addition and parsing


def add_args(parser):
    """
    Allow the custom executor to modify the parser as needed.

    Note that we do not here, but it's recommended to use your custom
    parser GROUP_IDENTIFIER as a prefix to honor the namespace.
    """
    _add_dataclass_options(ExecutorParameters, parser)


def parse(args):
    """
    Custom parsing of arguments for the Flux executor.

    For arguments that are scoped to your custom data class, this
    function should map these ExecutorParameters from the parsed args
    back into the dataclass above. This will be passed to the
    executor. For shared args (not part of your dataclass) you can also
    modify args as needed here, assuming that  the user has selected
    your executor (it is only possible to select one).
    """
    # Since flux is already a known executor, just set the --flux flag to true
    # Although we will use the module, this will prepare other settings
    args.flux = True

    # Parse namespaced args (starting with flux_) into dataclass.
    # See plugins.py in snakemake to customize here
    return plugins.args_to_dataclass(args, ExecutorParameters)
