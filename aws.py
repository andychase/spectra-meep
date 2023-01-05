import multiprocessing
import os
import uuid

import boto3
import dotenv
import psycopg

import main
from utils.run_utils import compress_and_clean_dir

dotenv.load_dotenv(".env")

conn_config = dict(
    host=os.environ['POSTGRES_HOST'],
    port=5432,
    dbname=os.environ['POSTGRES_DB'],
    user=os.environ['POSTGRES_USERNAME'],
    password=os.environ['POSTGRES_PASSWORD']
)


def update_time(cur, name):
    cur.execute("""
        update meepdb.chem
        set last_activity = now()
        where name = %s
    """, (name,))


def with_conn():
    with psycopg.connect(autocommit=True, **conn_config) as conn:
        cur = conn.cursor()
        with conn.transaction():
            yield cur


def aws_loop():
    # Connect to database and get job
    name = None
    for cur in with_conn():
        cur.execute("""
            SELECT name, save_uuid
            
            from meepdb.chem c
            where (
                    last_activity is null or
                    last_activity < now() - interval '15 minutes'
                )
              and is_done is FALSE
            order by name_length
            limit 1 FOR UPDATE;
            """
                    )
        result = cur.fetchone()
        if not result:
            raise Exception("No result set returned!")
        name, save_uuid = result
        # Set last_activity to lock it
        update_time(cur, name)

    p = multiprocessing.Process(target=main.run_single, args=(name,))
    p.start()
    p.join(60)
    with psycopg.connect(autocommit=True, **conn_config) as conn:
        cur = conn.cursor()
        with conn.transaction():
            update_time(cur, name)

    # On completion
    save_uuid = str(uuid.uuid4())
    for gz_path in compress_and_clean_dir():
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.environ['AWS_USERNAME'],
            aws_secret_access_key=os.environ['AWS_PASSWORD']
        )
        s3_client.upload_file(gz_path, "spectrameep", save_uuid + ".tar.gz")
    for cur in with_conn():
        cur.execute("""
                update meepdb.chem
                set 
                    last_activity = now(),
                    is_done = TRUE,
                    save_uuid = %s
                
                where name = %s
            """, (save_uuid, name))

    # If there's a save uuid, pull it

    # If there's no save uuid
    # Start fresh else restart from checkpoint
    # Every 10 minutes
    # Checkpoint, end container
    # Save files with checkpoint
    # Upload checkpoint to s3
    # Save checkpoint in database
    # Re-start from checkpoint


if __name__ == "__main__":
    aws_loop()
