- Build a box to hold cages, lights, and camera
- Strap the computer to the side, place on top or put inside the box. If placing inside the box, make sure to make an inner box to block LEDs on computer.

## Computer

- Raspberry Pi 3 [Canakit at Amazon][5]
    - 5V AC/DC power, 2A
    - SD card, class 10, 32 GB (for system installation, 16 GB is fine, class 10 is important)
    - Case
- USB key, 64 GB (to save video)
- Ethernet cable

## Camera
- [Raspberry Pi NoIR, 8 MP, Version 2][4].
- CSI Camera cable

## Lights
- 12V AC/DC adapter, 1 Amp
- [2-channel relay][6] (to switch lights on/off)
- [850 nm IR LEDs][7]. Don't use IR LEDs >900nm as the camera is not very sensitive in this range and images will be grainy.
- White LEDs
- Resistors to go inline with all LEDs. All LEDs need resistors!

## Environmental
- [DHT 22 temperature and humidity sensor][3]
- [SI1145 Digital UV Index / IR / Visible Light Sensor][2]

[2]: https://www.adafruit.com/product/1777
[3]: https://www.adafruit.com/product/385?gclid=CjwKCAiA9f7QBRBpEiwApLGUip6TE2XPQx_9hVrRY83GHtGapdZq6H4t1ZHUJfuRXRTZdBMLvbmCJhoCWC4QAvD_BwE
[4]: https://www.adafruit.com/product/1567
[5]: https://www.amazon.com/CanaKit-Raspberry-Complete-Starter-Kit/dp/B01C6Q2GSY/ref=sr_1_2_sspa?s=electronics&ie=UTF8&qid=1512090648&sr=1-2-spons&keywords=canakit+raspberry+pi+3&psc=1
[6]: https://www.sainsmart.com/products/2-channel-5v-relay-module
[7]: https://www.sparkfun.com/products/9469