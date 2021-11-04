# Initial Development Setup

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

5. Update pip, setuptool, and wheel.

```
pip install -U pip setuptools wheel
```

6. Install requirements

```
pip install -r requirements.txt
```

Ok, now should be read to run.

7. Run fpms directly using sudo and specifying Python in our venv bin folder:

```
sudo venv/bin/python3 -m wlanpi_fpms
```

# Development instructions

If you've already followed the bringup instructions and installed the requirements, development looks like this:

```
cd <root of repo>
source venv/bin/activate
sudo venv/bin/python3 -m wlanpi_fpms
```