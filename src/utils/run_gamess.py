import logging
import os
import pathlib
import shutil
import subprocess
import sys
import uuid

from utils.run_ff import FFException, FFKnownException, FFBasisException, FFBadMultException

gamess_path = pathlib.Path(__file__).parent.parent.parent / "gamess_linux"
if os.name == 'nt':
    gamess_path = pathlib.Path("C:\\Users\\Public\\gamess-64")


def _run(_dir, _input):
    aux = gamess_path / "auxdata"
    restart = _dir / "restart"
    scratch = _dir / "scratch"
    input_dir = _dir / "inputs"
    output_dir = _dir / "outputs"
    os.environ.update({
        'SCR': str(restart.absolute()),
        'USERSCR': str(restart.absolute()),
        'GMSPATH': str(gamess_path.absolute())
    })
    [_.mkdir(exist_ok=True) for _ in (restart, scratch, input_dir, output_dir)]
    input_file = input_dir / "input.inp"
    logfile = output_dir / f"LOGFILE_{uuid.uuid4()}"
    cpus = str(len(os.sched_getaffinity(0)) if os.name != 'nt' else os.cpu_count())
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
    if os.name == 'nt':
        subprocess.run(
            [gamess_path / "rungms.bat", input_file, "2022.R2.intel", cpus, logfile.absolute()],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            cwd=_dir
        )
    else:
        with open(logfile, "w") as f:
            subprocess.run(
                ["csh", gamess_path / "rungms", input_file, "2022.2", cpus, "1", "0"],
                check=True,
                stdout=f,
                stderr=sys.stderr,
                cwd=_dir
            )

    with open(logfile) as f:
        log = f.read()
        if "CHECK YOUR INPUT CHARGE AND MULTIPLICITY" in log:
            raise FFBadMultException("Bad mult")
        if "SCF DOES NOT CONVERGE AT VIB0 POINT" in log:
            raise FFKnownException(f"Did not converge")
        if "ERROR, ILLEGAL POINT GROUP" in log:
            raise FFKnownException(f"Bad point group")
        if " BASIS FUNCTION REQUESTED" in log:
            raise FFBasisException(f"Bad basis function")
        if "EXECUTION OF GAMESS TERMINATED -ABNORMALLY-" in log:
            raise FFException(f"Error running gamess: {log[log.find('ERROR'):]}")


def extract_field_from_output(name, punch):
    vec_data = punch[punch.find(name) + len(name):]
    vec_data = vec_data[:vec_data.find("$END")]
    return vec_data


def get_config(gbasis="CCD"):
    return f"""
 $SYSTEM MWORDS=100 $END
 $BASIS GBASIS={gbasis} NGAUSS=6 $END
"""


# noinspection DuplicatedCode
def calculate_hess(input_data, _dir, config_args=(), add_charge=False):
    _run(_dir, f"""
 $CONTRL SCFTYP=RHF MULT=1 NPRINT=0 COORD=CART UNITS=ANGS {'ICHARG=1' if add_charge else ''}
 RUNTYP=OPTIMIZE ICUT=12 ITOL=25 DFTTYP=B3LYP NOSYM=1 {'ISPHER=1' if not config_args else ''}
 $END
 {get_config(*config_args)}
 $FORCE METHOD=NUMERIC VIBANL=.TRUE. PURIFY=.t. NVIB=2 $END
 $SCF DIRSCF=.TRUE. $END
 $CPHF CPHF=AO $END
 $STATPT OPTTOL=1e-6 NSTEP=200 HESS=CALC IHREP=0 HSSEND=.TRUE. $END
{input_data}
""")

    punch = "\n".join(open(_).read() for _ in (_dir / "restart").glob("*.dat"))
    return punch


def calculate_raman(input_data, _dir, punch, config_args=(), add_charge=False):
    _run(_dir, f"""
 $CONTRL SCFTYP=RHF MULT=1 NPRINT=0 COORD=UNIQUE COORD=CART UNITS=ANGS {'ICHARG=1' if add_charge else ''}
 RUNTYP=RAMAN ICUT=12 ITOL=25 {'ISPHER=1' if not config_args else ''}
 $END
 {get_config(*config_args)}
 $RAMAN EFIELD=0.002 $END
{input_data}
 $VEC
 {extract_field_from_output("$VEC", punch).strip()}
 $END
 $HESS
{extract_field_from_output("$HESS", punch).strip()}
 $END
""")


def run_with_input(raw_input_data, _dir: pathlib.Path, raise_error=False, config_args=(), add_charge=False):
    if not _dir.exists():
        _dir.mkdir(parents=True)
    input_data = raw_input_data[raw_input_data.find(" $DATA"):raw_input_data.rfind(" $END") + 5]
    completed_ok = True
    try:
        try:
            punch = calculate_hess(raw_input_data, _dir, config_args, add_charge)
            calculate_raman(raw_input_data, _dir, punch, config_args, add_charge)
        except FFBasisException:
            if config_args == ():
                return run_with_input(input_data, _dir, raise_error, config_args=("STO",), add_charge=add_charge)
            else:
                raise
        except FFBadMultException:
            if add_charge is False:
                return run_with_input(input_data, _dir, raise_error, config_args, add_charge=True)
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
