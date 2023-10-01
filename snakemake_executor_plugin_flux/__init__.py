from snakemake_interface_executor_plugins.settings import CommonSettings
from .executor import FluxExecutor as Executor  # noqa


# Required:
# Common settings shared by various executors.
common_settings = CommonSettings(
    # define whether your executor plugin executes locally
    # or remotely. In virtually all cases, it will be remote execution
    # (cluster, cloud, etc.). Only Snakemake's standard execution
    # plugins (snakemake-executor-plugin-dryrun, snakemake-executor-plugin-local)
    # are expected to specify False here.
    non_local_exec=True,
    # Flux can have a shared filesystem if run in an HPC context, or not if cloud
    # so we cannot set it one way or the other.
    implies_no_shared_fs=True,
)
