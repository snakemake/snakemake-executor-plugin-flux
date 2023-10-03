import os
import shlex

from typing import List, Generator
from snakemake_interface_executor_plugins.executors.base import SubmittedJobInfo
from snakemake_interface_executor_plugins.executors.remote import RemoteExecutor
from snakemake_interface_executor_plugins.workflow import WorkflowExecutorInterface
from snakemake_interface_executor_plugins.logging import LoggerExecutorInterface
from snakemake_interface_executor_plugins.jobs import (
    JobExecutorInterface,
)
from snakemake_interface_common.exceptions import WorkflowError  # noqa

# Just import flux python bindings once
try:
    import flux
    import flux.job
    from flux.job import JobspecV1
except ImportError:
    flux = None


class FluxExecutor(RemoteExecutor):
    def __init__(
        self,
        workflow: WorkflowExecutorInterface,
        logger: LoggerExecutorInterface,
    ):
        super().__init__(
            workflow,
            logger,
            # configure behavior of RemoteExecutor below
            # whether arguments for setting the remote provider shall  be passed to jobs
            pass_default_remote_provider_args=True,
            # whether arguments for setting default resources shall be passed to jobs
            pass_default_resources_args=True,
            # whether environment variables shall be passed to jobs
            pass_envvar_declarations_to_cmd=True,
            # specify initial amount of seconds to sleep before checking for job status
            init_seconds_before_status_checks=0,
        )

        # Attach variables for easy access
        self.workdir = os.path.realpath(os.path.dirname(self.workflow.persistence.path))
        self.envvars = list(self.workflow.envvars) or []

        # access executor specific settings
        # self.workflow.executor_settings

        # Quit early if we can't access the flux api
        if not flux:
            raise WorkflowError("Cannot import flux. Are Python bindings available?")
        self._fexecutor = flux.job.FluxExecutor()

    def get_envvar_declarations(self):
        """
        Temporary workaround until:
        https://github.com/snakemake/snakemake-interface-executor-plugins/pull/31
        is able to be merged.
        """
        if self.pass_envvar_declarations_to_cmd:
            return " ".join(
                f"{var}={repr(os.environ[var])}"
                for var in self.workflow.remote_execution_settings.envvars or {}
            )
        else:
            return ""

    def run_job(self, job: JobExecutorInterface):
        # Implement here how to run a job.
        # You can access the job's resources, etc.
        # via the job object.
        # After submitting the job, you have to call
        # self.report_job_submission(job_info).
        # with job_info being of type
        # snakemake_interface_executor_plugins.executors.base.SubmittedJobInfo.
        # If required, make sure to pass the job's id to the job_info object, as keyword
        # argument 'external_job_id'.

        flux_logfile = job.logfile_suggestion(os.path.join(".snakemake", "flux_logs"))
        os.makedirs(os.path.dirname(flux_logfile), exist_ok=True)

        # The entire snakemake command to run, etc
        command = self.format_job_exec(job)
        self.logger.debug(command)

        # Generate the flux job
        # flux does not support mem_mb, disk_mb
        fluxjob = JobspecV1.from_command(command=shlex.split(command))

        # A duration of zero (the default) means unlimited
        fluxjob.duration = job.resources.get("runtime", 0)
        fluxjob.stderr = flux_logfile

        # Ensure the cwd is the snakemake working directory
        fluxjob.cwd = self.workdir
        fluxjob.environment = dict(os.environ)

        # Resources, must have at least one CPU, and integer value
        cpus_per_task = max(1, int(job.resources.get("cpus_per_task") or job.threads))
        fluxjob.cpus_per_task = cpus_per_task
        flux_future = self._fexecutor.submit(fluxjob)

        # Save aux metadata
        aux = {"flux_future": flux_future, "flux_logfile": flux_logfile}

        # Record job info
        jobid = str(flux_future.jobid())
        self.report_job_submission(SubmittedJobInfo(job, external_jobid=jobid, aux=aux))

    def get_snakefile(self):
        assert os.path.exists(self.workflow.main_snakefile)
        return self.workflow.main_snakefile

    def _get_jobname(self, job):
        # Use a dummy job name (human readable and also namespaced)
        return "snakejob-%s-%s-%s" % (self.run_namespace, job.name, job.jobid)

    async def check_active_jobs(
        self, active_jobs: List[SubmittedJobInfo]
    ) -> Generator[SubmittedJobInfo, None, None]:
        # Check the status of active jobs.

        # You have to iterate over the given list active_jobs.
        # If you provided it above, each will have its external_jobid set according
        # to the information you provided at submission time.
        # For jobs that have finished successfully, you have to call
        # self.report_job_success(active_job).
        # For jobs that have errored, you have to call
        # self.report_job_error(active_job).
        # This will also take care of providing a proper error message.
        # Usually there is no need to perform additional logging here.
        # Jobs that are still running have to be yielded.
        #
        # For queries to the remote middleware, please use
        # self.status_rate_limiter like this:
        #
        # async with self.status_rate_limiter:
        #    # query remote middleware here
        #
        # To modify the time until the next call of this method,
        # you can set self.next_sleep_seconds here.

        # Loop through active jobs and act on status
        for j in active_jobs:
            jobid = j.external_jobid
            self.logger.debug(f"Checking status for job {jobid}")
            flux_future = j.aux["flux_future"]

            # Aux logs are consistently here
            aux_logs = [j.aux["flux_logfile"]]

            # Case 1: the job is done
            if flux_future.done():
                # The exit code can help us determine if the job was successful
                try:
                    exit_code = flux_future.result(0)
                except RuntimeError:
                    # job did not complete
                    msg = f"Flux job '{j.external_jobid}' failed. "
                    self.report_job_error(j, msg=msg, aux_logs=aux_logs)

                else:
                    # the job finished (but possibly with nonzero exit code)
                    if exit_code != 0:
                        msg = f"Flux job '{jobid}' finished with non-zero exit code. "
                        self.report_job_error(j, msg=msg, aux_logs=aux_logs)
                        continue

                    # Finished and success!
                    self.report_job_success(j)

            # Otherwise, we are still running
            else:
                yield j

    def cancel_jobs(self, active_jobs: List[SubmittedJobInfo]):
        """
        cancel all active jobs. This method is called when snakemake is interrupted.
        """
        for job in active_jobs:
            if not job.flux_future.done():
                flux.job.cancel(self.f, job.jobid)
        self.shutdown()
