# syntax=docker/dockerfile:1

FROM python:3.8-slim-bullseye
WORKDIR /app

COPY ff_linux ff_linux
COPY gamess_linux gamess_linux

RUN dpkg --add-architecture i386 && \
    apt-get update &&  \
    apt-get install -y \
    software-properties-common \
    openbabel \
    openbabel-gui \
    libopenbabel-dev \
    build-essential \
    swig \
    swapspace \
    libpq-dev \
    csh gfortran libatlas-base-dev libxc-dev curl cmake \
    libc6:i386 libncurses5:i386 libstdc++6:i386

RUN ln -s /usr/include/openbabel3 /usr/local/include/openbabel3

COPY src/requirements.txt src/requirements.txt
RUN pip3 install -r src/requirements.txt

COPY src src

CMD [ "python3", "./src/aws.py"]
