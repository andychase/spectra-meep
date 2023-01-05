import pathlib
import subprocess
import time
import dotenv

dotenv.load_dotenv()

# Connect to database and get job
q = """
SELECT FOR UPDATE
    
"""
# If last active > 10 minutes ago