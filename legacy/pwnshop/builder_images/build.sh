#!/bin/bash -ex

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for UV in 16 18 20 22 24
do
	docker pull ubuntu:"$UV".04
	docker build --build-arg BASE=ubuntu:"$UV".04 -t pwncollege/pwnshop-builder:ubuntu"$UV"04 - < builder-ubuntu.docker
	docker push pwncollege/pwnshop-builder:ubuntu"$UV"04
done
