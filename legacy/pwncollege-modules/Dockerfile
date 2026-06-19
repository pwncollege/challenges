FROM pwncollege/pwnshop:latest
RUN apt update && apt-get -y install parallel
ADD . /modules
RUN mkdir /home/hacker && chown 1000:1000 /home/hacker
WORKDIR /modules/pwncollege_modules
