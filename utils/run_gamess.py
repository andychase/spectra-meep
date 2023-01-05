import logging
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import uuid

from utils.run_ff import FFException, FFKnownException, FFBasisException

gamess_path = pathlib.Path(__file__).parent.parent / "gamess_linux"


def _run(_dir, _input):
    aux = gamess_path / "auxdata"
    restart = _dir / "restart"
    scratch = _dir / "scratch"
    input_dir = _dir / "inputs"
    output_dir = _dir / "outputs"
    [_.mkdir(exist_ok=True) for _ in (restart, scratch, input_dir, output_dir)]
    input_file = input_dir / "input.inp"
    logfile = output_dir / f"LOGFILE_{uuid.uuid4()}"
    cpus = subprocess.check_output(["nproc"], text=True).strip()
    if restart.exists():
        shutil.rmtree(restart)
        restart.mkdir()
    with open(_dir / "rungms.gms", "w") as f:
        f.write(f"""
GAMESSDIR={gamess_path.absolute()}
AUXDATADIR={aux.absolute()}
RESTARTDIR={restart.absolute()}
SCRATCHDIR={scratch.absolute()}
    """.strip())

    with open(input_file, "w") as f:
        f.write(_input)
    with open(logfile, "w") as f:
        subprocess.run(
            [
                "csh", gamess_path / "rungms", input_file, "2022.2", cpus, "1", "1"
            ],
            check=True,
            stdout=f,
            stderr=sys.stderr,
            cwd=_dir
        )
    with open(logfile) as f:
        log = f.read()
        if "SCF DOES NOT CONVERGE AT VIB0 POINT" in log:
            raise FFKnownException(f"Did not converge")
        if "ERROR, ILLEGAL POINT GROUP" in log:
            raise FFKnownException(f"Bad point group")
        if "ILLEGAL EXTENDED BASIS FUNCTION REQUESTED" in log:
            raise FFBasisException(f"Bad basis function")
        if "EXECUTION OF GAMESS TERMINATED -ABNORMALLY-" in log:
            raise FFException(f"Error running gamess: {log[log.find('ERROR'):]}")


def extract_field_from_output(name, punch):
    vec_data = punch[punch.find(name) + len(name):]
    vec_data = vec_data[:vec_data.find("$END")]
    return vec_data


def get_config(gbasis="N311"):
    return f"""
 $SYSTEM MWORDS=100 $END
 $BASIS GBASIS={gbasis} NGAUSS=6 $END
"""


# noinspection DuplicatedCode
def calculate_hess(input_data, _dir, config_args=()):
    _run(_dir, f"""
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

    punch = "\n".join(open(_).read() for _ in (_dir / "restart").glob("*.dat"))
    return punch


def calculate_raman(input_data, _dir, punch, config_args=()):
    _run(_dir, f"""
 $CONTRL SCFTYP=RHF MULT=1 NPRINT=0 COORD=UNIQUE
 RUNTYP=RAMAN ICUT=12 ITOL=25
 $END
 {get_config(*config_args)}
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


def run_with_input(input_data, raise_error=False, config_args=()):
    input_data = input_data[input_data.find("$DATA") + 5:input_data.rfind("$END")]
    completed_ok = True
    _dir = pathlib.Path("/tmp/spectra_meep")
    if _dir.exists():
        shutil.rmtree(_dir)
    _dir.mkdir(parents=True, exist_ok=True)

    completed_ok = True
    try:
        try:
            punch = calculate_hess(input_data, _dir)
            calculate_raman(input_data, _dir, punch)
        except FFBasisException:
            if config_args == ():
                return run_with_input(input_data, raise_error, config_args=("N31",))
            else:
                raise
    except FFKnownException:
        completed_ok = False
        print("Failed computing chem")
    except Exception:
        completed_ok = False
        logging.exception("Gamess failed")
        if raise_error:
            raise
    punch_files = [open(f).read() for f in _dir.glob("*.dat")]
    log_files = [open(f).read() for f in (_dir / "outputs").glob("LOGFILE*")]
    return completed_ok, punch_files, log_files
