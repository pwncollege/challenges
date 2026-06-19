FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_CTYPE=C.UTF-8

RUN <<EOF
    rm -f /etc/apt/apt.conf.d/docker-clean
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

    (set +o pipefail; yes | unminimize)

    dpkg --add-architecture i386

    apt-get clean && rm -rf /var/lib/apt/lists/*
EOF

RUN apt-get update && xargs apt-get install --no-install-recommends -yqq <<EOF && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
        build-essential
        ca-certificates
        curl
        git
        libseccomp-dev
        libssl-dev
        python-is-python3
        python3-dev
        python3-pip
        python3-yaml
        qemu-system
        strace
        sudo
        unzip
        wget
EOF

RUN <<EOF
    git clone https://github.com/capstone-engine/capstone /opt/capstone
    cd /opt/capstone
    git checkout 0a67596
    make
    make install
    rm -rf /opt/capstone
EOF

ADD . /pwnshop
RUN pip install /pwnshop
RUN echo -n 'pwn.college{TEST}' > /flag
