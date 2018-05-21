		while true; do
			read -p "Are all your streaming browser windows closed? [y/n]" yn
			case $yn in
				[Yy]* ) echo "stopping video stream";sudo kill -9 $uv4lPID;exit;;
				[Nn]* ) echo "stream stop cancelled by user";exit;;
				* ) echo "Please answer yes or no with 'y' or 'n'.";;
			esac
		done
