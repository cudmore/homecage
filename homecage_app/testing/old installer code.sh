#
# append to .bashrc if neccessary
bash_append='export PATH='"$PWD/bin"':$PATH'

printf '\n === 5/5 Updating $PATH \n'

if [[ ":$PATH:" == *":$PWD/bin:"* ]]; then
  echo "   OK: Your path already contains $PWD/bin"
else
  echo '   Your $PATH is missing '"$PWD"'/bin, appending to '"$HOME"'/.bashrc'
	echo '      '$bash_append
	echo $bash_append | tee -a $HOME/.bashrc
fi

#
# make a homecage_dir variable so bin/homecage knows where it is installed
printf "\n === 6/6: Checking that homecage_path=$PWD \n"
if [[ "$homecage_path" == "$PWD" ]]; then
  echo "   OK: Your homecage_path is already set to $PWD"
else
	echo "   Appending to $HOME/.bashrc"
	tmp='export homecage_path="'"$PWD"'"'
	echo '      '$tmp
	echo $tmp | tee -a $HOME/.bashrc
fi

source $HOME/.bashrc

