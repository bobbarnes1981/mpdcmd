
# create venv

python -m venv --upgrade-deps venv

# windows

activate

```venv/scripts/activate```

deactivate

```deactivate```

install requirements

```pip install -r requirements.txt```

run

```python .\mpdcmd\```

# linux

activate

```source venv/bin/activate```

install requirements

on debian bookworm ```apt-get install libgtk-3-dev``` is required for wxPython

```pip install -r requirements.txt```

run

```python ./mpdcmd/```
