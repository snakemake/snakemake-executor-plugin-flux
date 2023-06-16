import snakemake.plugins as plugins
from snakemake.executors import CPUExecutor

from snakemake_executor_flux.version import __version__

from .executor import FluxExecutor

assert __version__

# Common plugin interfaces to get the executor classes
# These could be functions if the import needs to happen locally
local_executor = CPUExecutor
executor = FluxExecutor


# Common plugin interfaces for custom argument addition and parsing


def add_args(parser):
    """
    Allow the custom executor to modify the parser as needed.

    Note that we do not here, but it's recommended to use your custom
    parser GROUP_IDENTIFIER as a prefix to honor the namespace.
    """
    # This is the group identifier for argparse
    # It matches the snakemake_executor_<name>
    GROUP_IDENTIFIER = plugins.get_plugin_name(__file__)
    # You could create a group argument here.
    assert GROUP_IDENTIFIER


def parse(args):
    """
    Custom parsing of arguments for the Flux executor.

    Modify args as needed here, assuming that the user has selected
    your executor (it is only possible to select one).
    """
    # Since flux is already a known executor, just set the --flux flag to true
    # Although we will use the module, this will prepare other settings
    args.flux = True
