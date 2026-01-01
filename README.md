# Darkstar74
Darkstar74 - a retrostyle, vectorbased asteroids clone (written in python)

A game, created especially for the Pimoroni Presto with attached QwSTPad. The 7 LEDs mounted on the back are used to create an ambilight effect. The spaceship is steered with **left** & **right**. To fire, press the **A** button. To thrust, press the **X** button.

The design of the font, asteroids, ufo and spaceship is taken from the original game *Asteroids* (developed in 1979 by Lyle Rains and Ed Logg for Atari). See [https://computerarcheology.com/Arcade/Asteroids/DVG.html](https://computerarcheology.com/Arcade/Asteroids/DVG.html).

- [Required Hardware](#required-hardware)
- [Installation](#installation)
- [Pimoroni Presto](#pimoroni-presto)

## Required Hardware
* Pimoroni Presto
* QwSTPad (with id 0 - can be changed in darkstar74_presto_240.py)
```python
I2C_PINS      = {"id": 0, "sda": 40, "scl": 41} # The I2C pins the QwSTPad is connected to
I2C_ADDRESS   = ADDRESSES[0]                    # The I2C address of the connected QwSTPad
```
* Power (battery or AC adapter)

## Installation
1. Download the python file to your PC
2. Upload the file to your Pimoroni Presto (e.g., with [Thonny](https://thonny.org/)).
3. Start darkstar74_presto.py (e.g., with Thonny)
4. Play and enjoy!
5. To start Darkstar74 automaticaly - rename it to main.py


## Pimoroni Presto
The Pimoroni Presto is a RP2350-powered microcontroller board with a 4" square touchscreen (480x480px).
* [github Pimoroni Presto](https://github.com/pimoroni/presto)
* [shop Pimoroni Presto](https://shop.pimoroni.com/products/presto)
