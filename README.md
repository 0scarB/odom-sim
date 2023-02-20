## Environment setup (Mac/Linux)
```bash
#!/bin/bash

python3.10 -m venv .venv
.venv/bin/pip install pip-tools
./setup-requirements.sh
```

## Start Simulation as Static Site (Mac/Linux)
```bash
#!/bin/bash

./static.sh
```
Open http://0.0.0.0:8000 in your browser.

## Start Simulation and Keyboard Input Capture through Webserver (Mac/Linux)
```bash
#!/bin/bash

./serve.sh
```
Open http://0.0.0.0:8000/sim in your browser.

## Run Tests
```bash
#!/bin/bash

./test.sh
```