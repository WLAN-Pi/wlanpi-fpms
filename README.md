# fpms
**WLAN Pi Front Panel Menu System** 

This project is the consolidation of the forked NanoHatOLED & BakeBit repos that were used to build the original front panel menu system for the WLAN Pi.

The original repos contained many files that were not needed for the WLAN Pi, and were also based on python 2. This provided a number of support issues. Therefore, both repos were combined in to a unified repo, conversions were completed to support python 3 and extraneous files from the original repos were removed to provide a slimmed down code base.

## Installation notes

Before fpms can be installed, some additional python3 modules are required. Complete the following steps:

``` 
sudo apt-get update
sudo apt-get install python3-smbus
sudo python3 -m pip install pillow
```

The following steps must also be completed:

    1. Edit the oled-start file : "sudo nano /usr/local/bin/oled-start"

        from:

            #!/bin/sh
            cd /home/wlanpi/NanoHatOLED
            ./NanoHatOLED

        to:

            #!/bin/sh
            cd /usr/local/fpms
            ./NanoHatOLED

    2. Clone the "fpms" repo as wlanpi user:

        cd /usr/local
        sudo git clone https://github.com/WLAN-Pi/fpms.git

    3. Remove the old NanoHatOLED folder:

        cd ~
        sudo rm -rf ./NanoHatOLED
    
    4. Remove the network info cron entry "@reboot /home/wlanpi/NanoHatOLED/BakeBit/Software/Python/scripts/networkinfo/networkinfocron.sh" by editing cron with:

        sudo crontab -e

    5. Sync filesystem:

        sudo sync

    6. Power off/on (not reboot from CLI ) the WLAN Pi 

Once the fpms package has been successfully installed and is operational, it may be updated using the WLAN Pi package admin tool 'pkg_admin":

```
    pkg_admin -i fpms -b <branch/version name>
```

## Original Migration Notes

The move to python 3.5 required several file updates to provide support for the new python version. When moving to python 3.7 in the future, these will need to be completed again (with appropriate updates for 3.7) to support the new version. The steps are documented here for future reference (these were kindly figured out & provided by Adrian Granados):

    1. Update the package list and install the following packages:

    sudo apt-get update
    sudo apt-get install python3-smbus
    sudo python3 -m pip install pillow

    2. In line 90 of ~/NanoHatOLED/Source/main.c, replace the string “python2.7” with “python3.5” so that it reads as follows:

    rv = find_pid_by_name( "python3.5", py_pids);

    3. In line 119 of ~/NanoHatOLED/Source/main.c, replace the string “python” with “python3” so that it reads as follows:

    sprintf(cmd, "cd %s/BakeBit/Software/Python && python3 %s 2>&1 | tee /tmp/nanoled-python.log", workpath, python_file);

    3. Recompile NanoHatOLED:

    cd ~/NanoHatOLED
    gcc Source/daemonize.c Source/main.c -lrt -lpthread -o NanoHatOLED

    4. Update syntax errors thrown up by the new version of python in the following files:
        NanoHatOLED/BakeBit/Software/Python/bakebit_128_64_oled.py
        NanoHatOLED/BakeBit/Software/Python/bakebit_nanohat_oled.py


