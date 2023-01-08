# syntax=docker/dockerfile:1

FROM python:3.8-slim-bullseye
WORKDIR /app

COPY gamess_linux gamess_linux

RUN apt-get update &&  \
    apt-get install -y \
    software-properties-common \
    build-essential \
    swapspace \
    libpq-dev \
    csh gfortran libatlas-base-dev libxc-dev curl cmake

WORKDIR /app/gamess_linux
RUN bash -c '[ $(arch) == "aarch64" ] && mv install.arm64.info install.info'
RUN make clean
RUN make libxc -j$(nproc)
RUN make modules
RUN make
WORKDIR /app

COPY src/requirements.txt src/requirements.txt
RUN pip3 install -r src/requirements.txt

COPY src src

CMD [ "python3", "./src/aws.py"]
