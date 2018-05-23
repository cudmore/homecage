Videowall is Javascript code and a python web-server to view and control multiple copies of homecage on different Raspberry Pi's! In theory, this allows you to control any number of Raspberry Pi's with their own cameras.

## Install

See the main homecage [install][install] page.
	
## Serve

Once homecage is [installed][install].

	cd ~/homecage/videowall_app/
	python videowall_app.py 

## Browse

	http://[your_pi_ip]:8000

## Example

This example shows controlling three Raspberry Pi computers, each running homecage. Any number of Raspberry Pi camera systems can be added with the 'Add Server' button. The videowall allows each Pi to be independently controlled.

<IMG SRC="../img/videowall.png">

[install]: http://blog.cudmore.io/homecage/installing-the-software/