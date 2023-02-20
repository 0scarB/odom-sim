#!/bin/bash

.venv/bin/python3 -m piptools compile ./requirements.in -o ./requirements.txt
.venv/bin/python3 -m pip install -r ./requirements.txt
