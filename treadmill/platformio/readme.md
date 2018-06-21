## Platformio

This folder contains code to be uploaded to a teensy/arduino microcontroller. To do this from the command line, use platformio.

See the [comparison chart](https://www.pjrc.com/teensy/techspecs.html), the best option is Teensy 35.

The code relies on two teensy/arduino libraries

 - [AccelStepper library](https://www.pjrc.com/teensy/td_libs_AccelStepper.html)
 - [Encoder library](https://www.pjrc.com/teensy/td_libs_Encoder.html)
 
See [this][blog1] blog post for getting started. Also, see a recent bug report and the fix in the [teensy forum][teensy-forum] and the [platformio forum][platformio-forum]. As always with open source, it is not good because it is free, it is good because it improves with user feedback. Please contribute.


## Preliminaries

Add user pi to dialout group

	sudo usermod -a -G dialout pi

Install udev rules so you can talk to serial ports on usb. Download [49-teensy.rules](https://www.pjrc.com/teensy/49-teensy.rules). See end of this page for a copy of its contents.

	sudo pico /etc/udev/rules.d/49-teensy.rules

	# reboot the raspberry pi
	sudo reboot

## Install (using our script)

This assumes you have a Teensy 3.2/3.3

	cd homecage/treadmill/platformio
	./install-treadmill.sh
	
## Install platformio (manually)

	cd ~/homecage/treadmill/platformio

	# make a python 2 virtual environment
	virtualenv -p python2 --no-site-packages env

	source env/bin/activate
	
	pip install -U platformio
	
## Upload treadmill.cpp to a teensy 2 (manually)

	cd ~/homecage/treadmill/platformio/treadmill
	sudo ../env/bin/platformio run --target upload
	
After a lot of output, you should see something like

```
AVAILABLE: jlink, teensy-cli, teensy-gui
CURRENT: upload_protocol = teensy-cli
Rebooting...
Uploading .pioenvs/teensy31/firmware.hex
Teensy Loader, Command Line, Version 2.1
Read ".pioenvs/teensy31/firmware.hex": 30332 bytes, 11.6% usage
Soft reboot performed
Waiting for Teensy device...
(hint: press the reset button)
Found HalfKay Bootloader
Read ".pioenvs/teensy31/firmware.hex": 30332 bytes, 11.6% usage
Programming..............................
Booting
======================================== [SUCCESS] Took 19.42 seconds ========================================
```

# Troubleshooting

## Check that platformio.ini specifies your particular board

```
more platform.ini
```

```
[env:teensy31]
platform = teensy
board = teensy31
framework = arduino
```

## Get a list of boards

```
platformio boards

```

```
Platform: teensy
--------------------------------------------------------------------------------
ID                    MCU            Frequency  Flash   RAM    Name
--------------------------------------------------------------------------------
teensy20              ATMEGA32U4     16MHz     31.50KB 2.50KB Teensy 2.0
teensy30              MK20DX128      48MHz     128KB   16KB   Teensy 3.0
teensy31              MK20DX256      72MHz     256KB   64KB   Teensy 3.1 / 3.2
teensy35              MK64FX512      120MHz    512KB   192KB  Teensy 3.5
teensy36              MK66FX1M0      180MHz    1MB     256KB  Teensy 3.6
teensylc              MKL26Z64       48MHz     62KB    8KB    Teensy LC
teensy20pp            AT90USB1286    16MHz     127KB   8KB    Teensy++ 2.0
```

As an example, add a teensy 3.5 to platformio.ini with

	platformio init --board=teensy35

## Check which serial ports platformio is using

```
platformio device list
```

```
/dev/ttyACM0
------------
Hardware ID: USB VID:PID=16C0:0483 SER=1756190 LOCATION=1-1.1.2:1.0
Description: USB Serial

/dev/ttyAMA0
------------
Hardware ID: 3f201000.serial
Description: ttyAMA0
```

## Make a simple project to debug uploading to teensy

	mkdir blink
	cd blink

	#Initialize blink project with teensy 3.1/3.2 boards
	# this will create file platformio.ini and 
	# folders /src and /lib
	../env/bin/platformio init --board=teensy31
	
Copy the following into blink/src/main.cpp

	pico src/main.cpp

```
/*
 * Blink
 * Turns on an LED on for one second,
 * then off for one second, repeatedly.
 */
#include "Arduino.h"

void setup()
{
  // initialize LED digital pin as an output.
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop()
{
  int myDelay = 1000;

  // turn the LED on
  digitalWrite(LED_BUILTIN, HIGH);
  delay(myDelay);

  // turn the LED off
  digitalWrite(LED_BUILTIN, LOW);
  delay(myDelay);
}
```

Upload the blink project to teensy

```
sudo ../env/bin/platformio run --target upload

# if running into problems, try to clean and then upload again
sudo ../env/bin/platformio run --target clean
```

## To sudo or not

To upload to teensy you should use sudo. To create a new project you should not.

## udev rules

Here is the contents of [49-teensy.rules](https://www.pjrc.com/teensy/49-teensy.rules)

```
# UDEV Rules for Teensy boards, http://www.pjrc.com/teensy/
#
# The latest version of this file may be found at:
#   http://www.pjrc.com/teensy/49-teensy.rules
#
# This file must be placed at:
#
# /etc/udev/rules.d/49-teensy.rules    (preferred location)
#   or
# /lib/udev/rules.d/49-teensy.rules    (req'd on some broken systems)
#
# To install, type this command in a terminal:
#   sudo cp 49-teensy.rules /etc/udev/rules.d/49-teensy.rules
#
# Or use the alternate way (from this forum message) to download and install:
#   https://forum.pjrc.com/threads/45595?p=150445&viewfull=1#post150445
#
# After this file is installed, physically unplug and reconnect Teensy.
#
ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789B]?", ENV{ID_MM_DEVICE_IGNORE}="1"
ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789A]?", ENV{MTP_NO_PROBE}="1"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789ABCD]?", MODE:="0666"
KERNEL=="ttyACM*", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789B]?", MODE:="0666"
#
# If you share your linux system with other users, or just don't like the
# idea of write permission for everybody, you can replace MODE:="0666" with
# OWNER:="yourusername" to create the device owned by you, or with
# GROUP:="somegroupname" and mange access using standard unix groups.
#
#
# If using USB Serial you get a new device each time (Ubuntu 9.10)
# eg: /dev/ttyACM0, ttyACM1, ttyACM2, ttyACM3, ttyACM4, etc
#    apt-get remove --purge modemmanager     (reboot may be necessary)
#
# Older modem proding (eg, Ubuntu 9.04) caused very slow serial device detection.
# To fix, add this near top of /lib/udev/rules.d/77-nm-probe-modem-capabilities.rules
#   SUBSYSTEMS=="usb", ATTRS{idVendor}=="16c0", ATTRS{idProduct}=="04[789]?", GOTO="nm_modem_probe_end" 
#
```

[blog1]: http://blog.cudmore.io/post/2016/02/13/Programming-an-arduino-with-platformio/
[teensy-forum]: https://forum.pjrc.com/threads/52805-Uploading-to-teensy-with-platformio-gives-error-teensy_reboot-not-found-(Raspberry-Pi
[platformio-forum]: https://github.com/platformio/platform-teensy/issues/38