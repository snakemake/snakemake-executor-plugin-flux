from dataclasses import dataclass, field

from snakemake_interface_executor_plugins import CommonSettings, ExecutorSettingsBase

from .executor import FluxExecutor as Executor  # noqa


# Optional:
# define additional settings for your executor
# They will occur in the Snakemake CLI as --<executor-name>-<param-name>
# Omit this class if you don't need any.
@dataclass
class ExecutorSettings(ExecutorSettingsBase):
    myparam: int = field(default=None, metadata={"help": "Some help text"})


# Optional:
# specify common settings shared by various executors.
# Omit this statement if you don't need any and want
# to rely on the defaults (highly recommended unless
# you are very sure what you do).
common_settings = CommonSettings(
    # flux executor submits jobs to flux
    non_local_exec=True
)
