# syntax=docker/dockerfile:1

FROM docker:dind

RUN apk add criu --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing/
RUN apk add tar

WORKDIR /check
copy . .

RUN mkdir /etc/docker
RUN echo '{ "experimental": true }' > /etc/docker/daemon.json
