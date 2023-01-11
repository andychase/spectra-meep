import multiprocessing
import os
import pathlib
import uuid

from utils import run_gamess
from utils.db import with_conn, get_s3_client
from utils.run_utils import compress_and_clean_dir


def run_single(gms_input, _dir):
    completed_ok, punch_files, logfiles = run_gamess.run_with_input(gms_input, _dir)
    exit(0 if completed_ok else 1)


def update_time(cur, name):
    cur.execute("""
        update meepdb.chem
        set last_activity = now()
        where name = %s
    """, (name,))


def aws_loop(_dir):
    # Connect to database and get job
    name = None
    gms_input = None
    # If min_length environ added, append sql
    min_length_sql = ""
    if os.environ.get("MIN_LENGTH"):
        min_length_sql = f"""and name_length > {int(os.environ["MIN_LENGTH"])}"""
    for cur in with_conn():
        cur.execute(f"""
            SELECT name, save_uuid, gms_input
            from meepdb.chem c
            where (
                    last_activity is null or
                    last_activity < now() - interval '15 minutes'
                )
              and is_done is FALSE
              {min_length_sql}
            order by name_length
            limit 1 FOR UPDATE;
            """)
        result = cur.fetchone()
        if not result:
            raise Exception("No result set returned!")
        name, save_uuid, gms_input = result
        print("----~~~----")
        print(name)
        print("----~~~----")
        # Set last_activity to lock it
        update_time(cur, name)

    p = multiprocessing.Process(target=run_single, args=(gms_input, _dir))
    p.start()
    while True:
        p.join(60)
        for cur in with_conn():
            update_time(cur, name)
        if not p.is_alive():
            break
    completed_ok = p.exitcode == 0
    # On completion
    save_uuid = str(uuid.uuid4())
    for gz_path in compress_and_clean_dir(_dir):
        s3_client = get_s3_client()
        s3_client.upload_file(gz_path, "spectrameep", save_uuid + ".tar.gz")
    for cur in with_conn():
        cur.execute("""
                update meepdb.chem
                set 
                    last_activity = now(),
                    is_done = TRUE,
                    save_uuid = %s,
                    completed_ok = %s
                
                where name = %s
            """, (save_uuid, completed_ok, name))

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
    aws_loop(pathlib.Path("/tmp/spectra_meep"))
