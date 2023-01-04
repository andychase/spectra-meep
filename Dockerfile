# syntax=docker/dockerfile:1

FROM python:3.8-slim-bullseye

RUN dpkg --add-architecture i386 && apt-get update && apt-get install -y \
    openbabel \
    openbabel-gui \
    libopenbabel-dev \
    build-essential \
    swig \
    libc6:i386 libncurses5:i386 libstdc++6:i386

RUN ln -s /usr/include/openbabel3 /usr/local/include/openbabel3


WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

CMD [ "python3", "aws.py"]
