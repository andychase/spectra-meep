import logging
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import uuid
import uuid
import platform

ff_path = pathlib.Path(__file__).parent.parent / "ff" / "Firefly820.exe"
if platform.system() == "Linux":
    ff_path = (pathlib.Path(__file__).parent.parent / "ff_linux" / "firefly820").absolute()


class FFException(Exception):
    pass


class FFKnownException(FFException):
    pass


class FFBasisException(FFKnownException):
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
        if "SCF DOES NOT CONVERGE AT VIB0 POINT" in log:
            raise FFKnownException(f"Did not converge")
        elif "ILLEGAL EXTENDED BASIS FUNCTION REQUESTED" in log:
            raise FFBasisException(f"Bad basis function")
        elif "FIREFLY TERMINATED ABNORMALLY" in log:
            raise FFException(f"Error running firefly: {log[log.find('RUN TITLE'):]}")
    return punch_file


def get_config(gbasis="N311"):
    return f""""
 $SYSTEM MWORDS=100 $END
 $BASIS GBASIS={gbasis} NGAUSS=6 $END
"""


# noinspection DuplicatedCode
def calculate_hess(input_data, _dir, config_args=()):
    punchfile = _run(_dir, f"""
 $CONTRL SCFTYP=RHF MULT=1 NPRINT=0 COORD=UNIQUE
 RUNTYP=OPTIMIZE ICUT=12 ITOL=25 DFTTYP=B3LYP NOSYM=1
 $END
 {get_config(*config_args)}
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


def calculate_raman(input_data, _dir, vec_data, hess_data, config_args=()):
    _run(_dir, f"""
 $CONTRL SCFTYP=RHF MULT=1 NPRINT=0 COORD=UNIQUE
 RUNTYP=RAMAN ICUT=12 ITOL=25
 $END
 {get_config(*config_args)}
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


def run_with_input(input_data, raise_error=False, config_args=()):
    input_data = input_data[input_data.find("$DATA") + 5:input_data.rfind("$END")]
    completed_ok = True
    scratch_dir = "/tmp/spectra_meep"
    _dir = pathlib.Path(scratch_dir)
    _dir.mkdir(parents=True, exist_ok=True)
    try:
        try:
            hess_data, vec_data = calculate_hess(input_data, _dir)
            calculate_raman(input_data, _dir, vec_data, hess_data)
        except FFBasisException:
            if config_args == ():
                return run_with_input(input_data, raise_error, config_args=("N31",))
            else:
                raise
    except FFKnownException as e:
        completed_ok = False
        print(*e.args)
        if raise_error:
            raise
    except Exception:
        completed_ok = False
        if raise_error:
            raise
        logging.exception("Firefly failed")
    punch_files = [open(f).read() for f in _dir.glob("PUNCH*")]
    log_files = [open(f).read() for f in _dir.glob("LOGFILE*")]
    return completed_ok, punch_files, log_files


def compress_and_clean_dir():
    scratch_dir = "/tmp/spectra_meep"
    _dir = pathlib.Path(scratch_dir)
    gz_path = _dir.parent / "output.tar.gz"
    subprocess.check_call(["tar", "czvf", gz_path, _dir])
    for _dirs in pathlib.Path("/tmp").glob("spectra*"):
        if _dirs.is_dir():
            shutil.rmtree(_dirs)
        else:
            _dirs.unlink(missing_ok=True)
    yield gz_path
    gz_path.unlink(missing_ok=True)
