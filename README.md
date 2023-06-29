# Snakemake Executor Flux

This is an example implementation for an external snakemake plugin.
Since we already have one for Flux (and it can run in a container) the example
is for Flux. You can use this repository as a basis to design your own executor to work
with snakemake!

## Usage

### Tutorial

For this tutorial you will need Docker installer.

[Flux-framework](https://flux-framework.org/) is a flexible resource scheduler that can work on both high performance computing systems and cloud (e.g., Kubernetes).
Since it is more modern (e.g., has an official Python API) we define it under a cloud resource. For this example, we will show you how to set up a "single node" local
Flux container to interact with snakemake using the plugin here. You can use the [Dockerfile](examples/Dockerfile) that will provide a container with Flux and snakemake
Note that we install from source and bind to `/home/fluxuser/snakemake` with the intention of being able to develop (if desired).

First, build the container:

```bash
$ docker build -f example/Dockerfile -t flux-snake .
```

Note that this currently uses a [custom branch](https://github.com/vsoch/snakemake/tree/add/executor-plugins) to install Snakemake.
We will add the plugin to `/home/fluxuser/plugin`, install it, and shell in as the fluxuser to optimally interact with flux.
After the container builds, shell in:

```bash
$ docker run -it flux-snake bash
```

And start a flux instance:

```bash
$ flux start --test-size=4
```

Go into the examples directory (where the Snakefile is) and run snakemake, targeting your executor plugin.

```bash
$ cd ./example

# This says "use the custom executor module named snakemake_executor_flux"
$ snakemake --jobs 1 --executor flux
```
```console
Building DAG of jobs...
Using shell: /bin/bash
Job stats:
job                         count    min threads    max threads
------------------------  -------  -------------  -------------
all                             1              1              1
multilingual_hello_world        2              1              1
total                           3              1              1

Select jobs to execute...

[Fri Jun 16 19:24:22 2023]
rule multilingual_hello_world:
    output: hola/world.txt
    jobid: 2
    reason: Missing output files: hola/world.txt
    wildcards: greeting=hola
    resources: tmpdir=/tmp

Job 2 has been submitted with flux jobid ƒcjn4t3R (log: .snakemake/flux_logs/multilingual_hello_world/greeting_hola.log).
[Fri Jun 16 19:24:32 2023]
Finished job 2.
1 of 3 steps (33%) done
Select jobs to execute...

[Fri Jun 16 19:24:32 2023]
rule multilingual_hello_world:
    output: hello/world.txt
    jobid: 1
    reason: Missing output files: hello/world.txt
    wildcards: greeting=hello
    resources: tmpdir=/tmp

Job 1 has been submitted with flux jobid ƒhAPLa79 (log: .snakemake/flux_logs/multilingual_hello_world/greeting_hello.log).
[Fri Jun 16 19:24:42 2023]
Finished job 1.
2 of 3 steps (67%) done
Select jobs to execute...

[Fri Jun 16 19:24:42 2023]
localrule all:
    input: hello/world.txt, hola/world.txt
    jobid: 0
    reason: Input files updated by another job: hello/world.txt, hola/world.txt
    resources: tmpdir=/tmp

[Fri Jun 16 19:24:42 2023]
Finished job 0.
3 of 3 steps (100%) done
Complete log: .snakemake/log/2023-06-16T192422.186675.snakemake.log
```

And that's it! Continue reading to learn more about plugin design, and how you can also design your own executor
plugin for use or development (that doesn't need to be added to upstream snakemake).

## Developer

### Instructions

These are general instructions for the naming of your library.

1. The plugin module should have the prefix `snakemake_executor_<name>`
2. The name of your executor is assumed to be the last term (e.g., `<name>` or "flux" here)
3. The library name, if provided via pypi to be installed with pip, should follow the same convention, but using dashes, e.g., "snakemake-executor-flux"
4. Arguments are provided in two ways:
  a. Via a custom data class that will be namespaced to your executor by snakemake OR
  b. Using an already established Snakemake argument (e.g., `--preemtible` or `--container-image`)

The above will be discussed in more detail.

### How does it work?

We [discover plugins](https://github.com/vsoch/snakemake/blob/add/executor-plugins/snakemake/plugins.py) via a simple approach
that looks for modules that start with the prefix "snakemake_executor_<name>" as mentioned above.
While there are several [design approaches](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/)
for implementing plugins, this one was chose for its simplicity, and not requiring the current Snakemake build or install
setup to drastically change. Our setup supports:

 - Install of any custom number of executor plugins
 - Choosing to use one by specifying it's name with `--executor <name>`
 - Defining a custom data class that is added as additional arguments (and later parsed back into the class)

Each plugin is expected to have, at the top level of the module (e.g., `snakemake_executor_example.<func>`), the following functions or attributes for Snakemake to find:

 - A custom dataclasses.dataclass with namespaced executor plugin arguments, `ExecutorParameters`
 - A `snakemake_minimum_version` that defines the minimum version of snakemake your plugin is compatible with.
 - `local_executor`: should be akin to a "pointer" to whatever class you want Snakemake to use for your local executor. For most, this can be the `snakemake.executor.CPUExecutor`
 - `executor`: should reference your custom executor class, which is expected to take a core set of arguments plug the original args spec. As an example:

More detail on the above is provided below.

#### dataclasses.dataclass

Your executor plugin is driven by the custom dataclass. We chose this design because it needs to be possible
to interact with the executor from within Python (in which case you would create the dataclass) or from
the command line (in which case we convert from the dataclass to argparse and back again)! As an example,
here is a very basic way to define custom arguments for your executor plugin via a dataclass:

```python
import snakemake.plugins as plugins
from typing import Optional
from dataclasses import dataclass


@dataclass
class ExecutorParameters:
    help: Optional[str] = None
    description: Optional[str] = None
```

In the above, note that each argument will be prefixed with the executor plugin name when parsed as an argument
to snakemake. As an example:

```
# dataclass      snakemake argument    snakemake flag
description --> `flux_description` --> `--flux-description`
```

For the above to work for more than one plugin, it is very important that:

- You define the types to be Optional, otherwise Snakemake will error that the argument is required
- You also provide a default argument, otherwise the same will happen!

You can currently add arguments for str, int, float, or bool. Advanced types can be added
when needed or requested. This is done by way of support from [argparse-dataclass](https://github.com/mivade/argparse_dataclass/)
that is added to Snakemake.

#### snakemake_minimum_version

We ask that your class provide a `snakemake_minimum_version` that can be used to assess
compatibility with Snakemake. Note that (at the time of this writing) plugins are anticipated
to be added to Snakemake 7.28.4, so that would be the absolute minimum.

```python
# This is the minimum version of snakemake that the plugin is compatible with
snakemake_minimum_version = "7.3.4"
```

Note that if you want to live dangerously, you can choose "any":

```python
snakemake_minimum_version = "any"
```

This attribute will be checked for as part of the validation, and you should expect it to parse
with `packaging.version`, e.g.,:

```
import packaging.version

# This would be the version from snakemake
snakemake_version = packaging.version.parse(__version__)

# And you minimum version
minimum_version = packaging.version.parse(minimum_version)

# And how we compare them (this needs to be true)
snakemake_version >= minimum_version
```

Note that if we discover an "unknown" version with Snakemake, we allow it to pass, assuming
that you are developing.

#### ExecutorParameters

Your custom dataclass called `ExecutorParameters` must be available on the top
level of the plugin. If you don't have any arguments, a default (empty)
set will be used by Snakemake.

#### local_executor and executor

These are mostly just handles to point to the classes you want snakemake to use
for your executor and local_executor. As an example:

```python
from snakemake.executors import CPUExecutor
from .executor import FluxExecutor

# Common plugin interfaces to get the executor classes
# These could be functions if the import needs to happen locally
local_executor = CPUExecutor
executor = FluxExecutor
```
### scheduler logic

In the snakemake.scheduler, if we find that the user has provided the `--executor <name>` flag,
and it's an executor known to Snakemake, we will use your `local_executor` and `executor` classes
you've defined, and pass along expected (global) arguments along with your dataclass.

```python
# We have chosen an executor custom plugin
elif executor_args is not None and executor_args._executor_name in executor_plugins:
    executor = executor_plugins[executor_args._executor_name]
    self._local_executor = executor.local_executor(
        workflow,
        dag,
        local_cores,
        printreason=printreason,
        quiet=quiet,
        printshellcmds=printshellcmds,
        cores=local_cores,
    )
    self._executor = executor.executor(
        workflow,
        dag,
        cores,
        printreason=printreason,
        quiet=quiet,
        printshellcmds=printshellcmds,
        executor_args=executor_args,
)
```

Likely we can adjust this spec depending on what the average plugin executor needs. The current design of snakemake
has custom booleans for every executor, and this adds a lot of verbosity and complexity to the code. This design
isn't perfect, but might be a step in a direction that simplifies that a bit.
