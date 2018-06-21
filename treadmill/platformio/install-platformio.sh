# 20180619

if [ $(id -u) = 0 ]; then
   echo "Do not run with sudo. Try again without sudo"
   exit 1
fi

if [ ! -d "env/" ]; then
	echo '==='
	echo "=== Making Python 2 virtual environment in $PWD/env"
	echo '==='
	mkdir env
	virtualenv -p python2 --no-site-packages env
fi

source env/bin/activate

echo '==='
echo "=== Installing platformio"
echo '==='

pip install -U platformio

echo '==='
echo "=== Uploading treadmill code to teensy"
echo '==='

cd treadmill
sudo ../env/bin/platformio run --target upload
