. ./.venv/bin/activate
python3 -m piptools compile ./requirements.in -o ./requirements.txt
python3 -m pip install -r ./requirements.txt
