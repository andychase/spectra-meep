FROM python:3.8-slim-bullseye

COPY gamess_linux /app/gamess_linux

RUN apt-get update && apt-get install -y \
    software-properties-common \
    swapspace \
    libpq-dev

# Set up gamess
WORKDIR /app/gamess_linux
COPY script/build.sh .
RUN bash build.sh

# Set up python supervisor
WORKDIR /app
COPY src/requirements.txt src/requirements.txt
RUN pip3 install -r src/requirements.txt
COPY src src

CMD [ "python3", "./src/aws.py"]
