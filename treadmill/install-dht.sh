# Robert Cudmore
# 20180625

# This bash script will attempt to install the Adafruit Python DHT library

if [ $(id -u) = 0 ]; then
   echo "Do not run with sudo. Try again without sudo"
   exit 1
fi

source env/bin/activate

sudo apt-get install python3-dev

cd

if [ -d "Adafruit_Python_DHT" ]; then
  rm -Rf Adafruit_Python_DHT
fi

git clone https://github.com/adafruit/Adafruit_Python_DHT.git

cd Adafruit_Python_DHT

python setup.py install

deactivate
