FROM ubuntu:20.04

# hd from bsdmainutils
# ar from binutils
# ssh-keygen from openssh-client
RUN apt-get update && xargs apt-get install --no-install-recommends -yqq <<EOF && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
        less
        vim
        emacs
        nano
        bsdmainutils
        zip
        binutils
        cpio
        genisoimage
        make
        socat
        whiptail
        ed
        python
        ruby
        gcc
        wget
        openssh-client
EOF

RUN mkdir -p /run/challenge/bin /challenge

COPY --chmod=755 <<'EOF' /challenge/.init
#!/bin/sh

program="$(cat /challenge/.config)"
chmod u+s "/usr/bin/${program}"
ln -s "/usr/bin/${program}" "/challenge/${program}"
ln -s "/usr/bin/${program}" "/run/challenge/bin/${program}"

rm /challenge/.config
rm /challenge/.init
EOF
