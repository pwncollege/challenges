#!/bin/sh
set -eu

cd /challenge

mkdir -p /challenge/keys
CHILDREN="willow hazel holly rowan laurel juniper aspen ash maple alder cedar birch elm cypress pine spruce"
for identity in santa hacker $CHILDREN; do
  mkdir -p "/challenge/keys/${identity}"
  ssh-keygen -t ed25519 -N "" -f "/challenge/keys/${identity}/key" >/dev/null
done
chown -R 1000:1000 /challenge/keys/hacker

touch /var/log/north_poole.log
chmod 600 /var/log/north_poole.log

touch /var/log/santa.log
chmod 600 /var/log/santa.log

touch /var/log/elf.log
chmod 600 /var/log/elf.log

touch /var/log/children.log
chmod 600 /var/log/children.log

./north_poole.py >> /var/log/north_poole.log 2>&1 &
sleep 2

export NORTH_POOLE=http://localhost

./santa.py >> /var/log/santa.log 2>&1 &

for name in jingle sparkle tinsel nog snowflake; do
  ELF_NAME="$name" ./elf.py >> /var/log/elf.log 2>&1 &
done

./children.py $CHILDREN >> /var/log/children.log 2>&1 &
