
## Camera

It is worth while checking out the [specs][3] as they are impressive.

Attach the camera to the Pi with a flat ribbon cable. The cable should have blue tabs on one side of each end. The blue tab goes towards the ethernet port on the Pi and towards the back of the camera (away from the lens).

<IMG SRC="../img/pi-noir-camera.png" width=400>

## Raspberry Pi B+/2/3 pinout

### Digital input/output pins

Each of the yellow numbered pins are digital input/output (DIO) pins. Your free to attach each component to the pin numbers of your choice. Just be sure that the pin numbers specified in the code match the way you wired the system.

### 5V and ground pins

There are multiple power and ground pins, use these to connect to the relay switch, the temperature sensor, and the light sensor. Conceptually, all the ground pins are the same, you can use a [bread-board][2] if you run out of ground pins.

<IMG SRC="../img/raspberry-pin-out.png" width=600>

## Lights

You want to use an external 12V AC/DC power supply for all the LEDs. Don't power the lights directly from the 5V pins on the Pi, it will not have anough current. A 1 Amp 12V adapter should be fine, don't worry, if it is under-powered your lights will be a little dim.

Never connect the 12V adapter directly to the Pi, instead use a relay switch.

Only work with DC current coming out of the AC/DC adapter, **DO NOT** work with AC power coming from the wall as it can kill you.

Use IR LEDs <900 nm as these are within the sensitivity range of the Pi NoIR camera. A lot of IR lights are 940nm, these are not well suited for use with the Pi NoIR camera but are designed for simple IR sensors you would use for a TV remote.

Here we will wire the system with the white LED on channel 1 and the IR LED on channel 2 of the relay switch.

<IMG SRC="../img/two-channel-relay.png" width=600>

### Connect a 12V AC/DC adapter, IR, and white lights to the two-channel relay switch.

 - Using an old 12V AC/DC adapter, cut the wire and stick the positive 'hot' wire into the center 'common' pin' of channel 1 on the relay switch. The 'hot' end wire usually has a white line down the length of the wire. You can also determine the 'hot' end using a multi-meter, it is the one that gives a positive (not negative) voltage when attached to the positive (normally red) end of the multi-meter.
 
 - Cut a bit of wire and connect the center 'common pin' of channel 1 to the center 'common pin' of channel 2. This is the 'hot' end.
 
 - Stick the positive end of the white LED into the 'normally closed' port of channel 1. Attach the negative end of the white LED to the 'ground' wire of the 12V AC/DC adapter.
 
 - Do the same for the IR LED. Stick the positive end into the 'normally closed' port of channel 2 on the relay switch. Attach the negative end of the IR LED to the 'ground' wire of the 12V AC/DC adapter.

One important concept is that 'all grounds are the same'. This includes the ground on the 12V AC/DC adapter, the ground of the LEDs, the ground of theRaspberry Pi, etc.

### Connect the Pi to the relay switch switch

 - Connect a DIO pin from the Pi to the 'In1=Digital Input' pin on the relay switch.
 
 - Connect a second DIO pin from the Pi to the 'In2=Digital Input' pin on the relay switch.
 
 - Connect a 5V pin from the Pi to the 'Vcc' pin on the relay switch.
 
 - Connect a ground pin from the Pi to the 'ground' pin on the relay switch.
  
## DHT 22 temperature sensor

This is powered by the Raspberry Pi. Connect 3 wires from the Pi to the sensor.

 - Connect a 5V pin from the pi to the 'VCC' pin on the sensor.
 
 - Connect a ground pin from the Pi to the 'GND' pin on the sensor.
 
 - Connect a DIO pin from the Pi to the 'DATA' pin on the sensor.

<IMG SRC="../img/dht22-pin-out.png" width=300>

## Combined visible and IR light sensor

This is powered by the Raspberry Pi. One example is a [SI1145 Digital UV Index / IR / Visible Light Sensor][1]. Your on your own to wire this.

[1]: https://www.adafruit.com/product/1777
[2]: https://www.adafruit.com/product/64?gclid=CjwKCAiA9f7QBRBpEiwApLGUijY03SkJ-mU-7PzpacD5HT3Y4dMM7gbnNP1328raTCGwOq8OPo4NjxoC67YQAvD_BwE
[3]: https://www.raspberrypi.org/documentation/hardware/camera/

