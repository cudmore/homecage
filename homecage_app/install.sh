if [ $(id -u) = 0 ]; then
   echo "Do not run with sudo. Try again without sudo"
   exit 1
fi

./install-homecage.sh
./install-extras.sh

echo ' '
echo 'Done installing homecage server. The homecage server is running and will run at boot.'
echo 'Remember to install uv4l and avconv with ./install-extras.sh'
echo 'To use the server, point your browser to:'
echo "    http://$ip:5000"
