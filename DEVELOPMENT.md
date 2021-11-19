# Development Setup Instructions

## Initial Setup

The following steps are the initial instructions to clone the codebase locally and setup a virtualenv.

1. Clone repo:

```
git clone git@github.com:WLAN-Pi/wlanpi-fpms.git && cd wlanpi-fpms
```

2. Create virtualenv:

```
python3 -m venv venv
```

3. Activate venv:

```
source venv/bin/activate
```

5. Update pip, setuptool, and wheel (this is only done once)

```
pip install -U pip setuptools wheel
```

6. Install requirements

```
pip install -r requirements.txt
```

## Executing the wlanpi-fpms module

Ok, now should be read to run the code. This version of the fpms is packaged into a module. So, we need to instruction Python to run it as a module with the `-m` option.

1. Activate the virtualenv

```
source venv/bin/activate
```

2. We need to run fpms as sudo, which means we'll need to pass along the location of the Python environment to sudo like this:

```
sudo venv/bin/python3 -m fpms
```

Further reading on executing modules with Python at <https://docs.python.org/3/library/runpy.html>.

## Cheatsheat

Is your development environment already setup?

```
cd <root of repo>
source venv/bin/activate
sudo venv/bin/python3 -m fpms
```