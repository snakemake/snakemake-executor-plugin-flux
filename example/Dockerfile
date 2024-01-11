FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
        libfftw3-dev libfftw3-bin pdsh libfabric-dev libfabric1 \
        dnsutils telnet strace cmake git g++ openmpi-bin \
        openmpi-common wget curl unzip libopenmpi-dev \
        software-properties-common gpg-agent build-essential

RUN add-apt-repository ppa:deadsnakes/ppa && apt-get update && \
    apt install -y python3.12 python3.12-dev

RUN update-alternatives --install /usr/bin/python3 python /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python python3 /usr/bin/python3.12 1

RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py

RUN pip3 install -U git+https://github.com/snakemake/snakemake-interface-common@main && \
    pip3 install -U git+https://github.com/snakemake/snakemake-interface-executor-plugins && \
    pip3 install -U git+https://github.com/snakemake/snakemake-interface-storage-plugins@main && \
    pip3 install -U git+https://github.com/snakemake/snakemake-storage-plugin-s3@main && \
    pip3 install -U git+https://github.com/snakemake/snakemake-storage-plugin-gcs@main && \
    pip3 install -U git+https://github.com/snakemake/snakemake@main

# This first section from src/test/docker/bionic/Dockerfile in flux-core
# https://github.com/flux-framework/flux-core/blob/master/src/test/docker/bionic/Dockerfile
RUN apt-get update && \
    apt-get -qq install -y --no-install-recommends \
        apt-utils && \
    rm -rf /var/lib/apt/lists/*

# Utilities
RUN apt-get update && \
    apt-get -qq install -y --no-install-recommends \
        locales \
        ca-certificates \
        curl \
        wget \
        man \
        git \
        flex \
        ssh \
        sudo \
        vim \
        luarocks \
        munge \
        lcov \
        ccache \
        lua5.2 \
        mpich \
        valgrind \
        jq && \
    rm -rf /var/lib/apt/lists/*

# Compilers, autotools
RUN apt-get update && \
    apt-get -qq install -y --no-install-recommends \
        build-essential \
        pkg-config \
        autotools-dev \
        libtool \
	libffi-dev \
        autoconf \
        automake \
        make \
        cmake \
        clang \
        clang-tidy \
        gcc \
        g++ && \
    rm -rf /var/lib/apt/lists/*

# Other deps
RUN apt-get update && \
    apt-get -qq install -y --no-install-recommends \
        libsodium-dev \
        libzmq3-dev \
        libczmq-dev \
        libjansson-dev \
        libmunge-dev \
        libncursesw5-dev \
        liblua5.2-dev \
        liblz4-dev \
        libsqlite3-dev \
        uuid-dev \
        libhwloc-dev \
        libmpich-dev \
        libs3-dev \
        libevent-dev \
        libarchive-dev \
        libpam-dev && \
    rm -rf /var/lib/apt/lists/*

# Testing utils and libs
RUN apt-get update && \
    apt-get -qq install -y --no-install-recommends \
        faketime \
        libfaketime \
        pylint \
        cppcheck \
        enchant-2 \
        aspell \
        aspell-en && \
    rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8

# NOTE: luaposix installed by rocks due to Ubuntu bug: #1752082 https://bugs.launchpad.net/ubuntu/+source/lua-posix/+bug/1752082
RUN luarocks install luaposix


# Install openpmix, prrte
WORKDIR /opt/prrte
RUN git clone https://github.com/openpmix/openpmix.git && \
    git clone https://github.com/openpmix/prrte.git && \
    ls -l && \
    set -x && \
    cd openpmix && \
    git checkout fefaed568f33bf86f28afb6e45237f1ec5e4de93 && \
    ./autogen.pl && \
    PYTHON=/usr/bin/python3 ./configure --prefix=/usr --disable-static && make -j 4 install && \
    ldconfig && \
    cd .. && \
    cd prrte && \
    git checkout 477894f4720d822b15cab56eee7665107832921c && \
    ./autogen.pl && \
    PYTHON=/usr/bin/python3 ./configure --prefix=/usr && make -j 4 install && \
    cd ../.. && \
    rm -rf prrte

ENV LANG=C.UTF-8

# This is from the docker check script (run interactively during a test)
# https://github.com/flux-framework/flux-core/blob/master/src/test/docker/checks/Dockerfile
ARG USER=fluxuser
ARG UID=1000
ARG GID=1000

# Install flux-security by hand for now:
#
WORKDIR /opt
RUN git clone --depth 1 https://github.com/flux-framework/flux-security && \
    cd flux-security && \
    ./autogen.sh && \
    PYTHON=/usr/bin/python3 ./configure --prefix=/usr --sysconfdir=/etc && \
    make && \
    make install && \
    cd .. && \
    rm -rf flux-security

# Add configured user to image with sudo access:
#
RUN set -x && groupadd -g $UID $USER && \
    useradd -g $USER -u $UID -d /home/$USER -m $USER && \
    printf "$USER ALL= NOPASSWD: ALL\\n" >> /etc/sudoers

# Setup MUNGE directories & key
RUN mkdir -p /var/run/munge && \
    dd if=/dev/urandom bs=1 count=1024 > /etc/munge/munge.key && \
    chown -R munge /etc/munge/munge.key /var/run/munge && \
    chmod 600 /etc/munge/munge.key

# Build flux core
RUN python3 -m pip install cffi ply
RUN git clone https://github.com/flux-framework/flux-core && \
    cd flux-core && \
    ./autogen.sh && \
    PYTHON=/usr/bin/python3 PYTHON_PREFIX=PYTHON_EXEC_PREFIX=/usr/lib/python3.12/site-packages ./configure \
        --prefix=/usr \
        --sysconfdir=/etc \
        --with-systemdsystemunitdir=/etc/systemd/system \
        --localstatedir=/var \
        --with-flux-security && \
    make clean && \
    make && \
    sudo make install

# This is from the same src/test/docker/bionic/Dockerfile but in flux-sched
# Flux-sched deps
RUN sudo apt-get update
RUN sudo apt-get -qq install -y --no-install-recommends \
	libboost-graph-dev \
	libboost-system-dev \
	libboost-filesystem-dev \
	libboost-regex-dev \
	libyaml-cpp-dev \
	libedit-dev

ENV LD_LIBRARY_PATH=/opt/conda/lib:$LD_LIBRARY_PATH

# Build Flux Sched	
# https://github.com/flux-framework/flux-sched/blob/master/src/test/docker/docker-run-checks.sh#L152-L158
RUN git clone https://github.com/flux-framework/flux-sched && \
    cd flux-sched && \
    git fetch && \
    ./autogen.sh && \
    PYTHON=/usr/bin/python3 ./configure --prefix=/usr --sysconfdir=/etc \
       --with-systemdsystemunitdir=/etc/systemd/system \
       --localstatedir=/var && \
    make && \
    sudo make install && \
    ldconfig

WORKDIR /home/fluxuser/plugin
COPY . /home/fluxuser/plugin

RUN pip install .
