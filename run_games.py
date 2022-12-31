import logging
import os
import pathlib
import subprocess
import sys
import tempfile
import uuid

gamess_path = pathlib.Path("C:\\Users\\Public\\gamess-64")


class FFException(Exception):
    pass


def _run(_dir, _input):
    aux = gamess_path / "auxdata"
    restart = _dir / "restart"
    scratch = _dir / "scratch"
    input_dir = _dir / "inputs"
    output_dir = _dir / "outputs"
    [_.mkdir(exist_ok=True) for _ in (restart, scratch, input_dir, output_dir)]
    input_file = input_dir / "input.inp"
    logfile = output_dir / f"LOGFILE_{uuid.uuid4()}"
    with open(_dir / "rungms.gms", "w") as f:
        f.write(f"""
GAMESSDIR={gamess_path.absolute()}
AUXDATADIR={aux.absolute()}
RESTARTDIR={restart.absolute()}
SCRATCHDIR={scratch.absolute()}
    """.strip())

    with open(input_file, "w") as f:
        f.write(_input)
    subprocess.run(
        [
            gamess_path / "rungms.bat", input_file, "2022.R2.intel", "5", logfile.absolute()
        ],
        check=True,
        stdout=sys.stdout,
        stderr=sys.stderr,
        cwd=_dir
    )
    if not logfile.exists():
        raise FFException("No LOGFILE found")
    with open(logfile) as f:
        log = f.read()
        if "GAMESS TERMINATED -ABNORMALLY-" in log:
            raise FFException(f"Error running gamess: {log[log.find('ERROR'):]}")


def extract_field_from_output(name, punch):
    vec_data = punch[punch.find(name) + len(name):]
    vec_data = vec_data[:vec_data.find("$END")]
    return vec_data

CONFIG = """"
 $SYSTEM MWORDS=100 MEMDDI=100 $END
 $BASIS GBASIS=N31 NGAUSS=6 $END
"""

# noinspection DuplicatedCode
def calculate_hess(input_data, _dir):
    _run(_dir, f"""
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

    punch = "\n".join(open(_).read() for _ in (_dir / "restart").glob("*.dat"))
    return punch



def calculate_raman(input_data, _dir, punch):
    _run(_dir, f"""
 $CONTRL SCFTYP=RHF MULT=1 NPRINT=0 COORD=UNIQUE
 RUNTYP=RAMAN ICUT=12 ITOL=25
 $END
 {CONFIG}
 $RAMAN EFIELD=0.002 $END
 $DATA

{input_data.strip()}
 $END
 $VEC
 {extract_field_from_output("$VEC", punch).strip()}
 $END
 $HESS
{extract_field_from_output("$HESS", punch).strip()}
 $END
	""")

def clean_log_file(log_file):
    return log_file.split("     RUN TITLE", 1)[1]

def run_with_input(input_data, raise_error=False):
    input_data = input_data[input_data.find("$DATA") + 5:input_data.rfind("$END")]
    with tempfile.TemporaryDirectory() as scratch_dir:
        _dir = pathlib.Path(scratch_dir)
        completed_ok = True
        try:
            punch = calculate_hess(input_data, _dir)
            calculate_raman(input_data, _dir, punch)
        except:
            completed_ok = False
            if raise_error:
                raise
            else:
                logging.exception("Gamess failed")
        punch_files = [open(f).read() for f in _dir.glob("*.dat")]
        log_files = [clean_log_file(open(f).read()) for f in (_dir / "outputs").glob("LOGFILE*")]
        return completed_ok, punch_files, log_files
