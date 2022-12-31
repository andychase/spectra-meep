import logging
import os
import pathlib
import subprocess
import sys
import tempfile
import uuid
import platform

ff_path = "C:\\Users\\comp1\\Desktop\\ff820_windows\\Firefly820.exe"
if platform.system() == "Linux":
	ff_path = (pathlib.Path(__file__).parent / "ff_linux" / "firefly820").absolute()

class FFException(Exception):
	pass

def _run(_dir, _input):
	punch_file = _dir / "PUNCH"
	irc_file = _dir / "IRCDATA"
	log_file = _dir / "LOGFILE"
	input_file = _dir / "INPUT"
	with open(input_file, "w") as f:
		f.write(_input)
	if punch_file.exists():
		punch_file.rename(_dir / f"PUNCH_{uuid.uuid4()}")
	if irc_file.exists():
		irc_file.rename(_dir / f"IRCDATA_{uuid.uuid4()}")
	if log_file.exists():
		log_file.rename(_dir / f"LOGFILE_{uuid.uuid4()}")
	subprocess.run(
		[
			ff_path, "-p", "-r", "-i", input_file, "-o", log_file, "-t", _dir
		],
		check=False,
		stdout=sys.stdout,
		stderr=sys.stderr,
		cwd=_dir
	)
	if not (_dir / "LOGFILE").exists():
		raise FFException("No LOGFILE found")
	with open(_dir / "LOGFILE") as logfile:
		log = logfile.read()
		if "FIREFLY TERMINATED ABNORMALLY" in log:
			raise FFException(f"Error running firefly: {log[log.find('ERROR'):]}")
	return punch_file

CONFIG = """"
 $SYSTEM MWORDS=100 $END
 $BASIS GBASIS=N31 NGAUSS=6 $END
"""

# noinspection DuplicatedCode
def calculate_hess(input_data, _dir):
	punchfile = _run(_dir, f"""
 $CONTRL SCFTYP=RHF MULT=1 NPRINT=0 COORD=UNIQUE
 RUNTYP=OPTIMIZE ICUT=12 ITOL=25 DFTTYP=B3LYP NOSYM=1
 $END
 {CONFIG}
 $FORCE METHOD=NUMERIC VIBANL=.TRUE. PURIFY=.t. NVIB=2 $END
 $SCF DIRSCF=.TRUE. $END
 $CPHF CPHF=AO $END
 $STATPT OPTTOL=1e-6 NSTEP=200 HESS=CALC IHREP=0 HSSEND=.TRUE. $END
 $DATA

{input_data.strip()}
 $END
	""")

	punch = open(punchfile).read()
	hess_data = punch[punch.find("$HESS") + 5:]
	hess_data = hess_data[:hess_data.find("$END")]
	vec_data = punch[punch.find("$VEC") + 4:]
	vec_data = vec_data[:vec_data.find("$END")]
	return hess_data, vec_data

def calculate_raman(input_data, _dir, vec_data, hess_data):
	_run(_dir, f"""
 $CONTRL SCFTYP=RHF MULT=1 NPRINT=0 COORD=UNIQUE
 RUNTYP=RAMAN ICUT=12 ITOL=25
 $END
 {CONFIG}
 $DATA

{input_data.strip()}
 $END
 $VEC
 {vec_data.strip()}
 $END
 $HESS
{hess_data.strip()}
 $END
	""")

def run_with_input(input_data, raise_error=False):
	input_data = input_data[input_data.find("$DATA") + 5:input_data.rfind("$END")]
	completed_ok = True
	with tempfile.TemporaryDirectory() as scratch_dir:
		_dir = pathlib.Path(scratch_dir)
		try:
			hess_data, vec_data = calculate_hess(input_data, _dir)
			calculate_raman(input_data, _dir, vec_data, hess_data)
		except:
			completed_ok = False
			if raise_error:
				raise
			else:
				logging.exception("Firefly failed")
		punch_files = [open(f).read() for f in _dir.glob("PUNCH*")]
		log_files = [open(f).read() for f in _dir.glob("LOGFILE*")]
		return completed_ok, punch_files, log_files
