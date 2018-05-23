- Build a box to hold cages, lights, and camera
- Strap the computer to the side, place on top or put inside the box. If placing inside the box, make sure to make an inner box to block LEDs on computer.
- Total cost of each system is about $130, why not build 10!

## Computer

- [Raspberry Pi 3 B+][5]
    - 5V AC/DC power, 2.5A
    - SD card, class 10, 32 GB (for system installation, 16 GB is fine, class 10 is important)
    - Case
- USB key, 64 GB (to save video)
- Ethernet cable

## Camera
- [Raspberry Pi NoIR, 8 MP, Version 2][4].
- [Camera cable][camera-cable]

## Lights
- 12V AC/DC adapter, 1 Amp
- [2-channel relay][6] (to switch lights on/off)
- [850 nm IR LEDs][7]. Don't use IR LEDs >900nm as the camera is not very sensitive in this range and images will be grainy.
- White LEDs
- [Resistors][resistors] to go inline with all LEDs. All LEDs need resistors!

## Environmental
- [DHT 22 temperature and humidity sensor][3]
- [SI1145 Digital UV Index / IR / Visible Light Sensor][2]

[2]: https://www.adafruit.com/product/1777
[3]: https://www.adafruit.com/product/385?gclid=CjwKCAiA9f7QBRBpEiwApLGUip6TE2XPQx_9hVrRY83GHtGapdZq6H4t1ZHUJfuRXRTZdBMLvbmCJhoCWC4QAvD_BwE
[4]: https://www.adafruit.com/product/1567
[5]: https://www.amazon.com/CanaKit-Raspberry-Starter-Premium-Black/dp/B07BCC8PK7/ref=sr_1_4?m=A30ZYR2W3VAJ0A&s=merchant-items&ie=UTF8&qid=1527021869&sr=1-4
[6]: https://www.sainsmart.com/products/2-channel-5v-relay-module
[7]: https://www.sparkfun.com/products/9469
[camera-cable]: https://www.amazon.com/Adafruit-Flex-Cable-Raspberry-Camera/dp/B00M4DAQH8/ref=pd_sbs_147_1?_encoding=UTF8&pd_rd_i=B00M4DAQH8&pd_rd_r=1771c45c-5e01-11e8-a189-b96ead17a581&pd_rd_w=6Vuvj&pd_rd_wg=nx7YA&pf_rd_i=desktop-dp-sims&pf_rd_m=ATVPDKIKX0DER&pf_rd_p=5825442648805390339&pf_rd_r=JEGBB5W0HSFMY635WRX9&pf_rd_s=desktop-dp-sims&pf_rd_t=40701&psc=1&refRID=JEGBB5W0HSFMY635WRX9&dpID=31PUNUIdRlL&preST=_SX300_QL70_&dpSrc=detail
[resistors]: https://www.sparkfun.com/products/10969?_ga=2.157718462.561418548.1527022055-731846762.1520642321