# script to install adafruit dht temperature sensor

source ~/homecage/homecage_app/env/bin/activate

sudo apt-get install python3-dev

cd
rm -Rf Adafruit_Python_DHT
git clone https://github.com/adafruit/Adafruit_Python_DHT.git
cd Adafruit_Python_DHT
python setup.py install

deactivate
