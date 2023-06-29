from dataclasses import dataclass
from typing import Optional

from snakemake.executors import CPUExecutor

from snakemake_executor_flux.version import __version__

from .executor import FluxExecutor

assert __version__

# Common plugin interfaces to get the executor classes
# These could be functions if the import needs to happen locally
local_executor = CPUExecutor
executor = FluxExecutor

# This is the minimum version of snakemake that the plugin is compatible with
snakemake_minimum_version = "7.3.4"

# You can create a Dataclass that will translate to an argument group
# These will be namespaced as args with your dataclass args. E.g.,,
# description --> flux_description and --flux-description
# All arguments MUST be optional, and validation should
# happen in the init of your plugin.


@dataclass
class ExecutorParameters:
    help: Optional[str] = None
    description: Optional[str] = None
