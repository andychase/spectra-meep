import os
import pathlib

import boto3
import dotenv
import psycopg
from botocore.config import Config

dotenv.load_dotenv(pathlib.Path(__file__).parent.parent / ".env")


def with_conn():
    conn_config = dict(
        host=os.environ['POSTGRES_HOST'],
        port=5432,
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USERNAME'],
        password=os.environ['POSTGRES_PASSWORD']
    )

    with psycopg.connect(autocommit=True, **conn_config) as conn:
        cur = conn.cursor()
        with conn.transaction():
            yield cur


def get_s3_client():
    s = boto3.Session(
        aws_access_key_id=os.environ['AWS_USERNAME'],
        aws_secret_access_key=os.environ['AWS_PASSWORD']
    )
    client = s.client('s3', config=Config(tcp_keepalive=True))
    return client
