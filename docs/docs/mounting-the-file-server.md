
It is easy to make the Raspberry Pi a file server. See [AFP / Netatalk / Avahi or Samba][1] for install instrucitons

## MacOS

This assumes that apple-file-protocol (AFP) is installed and running on the Pi

    afp://[IP]
    
## Windows

This assumes Samba (SMB) is running and installed on the Pi

    smb:\\[IP]
    
[1]: http://blog.cudmore.io/post/2017/11/22/raspian-stretch/