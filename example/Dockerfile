FROM fluxrm/flux-sched:jammy
# This is run from the repository root
# docker build -t flux-snake .
# docker run -it flux-snake
USER root
ENV PATH=/opt/conda/bin:/root/.local/bin:$PATH
ENV FLUX_MODULE_PATH=${FLUX_MODULE_PATH}:/usr/lib/x86_64-linux-gnu/flux/modules

# Note this is a custom branch that currently has the functionality for plugins
RUN apt-get update && apt-get install -y python3-pip python3-venv

WORKDIR /home/fluxuser/plugin
COPY . /home/fluxuser/plugin
RUN chown -R fluxuser /home/fluxuser

ENV PATH=/opt/conda/bin:/home/fluxuser/.local/bin:$PATH
USER fluxuser

# Run/install poetry as fluxuser
RUN python3 -m pip install --user pipx && \
    python3 -m pipx ensurepath && \
    pipx install poetry && \
    sudo ln -s /bin/python3 /bin/python

RUN poetry lock && \
    poetry install && \
    pip install git+https://github.com/vsoch/snakemake@update-lazy-property-import && \
    pip install -e . && \
    sudo chown -R fluxuser /home/fluxuser
