Homecage is a Raspberry Pi camera controller.

## Features

- Web interface
- Record video
- Stream video
- Record video on GPIO/TTL triggers

## 1) Get a functioning Raspberry Pi

These instructions assume you have a functioning Raspberry Pi 2/3 with Raspian Stretch installed. To get started setting up a Pi from scratch, see our [setup intructions][0].

## 2) Clone the homecage repository

	git clone --depth=1 https://github.com/cudmore/homecage.git

## 3) Install homecage with our install script

	cd homecage/homecage_app
	./install-homecage.sh
	
If everything goes well, all the software should be ready to go. Point your browser to

	http://[your_ip]:5000

See our online documentation for detailed [install instructions][1].

[0]: http://blog.cudmore.io/post/2017/11/22/raspian-stretch/
[1]: http://blog.cudmore.io/homecage/installing-the-software/