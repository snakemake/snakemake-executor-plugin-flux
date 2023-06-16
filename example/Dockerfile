FROM fluxrm/flux-sched:focal
# This is run from the repository root
# docker build -t flux-snake .
# docker run -it flux-snake
USER root
ENV PATH=/opt/conda:/bin:$PATH

# Note this is a custom branch that currently has the functionality for plugins
RUN pip install git+https://github.com/vsoch/snakemake@add/executor-plugins && \
    ln -s /bin/python3 /usr/local/bin/python

WORKDIR /home/fluxuser/plugin
COPY . /home/fluxuser/plugin
RUN pip install . && \
    chown -R fluxuser /home/fluxuser
USER fluxuser
