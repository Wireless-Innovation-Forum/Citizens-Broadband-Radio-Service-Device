# CBSD Testing and Interoperability Repository

This repository contains the CBSD-facing mock Spectrum Access System (SAS),
WINNF test scenarios, expected messages, and historical laboratory certificates.
It works alongside `Spectrum-Access-System`, `Spectrum-Access_System-Release-2`,
and `Common-Data`; this mock server uses its bundled scenarios and does not
import those repositories' Python packages.

## Python support and installation

The target runtime is **Python 3.15**, with compatibility maintained for
**Python 3.11–3.14**. Python 2 and older Python 3 versions are no longer supported.
Python 3.15.0 was released on October 9, 2026:
[official release](https://www.python.org/downloads/release/python-3150/).

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and run
from this repository's root:

```sh
uv python install
uv sync --locked
```

`.python-version` selects Python 3.15.0. `uv sync` creates `.venv` automatically;
`uv run --locked` selects the environment without manual activation. If Python
3.15.0 is not yet available through your uv release, update uv or select an
existing interpreter with `uv sync --locked --python /path/to/python3.15`.

For an earlier supported interpreter, use `uv sync --locked --python 3.11`
and pass the same `--python 3.11` to `uv run`. Use 3.12, 3.13 or 3.14 in the
same way. `pyproject.toml` declares runtime requirements, while `uv.lock`
records the reproducible resolution across supported Python versions.

The project declares only direct runtime dependencies: current Flask,
JSON Schema, PyJWT, and cryptography. Python 2 backports and 2017 transitive
pins have been removed. CPI RS256 and ES256 verification uses modern PyJWT and
cryptography APIs with an explicit algorithm allowlist.

`requirements.txt` and `requirements-gui.txt` are compatibility exports of
`uv.lock`; regenerate them after intentionally updating dependencies:

```sh
uv lock --upgrade
uv export --locked --no-dev --no-hashes --no-emit-project -o requirements.txt
uv export --locked --extra gui --no-dev --no-hashes --no-emit-project -o requirements-gui.txt
```

The optional Tk GUI additionally needs the platform's Tkinter package and:

```sh
uv sync --locked --extra gui
```

The GUI finds scenarios relative to this checkout. Set `CBRS_LOGO_PATH` to a
local image path to display a logo.

## Running the mock SAS

Configure the host, port, JSON and CSV locations, SAS certificate and key,
client CA chain, and CPI certificate in
`CBRS_Mock_SAS_Python_Master/cbrsPython-master/Configuration/conf.xml`.
Paths are relative to `cbrsPython-master`; absolute paths also work.
The defaults now refer to certificate filenames actually present in the repo.

**The bundled certificates expired in 2018–2019.** They remain historical test
artifacts. Configure fresh matching lab credentials and CA chains before
performing a live TLS session; no certificate verification bypass is enabled.
The harness requires client certificates and preserves the TLS 1.2 protocol
and cipher list required by its existing WINNF scenarios.

```sh
uv run --locked python CBRS_Mock_SAS_Python_Master/cbrsPython-master/cbrsPython/controllers/StartOfProject.py
```

Enter a scenario name without `.csv`, for example `WINNF.FT.C.DRG.1`.
The default API URL prefix is `/v1.2/`. Enter `quit` at the scenario prompt to
finish the session. Logs are written under `cbrsPython-master/Logs`.

The power measurement harness is started separately:

```sh
uv run --locked python CBRS_Mock_SAS_Python_Master/cbrsPython-master/cbrsPython/controllers/StartPowerMeas.py
```

Enter numeric spectrum and EIRP values. During the session, `get` prints the
selected spectrum and `stop` shuts down the server. Optional XML/HTML reports
use the bundled Allure command and also require a Java runtime.

## Validation

```sh
uv run --locked python -m compileall -q CBRS_Mock_SAS_Python_Master/cbrsPython-master/cbrsPython
uv run --locked python -m unittest discover -s tests -v
```

CI runs on Python 3.11 through 3.15. The regression suite checks all 52 bundled
CSV scenarios, a mock registration → spectrum inquiry → grant → heartbeat →
relinquishment → deregistration exchange, RSA/ECDSA CPI signatures and rejection
of tampered or unsigned data, numeric CLI inputs, thread shutdown, and a real
mutual TLS handshake using fresh temporary certificates. These checks run
without radio hardware. Hardware interoperability, the graphical interface,
and Java/Allure report rendering require their corresponding lab environment.
