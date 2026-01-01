# Darkstar74
# (c) Ralf Huwald 2023-2025
#
# Version für Pimoroni Presto (4" Display, 240x240 loRes Version)



from presto import Presto
from qwstpad import ADDRESSES, QwSTPad
from machine import freq,I2C
from math import cos, radians, sin, sqrt
from random import choice, randint, random
import sys
import time


# Auf Wunsch CPU-Takt erhöhen
# freq(264_000_000)

print('Programm          : Darkstar74 (4" Presto Version 240x240)\n')
print(f"Machine-Id        : {machine.unique_id()}")
print(f"Machine-Freq      : {machine.freq()/1000000} MHz")
print(f"sys.implementation: {sys.implementation}\n")

# Einige grundlegende Konstante
STARS                = const(150)     # 150, False = keine Sterne zeichnen
DEBUG                = const(False)   # False
AMBILIGHT            = const(True)    # True = Ambilight bei Explosion
ASTEROID_SPEED       = const(.1)      # 2
ASTEROID_SCALE_MULTI = const(.3)      # .5
LASER_TYPE_DOUBLE    = const(False)   # True = Double Laser, False = single Laser
LASER_MAX_COUNT      = const(4)       # 4 Max. Anzahl gleichzeitige Laser
LASER_LIFETIME       = const(35)      # 35
LASER_RAPID_FIRE     = const(True)    # False
LASER_COOLDOWN_MS    = const(50)      # 100ms to "cooldown" Laser -> max. 10 shot/sec
LASER_SPEED          = const(4)       # 4
SHIP_MAX_SPEED       = const(3)       # 3
SHIP_COUNT           = const(3)       # 3
SHIP_TURN            = const(6)       # 6
SHIP_BONUS           = const(15_000)  # 15000 Punkte für ein Bonus-Schiff
SHIP_ACCELERATION    = const(.1)      # .1
SHIP_DECELERATION    = const(.99)     # .99
UFO_SECONDS          = const(20)      # 20 Alle wieviel Sekunden soll ein Ufo auftauchen
UFO_SECONDS_RANDOM   = const(10)      # 10
UFO_SPEED            = const(2)       # 2
GOD_MODE             = const(False)   # GOD-Mode (Keine Kollisionen ermitteln)

SCALE_0       = const(0)
SCALE_1       = const(1)
SCALE_2       = const(2)

I2C_PINS      = {"id": 0, "sda": 40, "scl": 41} # The I2C pins the QwSTPad is connected to
I2C_ADDRESS   = ADDRESSES[0]                    # The I2C address of the connected QwSTPad

presto        = Presto(full_res=False, ambient_light=False, layers=2)
display       = presto.display

WIDTH, HEIGHT = display.get_bounds()
CENTER_X      = round(WIDTH//2)
CENTER_Y      = round(HEIGHT//2)


BLACK         = display.create_pen(0,     0,   0)
BLUE          = display.create_pen(0,     0, 160)
GREEN         = display.create_pen(0,   160,   0)
RED           = display.create_pen(160,   0,   0)
WHITE         = display.create_pen(160, 160, 160)


# Bestimmte Taste resetten (Alle oder KEY_LASER, KEY_THRUST, ...)
def reset_key(key = None):
    while True:
        buttons = qwstpad.read_buttons()
        if key == None:
            button_pressed = (buttons["U"] == True) or (buttons["D"] == True) or (buttons["L"] == True) or (buttons["R"] == True) or (buttons["A"] == True) or (buttons["B"] == True) or (buttons["X"] == True) or (buttons["Y"] == True) or (buttons["+"] == True) or (buttons["-"] == True)
            if button_pressed == False:
                break
        else:
            if buttons[key] == False:
                break
        time.sleep(.01)


# Die beliebte any_key Funktion
def press_any_key():
    reset_key()
    buttons = qwstpad.read_buttons()
    button_pressed = (buttons["U"] == True) or (buttons["D"] == True) or (buttons["L"] == True) or (buttons["R"] == True) or (buttons["A"] == True) or (buttons["B"] == True) or (buttons["X"] == True) or (buttons["Y"] == True) or (buttons["+"] == True) or (buttons["-"] == True)
    while button_pressed == False:
        time.sleep(.01)
        buttons = qwstpad.read_buttons()
        button_pressed = (buttons["U"] == True) or (buttons["D"] == True) or (buttons["L"] == True) or (buttons["R"] == True) or (buttons["A"] == True) or (buttons["B"] == True) or (buttons["X"] == True) or (buttons["Y"] == True) or (buttons["+"] == True) or (buttons["-"] == True)
    reset_key()


# Auf eine bestimmte Taste (U, D, L, R, A, B, X, Y, + oder -) warten
def press_key(key):
    reset_key(key)
    buttons = qwstpad.read_buttons()
    while buttons[key] == False:
        time.sleep(.01)
        buttons = qwstpad.read_buttons()
    reset_key(key)


# Auf eine beliebige Taste max <timeout> Millisekunden warten
# Eine Taste gedrückt : True
# Keine Taste gedrückt: False
def wait_for_any_key(timeout = 3_000):
    # reset_key()
    for i in range(0,int(timeout/10)):
        buttons = qwstpad.read_buttons()
        button_pressed = (buttons["U"] == True) or (buttons["D"] == True) or (buttons["L"] == True) or (buttons["R"] == True) or (buttons["A"] == True) or (buttons["B"] == True) or (buttons["X"] == True) or (buttons["Y"] == True) or (buttons["+"] == True) or (buttons["-"] == True)
        if button_pressed == True:
            # reset_key()
            return True
        else:
            time.sleep(.01)
    return False


# Auf eine beliebige oder bestimmte warten
# Eine Taste gedrückt : Taste wird zurückgegeben
def wait_for_key(key = None, timeout = 3_000):
    reset_key()
    for i in range(0,int(timeout/10)):
        buttons = qwstpad.read_buttons()
        for _ in ("U","D","L","R","A","B","X","Y","+","-"):
            if key is None and buttons[_] == True:
                return _
            if key is not None and buttons[key] == True:
                return key
            time.sleep(.01)


class DVG():
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        
        self.cursor_x = 0
        self.cursor_y = 0
        
        # Global Scale der Vectoren (wird auf den Scale der Vector-Daten addiert)
        # 0 = /512 / *2
        # 1 = /256 / *4
        # 2 = /128 / *8
        # 3 = /64  / * 16
        # 4 = /32  / * 32
        # 5 = /16  / * 64
        # 6 = /8   / * 128
        # 7 = /4   / * 256
        # 8 = /2   / * 512
        # 9 = /1   / * 1024
        self.scale = 1
        
        # Sinus- und Cosinus-Tabelle für 0 - 359 Grad anlegen
        self.cossin = {}
        for winkel in range(0, 360):
            theta = radians(winkel)
            self.cossin[winkel] = (cos(theta), sin(theta))
        
        # Objekte (Buchstaben, Zahlen, Rocks & Co. anlegen
        self.objects = {}
        # Blank
        self.add_object(" ",     [ (1, 0, 3,  0) ] )
        # A - Z
        self.add_object("A",     [ (1, 7, 0, -2), (1, 7,  1, -1), (1, 7,  1,  1), (1, 7,  0,  2), (1, 0, -2, -1), (1, 7,  2,  0), (1, 0,  1,  1) ] )
        self.add_object("B",     [ (1, 7, 0, -3), (0, 7,  3,  0), (0, 7,  1,  1), (0, 7,  0,  1), (0, 7, -1,  1), (0, 7, -3,  0), (0, 0,  3,  0), (0, 7,  1,  1), (0, 7,  0,  1), (0, 7, -1,  1), (0, 7, -3, 0), (1, 0, 3, 0) ] )
        self.add_object("C",     [ (1, 7, 0, -3), (1, 7,  2,  0), (1, 0, -2,  3), (1, 7,  2,  0), (1, 0,  1,  0) ] )
        self.add_object("D",     [ (1, 7, 0, -3), (1, 7,  1,  0), (1, 7,  1,  1), (1, 7,  0,  1), (1, 7, -1,  1), (1, 7, -1,  0), (1, 0,  3,  0) ] )
        self.add_object("E",     [ (1, 7, 0, -3), (1, 7,  2,  0), (0, 0, -1,  3), (0, 7, -3,  0), (0, 0,  0,  3), (1, 7,  2,  0), (1, 0,  1,  0) ] )
        self.add_object("F",     [ (1, 7, 0, -3), (1, 7,  2,  0), (0, 0, -1,  3), (0, 7, -3,  0), (0, 0,  0,  3), (1, 0,  3,  0) ] )
        self.add_object("G",     [ (1, 7, 0, -3), (1, 7,  2,  0), (1, 7,  0,  1), (1, 0, -1,  1), (1, 7,  1,  0), (1, 7,  0,  1), (1, 7, -2,  0), (1, 0,  3,  0) ] )
        self.add_object("H",     [ (1, 7, 0, -3), (0, 0,  0,  3), (1, 7,  2,  0), (0, 0,  0, -3), (1, 7,  0,  3), (1, 0,  1,  0) ] )
        self.add_object("I",     [ (1, 7, 2,  0), (1, 0, -1,  0), (1, 7,  0, -3), (1, 0,  1,  0), (1, 7, -2,  0), (1, 0,  3,  3) ] )
        self.add_object("J",     [ (1, 0, 0, -1), (1, 7,  1,  1), (1, 7,  1,  0), (1, 7,  0, -3), (1, 0,  1,  3) ] )
        self.add_object("K",     [ (1, 7, 0, -3), (0, 0,  3,  0), (0, 7, -3,  3), (0, 7,  3,  3), (0, 0,  3,  0) ] )
        self.add_object("L",     [ (1, 0, 0, -3), (1, 7,  0,  3), (1, 7,  2,  0), (1, 0,  1,  0) ] )
        self.add_object("M",     [ (1, 7, 0, -3), (1, 7,  1,  1), (1, 7,  1, -1), (1, 7,  0,  3), (1, 0,  1,  0) ] )
        self.add_object("N",     [ (1, 7, 0, -3), (1, 7,  2,  3), (1, 7,  0, -3), (1, 0,  1,  3) ] )
        self.add_object("O",     [ (1, 7, 0, -3), (1, 7,  2,  0), (1, 7,  0,  3), (1, 7, -2,  0), (1, 0,  3,  0) ] )
        self.add_object("P",     [ (1, 7, 0, -3), (1, 7,  2,  0), (0, 7,  0,  3), (1, 7, -2,  0), (0, 0,  3,  3), (0, 0,  3,  0) ] )
        self.add_object("Q",     [ (1, 7, 0, -3), (1, 7,  2,  0), (1, 7,  0,  2), (1, 7, -1,  1), (1, 7, -1,  0), (1, 0,  1, -1), (1, 7,  1,  1), (1, 0,  1,  0) ] )
        self.add_object("R",     [ (1, 7, 0, -3), (1, 7,  2,  0), (0, 7,  0,  3), (1, 7, -2,  0), (0, 0,  1,  0), (0, 7,  3,  3), (1, 0,  1,  0) ] )
        self.add_object("S",     [ (1, 7, 2,  0), (0, 7,  0, -3), (1, 7, -2,  0), (0, 7,  0, -3), (1, 7,  2,  0), (1, 0,  1,  3) ] )
        self.add_object("T",     [ (1, 0, 1,  0), (1, 7,  0, -3), (1, 0, -1,  0), (1, 7,  2,  0), (1, 0,  1,  3) ] )
        self.add_object("U",     [ (1, 0, 0, -3), (1, 7,  0,  3), (1, 7,  2,  0), (1, 7,  0, -3), (1, 0,  1,  3) ] )
        self.add_object("V",     [ (1, 0, 0, -3), (1, 7,  1,  3), (1, 7,  1, -3), (1, 0,  1,  3) ] )
        self.add_object("W",     [ (1, 0, 0, -3), (1, 7,  0,  3), (1, 7,  1, -1), (1, 7,  1,  1), (1, 7,  0, -3), (1, 0,  1,  3) ] )
        self.add_object("X",     [ (1, 7, 2, -3), (1, 0, -2,  0), (1, 7,  2,  3), (1, 0,  1,  0) ] )
        self.add_object("Y",     [ (1, 0, 1,  0), (1, 7,  0, -2), (1, 7, -1, -1), (1, 0,  2,  0), (1, 7, -1,  1), (1, 0,  2,  2) ] )
        self.add_object("Z",     [ (1, 0, 0, -3), (1, 7,  2,  0), (1, 7, -2,  3), (1, 7,  2,  0), (1, 0,  1,  0) ] )
        # 0 - 9
        self.add_object("0",     [ (1, 7, 0, -3), (1, 7,  2,  0), (1, 7,  0,  3), (1, 7, -2,  0), (1, 0,  3,  0) ] )
        self.add_object("1",     [ (1, 0, 1,  0), (1, 7,  0, -3), (1, 0,  2,  3) ] )
        self.add_object("2",     [ (1, 0, 0, -3), (1, 7,  2,  0), (0, 7,  0,  3), (1, 7, -2,  0), (0, 7,  0,  3), (1, 7,  2,  0), (1, 0,  1,  0) ] )
        self.add_object("3",     [ (1, 7, 2,  0), (1, 7,  0, -3), (1, 7, -2,  0), (0, 0,  0,  3), (1, 7,  2,  0), (0, 0,  2,  3) ] )
        self.add_object("4",     [ (1, 0, 0, -3), (0, 7,  0,  3), (1, 7,  2,  0), (0, 0,  0, -3), (1, 7,  0,  3), (1, 0,  1,  0) ] )
        self.add_object("5",     [ (1, 7, 2,  0), (0, 7,  0, -3), (1, 7, -2,  0), (0, 7,  0, -3), (1, 7,  2,  0), (1, 0,  1,  3) ] )
        self.add_object("6",     [ (0, 0, 0, -3), (1, 7,  2,  0), (0, 7,  0,  3), (1, 7, -2,  0), (1, 7,  0, -3), (1, 0,  3,  3) ] )
        self.add_object("7",     [ (1, 0, 0, -3), (1, 7,  2,  0), (1, 7,  0,  3), (1, 0,  1,  0) ] )
        self.add_object("8",     [ (1, 7, 2,  0), (1, 7,  0, -3), (1, 7, -2,  0), (1, 7,  0,  3), (0, 0,  0, -3), (1, 7,  2,  0), (0, 0,  2,  3) ] )
        self.add_object("9",     [ (1, 0, 2,  0), (1, 7,  0, -3), (1, 7, -2,  0), (0, 7,  0,  3), (1, 7,  2,  0), (0, 0,  2,  3) ] )
        # Rocks & Co.
        self.add_object("rock1", [ (3, 0, 0, -1), (3, 7,  1, -1), (3, 7,  1,  1), (2, 7, -1,  2), (2, 7,  1,  2), (2, 8, -3,  2), (2, 8, -3,  0), (3, 7, -1, -1), (3, 7,  0, -2), (3, 7,  1, -1), (3, 7,  1, 1), (3, 0,  0,  1) ] )
        self.add_object("rock2", [ (2, 0, 2, -1), (2, 7,  2, -1), (3, 7, -1, -1), (2, 7, -2,  1), (2, 7, -2, -1), (3, 7, -1,  1), (2, 7,  1,  2), (2, 7, -1,  2), (3, 7,  1,  1), (2, 7,  1, -1), (2, 8,  3, 1), (2, 8,  2, -3), (3, 7, -1, -1), (2, 0, -2, 1) ] )
        self.add_object("rock3", [ (3, 0, -1, 0), (2, 7, -2,  1), (2, 7,  2,  3), (2, 7,  2, -3), (2, 7,  0,  3), (3, 7,  1,  0), (2, 7,  2, -3), (3, 7,  0, -1), (2, 7, -2, -3), (2, 7, -3,  0), (2, 7, -3, 3), (2, 7,  2,  1), (2, 0,  2,  0) ] )
        self.add_object("rock4", [ (2, 0,  1, 0), (2, 7,  3, -1), (2, 6,  0, -1), (2, 7, -3, -2), (2, 7, -3,  0), (2, 6,  1,  2), (2, 7, -3,  0), (2, 7,  0,  3), (2, 7,  2,  3), (2, 7,  3, -1), (2, 6,  1, 1), (3, 6,  1, -1), (2, 7, -3, -2), (2, 0, -1, 0) ] )
        self.add_object("ufo",   [ (1, 0, -4,-2), (1,12,  8,  0), (1, 0,  6,  4), (1,13,-20,  0), (1,13,  6,  4), (1,12,  8,  0), (1,13,  6, -4), (1,13, -6, -4), (1,12, -2, -4), (1, 12, -4, 0), (1,12, -2, 4), (1,13, -6,  4), (1, 0, 10, -2) ] )
        self.add_object("ship",  [ (2, 0,  0,-4), (2,10, -3,  8), (2,10,  1, -1), (2,10,  4,  0), (2,10,  1,  1), (2,10, -3, -8), (2, 0,  0,  4) ] )
        self.add_object("ship_thrust", [
                                   (2,  0,  0, -4), (2,  9, -3,  8), (2,  9,  1, -1), (2,  9,  4,  0), (2,  0, -4,  0), (2, -1,  2,  4), (2, -1,  2, -4), (2, -1,  1,  1), (2,  9, -3, -8), (2,  0,  0,  4) ] )
        self.add_object("explosion", [
                                   (3, 0, -1, 0), (3, 7,  0,  0), (3, 0, -1, -1), (3, 7,  0,  0), (3, 0,  1, -1), (3, 7,  0,  0), (2, 0,  3,  1), (3, 7,  0,  0), (2, 0,  2, -1), (3,  7,  0, 0), (3, 0,  0, 1), (3, 7,  0,  0), (2, 0,  1,  3), (3, 7, 0, 0), (2, 0, -1, 3), (3, 7, 0, 0), (5, 0, -512, -128), (3, 7, 0, 0), (2, 0, -3, 1), (3, 7, 0, 0) ] )
        
        # die 15 Helligkeitsstufen für die Vectoren
        self.colors = {}
        for bri in range(0,16):
            # bri_rgb = 128 + bri * 8
            bri_rgb = bri * 16
            color = display.create_pen(bri_rgb, bri_rgb, bri_rgb)
            self.colors[bri] = color
        
        # Erstmal sind keine Asteroiden angelegt
        self.asteroids = {}
        self.asteroids_counter = 0
        
        # Erstmal sind keine Laser unterwegs
        self.laser = {}
        self.laser_counter = 0
        
        # Sterne anlegen (unterschiedlich hell)
        self.stars = {}
        if STARS > 0:
            for _ in range(0, STARS):
                x             = randint(0, WIDTH - 1)
                y             = randint(16, HEIGHT - 1)
                color         = randint(1, 15)
                self.stars[_] = (x, y, color)
    
    
    def color(self,R,G,B):
        return (R, G, B)
    
    
    # Fügt die Daten eines Vector-Objekts zur Liste objects hinzu.
    # array_data ist eine Liste, die tupel mit folgendem Inhalt enthält:
    # - (Typ, [scale = 1], [bri = 7], x, y)
    #   siehe https://computerarcheology.com/Arcade/Asteroids/DVG.html
    def add_object(self, name, array_data):
        self.objects[name] = array_data
    
    
    def draw_asteroids(self):
        for i in self.asteroids.copy():
            if self.asteroids[i].collision == True and self.asteroids[i].collision_counter >= 30:
                del self.asteroids[i]
            else:
                self.asteroids[i].draw(self)
    
    
    def draw_laser(self):
        for i in self.laser:
            self.laser[i].draw(self)
    
    
    # Zeichnet ein Vector-Objekt an der Position cursor_x / cursor_y in der
    # angegebenen Grösse
    def draw_object(self, name, scale, magnifier= 0, degrees = 0, color = None, color_endpoint = None, manuel_vector_bri = None):
        x               = self.cursor_x
        y               = self.cursor_y
        degrees_rounded = round(degrees) % 360
        cosang, sinang  = self.cossin[degrees_rounded]
        
        if name in self.objects:
            object = self.objects[name]
        else:
            object = self.objects[" "]
        
        for vector in object:
            vector_scale, vector_bri, vector_x, vector_y = vector
            
            if scale + vector_scale == 0:
                multi = 1
            else:
                if scale + vector_scale < 0:
                    multi = round(512 / (512 << ((scale + vector_scale) * -1)), 2)
                else:
                    multi = round(512 / (512 >> (scale + vector_scale)), 2)
                vector_x = vector_x * multi
                vector_y = vector_y * multi
            
            if magnifier != 0:
                vector_x = vector_x + vector_x * magnifier
                vector_y = vector_y + vector_y * magnifier
            
            vector_x = round(vector_x, 0)
            vector_y = round(vector_y, 0)
            
            if degrees_rounded == 0:
                x1 = x + vector_x
                y1 = y + vector_y
            else:
                x_degrees = -1 * round(vector_x * -cosang + vector_y * sinang, 2)
                y_degrees = -1 * round(-vector_x * sinang + vector_y * -cosang, 2)
                x1 = x + x_degrees
                y1 = y + y_degrees
            
            if manuel_vector_bri != None:
                vector_bri = manuel_vector_bri
            
            if vector_bri != 0:
                if vector_bri == -1:
                    ccc = RED if color == None else color
                else:
                    ccc = self.colors[vector_bri] if color == None else color
                display.set_pen(ccc)
                
                if y == y1:
                    if x == x1:
                        display.pixel(round(x), round(y))
                    elif x1 > x:
                        display.pixel_span(round(x), round(y), round(x1 - x))
                    else:
                        display.pixel_span(round(x1), round(y), round(x - x1))
                else:
                    display.line(round(x), round(y), round(x1), round(y1))
                
                # display.line zeichnet in Firmware 1.0.0 1 Pixel zu wenig, daher die pixel Aufrufe
                if color_endpoint != None:
                    display.set_pen(color_endpoint)
                display.pixel(round(x), round(y))
                display.pixel(round(x1), round(y1))
            
            x = x1
            y = y1
        
        self.cursor_x = x
        self.cursor_y = y
    
    
    # Sterne, Score und/oder Ships zeichnen
    def draw_background(self, draw_stars = True, draw_score = True, draw_ships = True, update = False):
        display.set_layer(0)
        if draw_stars == True:
            display.set_pen(BLACK)
            display.clear()
            for _ in self.stars:
                x, y, color = self.stars[_]
                display.set_pen(self.colors[color])
                display.pixel(x, y)
        
        if draw_score == True:
            if draw_stars == False:
                display.set_pen(BLACK)
                display.rectangle(0, 0, 4 * 12 + 9, 18)
                display.rectangle(WIDTH - (4 * 12 + 10), 0, 4 * 12 + 9, 18)
            dvg.set_cursor(0, 14)
            dvg.draw_text(str(score), SCALE_1, dvg.colors[10])
            
            dvg.set_cursor(WIDTH - (4 * 12) - 10, 14)
            dvg.draw_text("{score:5d}".format(score = highscores[1]["score"]), SCALE_1, dvg.colors[10])
        
        if draw_ships == True:
            if draw_stars == False:
                display.set_pen(BLACK)
                display.rectangle(74, 0, 7 * 12, 18)
            x = 80
            for i in range(1,ship.count): #          Die verbleibenden Schiffe zeichnen
                dvg.set_cursor(x, 9)
                dvg.draw_object("ship", -1, 0, 0, dvg.colors[10], None)
                x += 12
        
        display.set_layer(1)
        
        if update == True:
            presto.update()
    
    
    # Errechnet die Länge eines Textes in Pixeln (Vector-Schrift)
    def get_text_len(self, text, scale):
        x_merk = self.cursor_x
        y_merk = self.cursor_y
        self.cursor_x = 0
        self.cursor_Y = 0
        
        for zeichen in text:
            self.draw_object(zeichen.upper(), scale, 0, 0, None, None, 0)
        
        text_len = self.cursor_x
        
        self.cursor_x = x_merk
        self.cursor_y = y_merk
        
        return text_len
    
    
    
    # Zeichnet einen Text an der Position cursor_x / cursor_y in der angegebenen Grösse
    def draw_text(self, text, scale, color = None, color_endpoint = None):
        for zeichen in text:
            self.draw_object(zeichen.upper(), scale, 0, 0, color, color_endpoint, None)
    
    
    def move_asteroids(self, recreate = False):
        for i in self.asteroids:
            self.asteroids[i].move(recreate)
    
    
    def move_laser(self):
        for i in self.laser:
            self.laser[i].move()
    
    
    def set_cursor(self, x, y):
        self.cursor_x = int(x)
        self.cursor_y = int(y)


class ASTEROID():
    def __init__(self, scale = None, speed = None, level = None, winkel = None):
        self.object   = choice(["rock1","rock2","rock3","rock4"])
        if scale == None:
            self.scale= choice([-2, -1, 0])
        else:
            self.scale= scale
        if self.scale == -2:
            self.diameter = 5
        elif self.scale == -1:
            self.diameter = 10
        else:
            self.diameter = 20
        if speed == None:
            if level == None:
                self.speed = round(ASTEROID_SPEED + ASTEROID_SCALE_MULTI * (2 - self.scale), 1)
            else:
                self.speed = round(ASTEROID_SPEED + (level / 3) + ASTEROID_SCALE_MULTI * (2 - self.scale), 1)
        else:
            self.speed = speed
        
        self.rotation = choice((-4, -2, 2, 4))
        
        self.grad     = randint(0,359)
        
        self.winkel   = randint(10,349) if winkel == None else winkel
        while self.winkel in (0, 90, 180, 270):
            self.winkel = randint(10,349)
        
        self.x = choice([0, 1, 2])
        if self.x == 0:
            self.x = 0 - self.diameter
        elif self.x == 1:
            self.x = randint(0 + self.diameter, WIDTH - self.diameter)
        else:
            self.x = WIDTH + self.diameter
        if self.x < 0 or self.x > WIDTH:
            self.y = randint(0 + self.diameter, HEIGHT - self.diameter)
        else:
            if self.winkel < 90 or self.winkel > 270:
                self.y = 0 - self.diameter
            else:
                self.y = HEIGHT + self.diameter
        self.collision = False
        self.collision_counter = 0
    
    
    # Asteroid zeichnen
    def draw(self, dvg):
        if DEBUG == True:
            dvg.set_cursor(round(self.x), round(self.y))
            dvg.draw_text(f"{int(self.winkel)}", 0, RED, None)
            dvg.set_cursor(round(self.x), round(self.y + 8))
            dvg.draw_text(f"{int(self.grad)}", 0, BLUE, None)
        dvg.set_cursor(round(self.x), round(self.y))
        if self.collision == True:
            self.collision_counter += 1
            if self.collision_counter < 30:
                dvg.draw_object("explosion", self.scale, self.collision_counter * .1, self.grad, None, dvg.colors[int(15 - (self.collision_counter/2))], None)
        else:
            dvg.draw_object(self.object, self.scale, 0, self.grad, None, None)
    
    
    # Asteroid bewegen
    def move(self, recreate = False):
        self.grad += self.rotation
        self.grad = self.grad % 360
        self.winkel = self.winkel % 360
        cosang, sinang = dvg.cossin[self.winkel]
        
        add_x = round(self.speed * sinang, 2)
        add_y = round(self.speed * -cosang, 2)
        
        self.x += add_x
        self.y += add_y
        
        if self.x >= WIDTH + self.diameter and add_x > 0:
            if recreate == True:
                self.__init__()
            else:
                self.x  = 0 - self.diameter
        elif self.x <= 0 - self.diameter and add_x < 0:
            if recreate == True:
                self.__init__()
            else:
                self.x = WIDTH + self.diameter
        if self.y >= HEIGHT + self.diameter and add_y > 0:
            if recreate == True:
                self.__init__()
            else:
                self.y = 0 - self.diameter
        elif self.y <= 0 - self.diameter and add_y < 0:
            if recreate == True:
                self.__init__()
            else:
                self.y = HEIGHT + self.diameter


class LASER():
    def __init__(self, x = 0, y = 0, speed_x = 0, speed_y = 0, winkel = 0, laser_left = True):
        cosang, sinang = dvg.cossin[winkel]
        
        if LASER_TYPE_DOUBLE == False:
            # Laser front
            add_x       = round(10 * sinang, 2)
            add_y       = round(10 * -cosang, 2)
            self.winkel = winkel
        else:
            if laser_left == True:
                # Laser left wing
                add_x       = round(8 * -cosang, 2)
                add_y       = round(8 * -sinang, 2)
                self.winkel = (winkel + 3) % 360
            else:
                # Laser right wing
                add_x       = round(8 * cosang, 2)
                add_y       = round(8 * sinang, 2)
                self.winkel = (winkel - 3) % 360
        
        self.speed    = LASER_SPEED
        if speed_x or speed_y:
            self.speed += sqrt(speed_x ** 2 + speed_y ** 2)
        self.x        = x + add_x
        self.y        = y + add_y
        self.lifetime = LASER_LIFETIME
    
    
    # Laser zeichnen
    def draw(self, dvg):
        display.set_pen(dvg.colors[15])
        display.pixel(round(self.x), round(self.y))
    
    
    # Laser bewegen
    def move(self):
        self.lifetime -= 1
        cosang, sinang = dvg.cossin[self.winkel]
        
        add_x = round(self.speed * sinang, 2)
        add_y = round(self.speed * -cosang, 2)
        
        self.x += add_x
        self.y += add_y
        
        if self.x >= WIDTH - 1  and add_x > 0:
            self.x  = 0
        elif self.x <= 0 and add_x < 0:
            self.x = WIDTH - 1
        if self.y >= HEIGHT - 1 and add_y > 0:
            self.y = 0
        elif self.y <= 0 and add_y < 0:
            self.y = HEIGHT - 1


class SHIP():
    def __init__(self):
        self.thrust            = False #      Kein Antrieb
        self.grad              = 0 #          Richtung, in die das Schiff ausgerichtet ist
        self.x                 = WIDTH / 2 #  Aktuelle X-Position des Schiffes
        self.y                 = HEIGHT / 2 # Aktuelle Y-Position des Schiffes
        self.speed_x           = 0. #         X-Geschwindigkeit des Schiffes
        self.speed_y           = 0. #         Y-Geschwindigkeit des Schiffes
        self.diameter          = 6 #          Durchmesser des Schiffes
        self.collision         = False #      Ist das Schiff kollidiert?
        self.collision_counter = 0 #          Counter für Kollisionen (bzw. die Animation)
        self.count             = SHIP_COUNT # Anzahl Schiffe (inkl. dem aktiven Schiff)
        self.reset_me          = False

    
    # Ist das Schiff mit einem Asteroiden oder Ufo kollidiert?
    def collision_detected(self, dvg, ufo = False):
        
        collision_detected = False
        
        if GOD_MODE == True:
            return collision_detected
        
        for i in dvg.asteroids:
            asteroid = dvg.asteroids[i]
            if asteroid.collision == False:
                a = abs(abs(self.x) - abs(asteroid.x))
                b = abs(abs(self.y) - abs(asteroid.y))
                c = sqrt(a**2 + b**2)
                # + 4 für das eigene Schiff (verbesserungswürdig)
                if c <= (asteroid.diameter + 4):
                    collision_detected = True
        if collision_detected == True:
            return collision_detected
        
        if ufo == False:
            return collision_detected
        
        if ufo.collision == False:
            a = abs(abs(self.x) - abs(ufo.x))
            b = abs(abs(self.y) - abs(ufo.y))
            c = sqrt(a**2 + b**2)
            # + 4 für das eigene Schiff (verbesserungswürdig)
            if c <= (ufo.diameter + 8):
                collision_detected = True
        
        return collision_detected
    
    
    # Schiff zeichnen
    def draw(self, dvg):
        color = None
        color_endpoint = dvg.colors[15]
        
        dvg.set_cursor(round(self.x), round(self.y))
        if self.collision == True:
            dvg.draw_object("explosion", -1, self.collision_counter * .1, self.grad, dvg.colors[int(15 - (self.collision_counter/4))], None)
        else:
            if self.thrust == True:
                dvg.draw_object("ship_thrust", -1, 0, self.grad, None, None)
            else:
                dvg.draw_object("ship", -1, 0, self.grad, None, None)
    
    
    # Schiff resetten (nach Kollision)
    def reset(self):
        self.thrust    = False #      Kein Antrieb
        self.grad      = 0 #          Richtung, in die das Schiff ausgerichtet ist
        self.x         = WIDTH / 2 #  Aktuelle X-Position des Schiffes
        self.y         = HEIGHT / 2 # Aktuelle Y-Position des Schiffes
        self.speed_x   = 0 #          X-Geschwindigkeit des Schiffes
        self.speed_y   = 0 #          Y-Geschwindigkeit des Schiffes
        self.collision = False #      Ist das Schiff kollidiert?
        self.collision_counter = 0 #  Counter für Kollisionen (bzw. die Animation)
        self.reset_me  = False
    
    
    # Schiff Thrust an
    def thrust_on(self):
        cosang, sinang = dvg.cossin[self.grad]
        
        self.speed_x = round(self.speed_x + SHIP_ACCELERATION * sinang, 2)
        self.speed_y = round(self.speed_y - SHIP_ACCELERATION * cosang, 2)
        self.thrust = True
        if self.speed_x < -SHIP_MAX_SPEED:
            self.speed_x = -SHIP_MAX_SPEED
        elif self.speed_x > SHIP_MAX_SPEED:
            self.speed_x = SHIP_MAX_SPEED
        if self.speed_y < -SHIP_MAX_SPEED:
            self.speed_y = -SHIP_MAX_SPEED
        elif self.speed_y > SHIP_MAX_SPEED:
            self.speed_y = SHIP_MAX_SPEED
    
    
    # Schiff Thrust aus
    def thrust_off(self):
        self.thrust = False
    
    
    # Schiff links drehen
    def turn_left(self):
        self.grad -= SHIP_TURN
        self.grad = self.grad % 360
    
    
    # Schiff rechts drehen
    def turn_right(self):
        self.grad += SHIP_TURN
        self.grad = self.grad % 360
    
    
    # Schiff bewegen
    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        if self.x > WIDTH - 1 + self.diameter:
            self.x = 0 - self.diameter
        if self.x < 0 - self.diameter:
            self.x = WIDTH - 1 + self.diameter
        if self.y > HEIGHT - 1 + self.diameter:
            self.y = 0 - self.diameter
        if self.y < 0 - self.diameter:
            self.y =HEIGHT - 1 + self.diameter


class UFO():
    def __init__(self, scale = None, speed = None, level = None):
        if scale == None:
            self.scale= -1
        else:
            self.scale= scale
        if self.scale == -1:
            self.diameter = 8
        elif self.scale == -2:
            self.diameter = 4
        if speed == None:
            self.speed = UFO_SPEED
        else:
            self.speed = speed
        self.rotation = 0
        self.grad     = 0
        self.winkel   = randint(10,349)
        while self.winkel in (0, 90, 180, 270):
            self.winkel = randint(10,349)
        self.x = choice([0,1,2])
        if self.x == 0:
            self.x = 0 - self.diameter
        elif self.x == 1:
            self.x = randint(0 + self.diameter, WIDTH - self.diameter)
        else:
            self.x = WIDTH + self.diameter
        if self.x < 0 or self.x > WIDTH:
            self.y = randint(0 + self.diameter, HEIGHT - self.diameter)
        else:
            if self.winkel < 90 or self.winkel > 270:
                self.y = 0 - self.diameter
            else:
                self.y = HEIGHT + self.diameter
        self.collision = False
        self.collision_counter = 0
    
    
    # Ufo zeichnen
    def draw(self, dvg):
        dvg.set_cursor(round(self.x), round(self.y))
        if self.collision == True:
            self.collision_counter += 1
            if self.collision_counter < 30:
                dvg.draw_object("explosion", self.scale, self.collision_counter * .1, self.grad, dvg.colors[int(15 - (self.collision_counter/2))], None)
        else:
            if DEBUG == True:
                display.set_pen(GREEN)
                display.pixel(round(self.x), round(self.y))
            dvg.draw_object("ufo", self.scale, 0, self.grad, None, None)
    
    
    # Ufo bewegen
    def move(self, recreate = False):
        self.grad += self.rotation
        self.grad = self.grad % 360
        self.winkel = self.winkel % 360
        cosang, sinang = dvg.cossin[self.winkel]
        
        add_x = round(self.speed * sinang, 2)
        add_y = round(self.speed * -cosang, 2)
        
        self.x += add_x
        self.y += add_y
        
        if self.x >= WIDTH + self.diameter and add_x > 0:
            if recreate == True:
                self.__init__()
            else:
                self.x  = 0 - self.diameter
        elif self.x <= 0 - self.diameter and add_x < 0:
            if recreate == True:
                self.__init__()
            else:
                self.x = WIDTH + self.diameter
        if self.y >= HEIGHT + self.diameter and add_y > 0:
            if recreate == True:
                self.__init__()
            else:
                self.y = 0 - self.diameter
        elif self.y <= 0 - self.diameter and add_y < 0:
            if recreate == True:
                self.__init__()
            else:
                self.y = HEIGHT + self.diameter
        if self.collision == False:
            if random() <= .03:
                self.winkel += choice((-60, -30, 30, 60))
                while self.winkel in (0, 90, 180, 270):
                    self.winkel += choice((-30, 30))


def init_ambilight(draw = False):
    if AMBILIGHT == True:
        for led_number in range(0,7):
            leds[led_number][2] = 0
        
        if draw == True:
            draw_ambilight()


def dec_ambilight(draw = False):
    if AMBILIGHT == True:
        for led_number in range(0,7):
            led_brightness = leds[led_number][2]
            led_brightness = max(led_brightness - 10, 0)
            leds[led_number][2] = led_brightness
        
        if draw == True:
            draw_ambilight()


def draw_ambilight():
    if AMBILIGHT == True:
        for led_number in range(0,7):
            led_brightness = leds[led_number][2]
            presto.set_led_rgb(led_number, led_brightness, led_brightness, led_brightness)


def check_ambilight(x, y, draw = False):
    if AMBILIGHT == True:
        for led_number in range(0, 7):
            led_x, led_y, led_brightness = leds[led_number]
            
            dist_x = abs(abs(x) - abs(led_x))
            dist_y = abs(abs(y) - abs(led_y))
            dist   = round(sqrt(dist_x**2 + dist_y**2))
            
            if dist <= 200:
                brightness = (200 - dist)
            else:
                brightness = 0
            
            if led_brightness < brightness:
                led_brightness = brightness
                leds[led_number][2] = led_brightness
        
        if draw == True:
            draw_ambilight()


def read_highscores():
    highscores = {}
    try:
        file = open("darkstar74_presto_240.hi", "r")
        for i in (1,2,3,4,5,6,7,8,9):
            satz = file.readline()
            highscores[i] = { "name": satz.split(".")[0], "score": int(satz.split(".")[1]) }
        file.close()
    except:
        highscores = {}
        highscores[1] = { "name": "LYLE RAINS", "score": 9_000 }
        highscores[2] = { "name": "ED LOGG",    "score": 8_000 }
        highscores[3] = { "name": "DOOLITTLE",  "score": 7_000 }
        highscores[4] = { "name": "BOILER",     "score": 6_000 }
        highscores[5] = { "name": "TALBY",      "score": 5_000 }
        highscores[6] = { "name": "PINBACK",    "score": 4_000 }
        highscores[7] = { "name": "POWELL",     "score": 3_000 }
        highscores[8] = { "name": "COMPUTER",   "score": 2_000 }
        highscores[9] = { "name": "BOMB 20",    "score": 1_000 }
        write_highscores(highscores)
    
    return highscores


def write_highscores(highscores):
    file = open("darkstar74_presto_240.hi", "w")
    for i in (1,2,3,4,5,6,7,8,9):
        highscore = highscores[i]
        file.write(highscore["name"] + "." + str(highscore["score"]) + "\n")
    file.close()


# Startbildschirm / Intro anzeigen
def show_title():
    dvg.draw_background(True, False, False, False)
    
    display.set_pen(BLACK)
    display.clear()
    
    # 3 Asteroiden für den Titel definieren
    dvg.asteroids.clear()
    dvg.asteroids_counter = 0
    dummy = ASTEROID(0,  0)
    dummy.x = 62
    dummy.y = 118
    dummy.rotation = 4 # choice((-4, -2, 2, 4))
    dvg.asteroids_counter += 1
    dvg.asteroids[dvg.asteroids_counter]  = dummy
    dummy = ASTEROID(-1,  0)
    dummy.x = 120
    dummy.y = 118
    dummy.rotation = 4 # choice((-4, -2, 2, 4))
    dvg.asteroids_counter += 1
    dvg.asteroids[dvg.asteroids_counter]  = dummy
    dummy = ASTEROID(-2,  0)
    dummy.x = 174
    dummy.y = 118
    dummy.rotation = 4 # choice((-4, -2, 2, 4))
    dvg.asteroids_counter += 1
    dvg.asteroids[dvg.asteroids_counter]  = dummy
    
    title_012 = 0 #                                0 = Score Table, 1 = Steering, 2 = Highscores
    
    running = True
    
    text_len = dvg.get_text_len("DARKSTAR74", SCALE_2)
    
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), 24)
    dvg.draw_text("DARKSTAR", SCALE_2, dvg.colors[12], None)
    dvg.draw_text("74", SCALE_2, RED, None)
    
    text_len = dvg.get_text_len("PRESS ANY KEY TO START", SCALE_0)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), HEIGHT - 16)
    dvg.draw_text("PRESS ANY KEY TO START", SCALE_0, dvg.colors[9], None)
    
    text_len = dvg.get_text_len("RELEASED IN MMCCL BY RALLO", SCALE_0)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), HEIGHT - 4)
    dvg.draw_text("RELEASED IN MMCCL BY ",SCALE_0,dvg.colors[6], None)
    dvg.draw_text("RALLO", SCALE_0, RED, None)
    
    while running:
        
        if title_012 == 0:
            
            display.set_pen(BLACK)
            display.rectangle(0, 32, WIDTH, HEIGHT - 56)
            
            ticks_start = time.ticks_ms()
            ticks_end   = ticks_start + 10_000
            
            while (time.ticks_ms() < ticks_end) and (running == True):
                text_len = dvg.get_text_len("SCORE TABLE", SCALE_1)
                dvg.set_cursor(WIDTH / 2 - (text_len / 2), 64)
                dvg.draw_text("SCORE TABLE", SCALE_1, dvg.colors[9], None)
                
                text_len = dvg.get_text_len(" 20 PTS  50 PTS  100 PTS", SCALE_0)
                dvg.set_cursor(40, 96)
                dvg.draw_text(" 20", SCALE_0, RED, None)
                dvg.draw_text(" PTS", SCALE_0, dvg.colors[7], None)
                
                dvg.set_cursor(96, 96)
                dvg.draw_text(" 50", SCALE_0, RED, None)
                dvg.draw_text(" PTS", SCALE_0, dvg.colors[7], None)
                
                dvg.set_cursor(152, 96)
                dvg.draw_text("100", SCALE_0, RED, None)
                dvg.draw_text(" PTS", SCALE_0, dvg.colors[7], None)
                
                display.set_pen(BLACK)
                display.rectangle(40, 98, 160, 40)
                dvg.draw_asteroids()
                
                dvg.set_cursor(72, 160)
                dvg.draw_text("200", SCALE_0, RED, None)
                dvg.draw_text(" PTS", SCALE_0, dvg.colors[7], None)
                
                dvg.set_cursor(128, 160)
                dvg.draw_text("500", SCALE_0, RED, None)
                dvg.draw_text(" PTS", SCALE_0, dvg.colors[7], None)
                
                dvg.set_cursor(74 + 20, 180)
                dvg.draw_object("ufo", -1, 0, 0, None, None)
                dvg.set_cursor(128 + 20, 180)
                dvg.draw_object("ufo", -2, 0, 0, None, None)
                
                presto.update()
                
                dvg.move_asteroids()
                
                if wait_for_any_key(50) == True:
                    running = False
            
        elif title_012 == 1:
            
            display.set_pen(BLACK)
            display.rectangle(0, 32, WIDTH, HEIGHT - 56)
            
            text_len = dvg.get_text_len("STEERING", SCALE_1)
            dvg.set_cursor(WIDTH / 2 - (text_len / 2), 64)
            dvg.draw_text("STEERING", SCALE_1, dvg.colors[9], None)
            
            display.set_pen(RED)
            display.circle(60 - 16, HEIGHT // 2, 8) #             left
            display.circle(60 + 16, HEIGHT // 2, 8) #             right
            display.circle(WIDTH // 4 * 3, HEIGHT // 2 - 16, 8) # thrust
            display.circle(180 + 16, HEIGHT // 2, 8) #            fire
            display.set_pen(BLACK)
            display.circle(60 - 16, HEIGHT // 2, 6) #             left
            display.circle(60 + 16, HEIGHT // 2, 6) #             right
            display.circle(WIDTH // 4 * 3, HEIGHT // 2 - 16, 6) # thrust
            display.circle(180 + 16, HEIGHT // 2, 6) #            fire
            
            display.set_pen(WHITE)
            display.circle(WIDTH // 4, WIDTH // 2 - 16, 8)
            display.circle(WIDTH // 4, WIDTH // 2 + 16, 8)
            display.circle(180 - 16, HEIGHT // 2, 8)
            display.circle(WIDTH // 4 * 3, WIDTH // 2 + 16, 8)
            display.set_pen(BLACK)
            display.circle(WIDTH // 4, WIDTH // 2 - 16, 6)
            display.circle(WIDTH // 4, WIDTH // 2 + 16, 6)
            display.circle(180 - 16, HEIGHT // 2, 6)
            display.circle(WIDTH // 4 * 3, WIDTH // 2 + 16, 6)
            
            dvg.set_cursor(8, HEIGHT // 2 + 3)
            dvg.draw_text("LEFT", SCALE_0, dvg.colors[9], None)
            dvg.set_cursor(89, HEIGHT // 2 + 3)
            dvg.draw_text("RIGHT", SCALE_0, dvg.colors[9], None)
            dvg.set_cursor(180, HEIGHT // 2 - 28)
            dvg.draw_text("THRUST", SCALE_0, dvg.colors[9], None)
            dvg.set_cursor(209, HEIGHT // 2 + 3)
            dvg.draw_text("FIRE", SCALE_0, dvg.colors[9], None)
        
            presto.update()
            
            if wait_for_any_key(10_000) == True:
                running = False
            
        else:
            
            display.set_pen(BLACK)
            display.rectangle(0, 32, WIDTH, HEIGHT - 56)
            
            text_len = dvg.get_text_len("HALL OF FAME", SCALE_1)
            dvg.set_cursor(WIDTH / 2 - (text_len / 2), 64)
            dvg.draw_text("HALL OF FAME", SCALE_1, dvg.colors[9], None)
            for i in highscores:
                highscore = highscores[i]
                dvg.set_cursor(48, 64 + i * 14)
                dvg.draw_text("{rank}".format(rank = "1ST.2ND.3RD.4TH.5TH.6TH.7TH.8TH.9TH".split(".")[i-1]), SCALE_0, dvg.colors[7], None)
                
                dvg.set_cursor(80, 64 + i * 14)
                dvg.draw_text(highscore["name"],                                                             SCALE_0, dvg.colors[7], None)
                
                dvg.set_cursor(160, 64 + i * 14)
                dvg.draw_text("{score:5d}".format(score = highscore["score"]),                               SCALE_0, RED, None)
        
            presto.update()
            
            if wait_for_any_key(10_000) == True:
                running = False
        
        title_012 += 1
        if title_012 == 3:
            title_012 = 0
    

def show_level():
    init_ambilight(draw = True)
    
    display.set_layer(1)
    display.set_pen(BLACK)
    display.clear()
    
    text_len = dvg.get_text_len("LEVEL " + str(level), SCALE_2)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), HEIGHT / 2 - 16)
    dvg.draw_text("LEVEL ", SCALE_2, dvg.colors[10], None)
    dvg.draw_text(str(level), SCALE_2, RED, None)
    
    presto.update()
    reset_key()
    wait_for_any_key(2_000)


def show_post_level():
    global score
    
    init_ambilight(draw = True)
    
    display.set_layer(1)
    display.set_pen(BLACK)
    display.clear()
    
    text_len = dvg.get_text_len("XXXXX  XXXXX", SCALE_1)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), 64)
    dvg.draw_text("SHOTS  ", SCALE_1, dvg.colors[10], None)
    dvg.draw_text("{shots:5d}".format(shots = shots), SCALE_1, dvg.colors[10], None)

    dvg.set_cursor(WIDTH / 2 - (text_len / 2), 64 + 24)
    dvg.draw_text("HITS   ", SCALE_1, dvg.colors[10], None)
    dvg.draw_text("{hits:5d}".format(hits = hits), SCALE_1, dvg.colors[10], None)
    
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), 64 + 24 + 24)
    dvg.draw_text("RATIO  ", SCALE_1, dvg.colors[10], None)
    ratio = round(100 / shots * hits) if shots > 0 else 0
    dvg.draw_text("{ratio:5d}".format(ratio = ratio), SCALE_1, dvg.colors[10], None)
    
    if ratio >= 75:
        bonus = 5_000
    elif ratio >= 50:
        bonus = 2_500
    elif ratio >= 25:
        bonus = 1_000
    else:
        bonus = 0
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), 64 + 24 + 24 + 24 + 24)
    dvg.draw_text("BONUS  ", SCALE_1, dvg.colors[10], None)
    dvg.draw_text("{bonus:5d}".format(bonus = bonus), SCALE_1, RED, None)
    
    score += bonus
    
    text_len = dvg.get_text_len("PRESS ANY KEY TO CONTINUE", SCALE_0)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), HEIGHT - 16)
    dvg.draw_text("PRESS ANY KEY TO CONTINUE", SCALE_0, dvg.colors[9], None)
    
    presto.update()
    
    wait_for_any_key(5_000)


def show_gameover():
    init_ambilight(draw = True)
    
    dvg.draw_background(True, False, False, False)
    display.set_layer(1)
    display.set_pen(BLACK)
    display.clear()
    
    text_len = dvg.get_text_len("GAME OVER", 2)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), 24)
    dvg.draw_text("GAME ", 2, dvg.colors[12], None)
    dvg.draw_text("OVER", 2, RED, None)
    presto.update()
    time.sleep(1)
    
    text_len = dvg.get_text_len("XXXXX  XXXXX", SCALE_1)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), 64)
    dvg.draw_text("LEVEL  ", SCALE_1, dvg.colors[9], None)
    dvg.draw_text("{level:5d}".format(level = level), SCALE_1, dvg.colors[10], None)
    presto.update()
    time.sleep(1)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), 80)
    dvg.draw_text("SCORE  ", SCALE_1, dvg.colors[9], None)
    dvg.draw_text("{score:5d}".format(score = score), SCALE_1, dvg.colors[10], None)
    presto.update()
    time.sleep(1)
    
    if score <= highscores[9]['score']:
        dvg.set_cursor(WIDTH / 2 - (text_len / 2), 112)
        dvg.draw_text("RANK   ", SCALE_1, dvg.colors[9], None)
        dvg.draw_text(" 10TH", SCALE_1, RED, None)
        
        text_len = dvg.get_text_len("PRESS ANY KEY TO CONTINUE", 0)
        dvg.set_cursor(WIDTH / 2 - (text_len / 2), HEIGHT - 16)
        dvg.draw_text("PRESS ANY KEY TO CONTINUE", 0, dvg.colors[9], None)
        
        presto.update()
        
        wait_for_any_key(10_000)
    else:
        for i in (1, 2, 3, 4, 5, 6, 7, 8, 9):
            if score > highscores[i]["score"]:
                rank = i
                break
        
        dvg.set_cursor(WIDTH / 2 - (text_len / 2), 112)
        dvg.draw_text("RANK     ", SCALE_1, dvg.colors[9], None)
        dvg.draw_text("1ST.2ND.3RD.4TH.5TH.6TH.7TH.8TH.9TH".split(".")[rank-1], SCALE_1, RED, None)
        
        text_len = dvg.get_text_len("ENTER YOUR NAME", SCALE_0)
        dvg.set_cursor(WIDTH / 2 - (text_len / 2), 144)
        dvg.draw_text("ENTER YOUR NAME", SCALE_0, dvg.colors[9], None)
        text_len = dvg.get_text_len("PRESS FIRE TO CONFIRM LETTER", SCALE_0)
        dvg.set_cursor(WIDTH / 2 - (text_len / 2), 160)
        dvg.draw_text("PRESS FIRE TO CONFIRM LETTER", SCALE_0, dvg.colors[9], None)
        text_len = dvg.get_text_len("PRESS THRUST TO CONFIRM NAME", SCALE_0)
        dvg.set_cursor(WIDTH / 2 - (text_len / 2), 176)
        dvg.draw_text("PRESS THRUST TO CONFIRM NAME", SCALE_0, dvg.colors[9], None)
        
        display.set_pen(WHITE)
        for _ in range(0, 10):
            display.line(41 + (_ * 16), 210, 41 + (_ * 16) + 14, 210)
        
        letters       = "ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789"
        letter_number = 0
        letter        = letters[letter_number]
        name          = ""
        end           = False
        
        while end == False:
            display.set_pen(BLACK)
            display.rectangle(41, 190, 158, 16)

            _x = 43
            for _ in name + letter:
                dvg.set_cursor(_x, 204)
                dvg.draw_text(_, SCALE_1, WHITE, None)
                _x += 16
            presto.update()
            
            key = wait_for_key()
            if key == KEY_THRUST:
                name += letter
                end = True
            elif key == KEY_LEFT:
                letter_number -= 1
                if letter_number < 0:
                    letter_number = len(letters) - 1
                letter = letters[letter_number]
            elif key == KEY_RIGHT:
                letter_number += 1
                if letter_number == len(letters):
                    letter_number = 0
                letter = letters[letter_number]
            elif key == KEY_LASER:
                name += letter
                if len(name) == 10:
                    end = True
        
        for i in range(9, rank, -1):
            highscores[i] = highscores[i - 1]
        highscores[rank] = { "name": name, "score":  score }
        write_highscores(highscores)


dvg = DVG()


display.set_layer(0)
display.set_pen(BLACK)
display.clear()
display.set_layer(1)
display.set_pen(BLACK)
display.clear()
presto.update()


# Joystick und Buttons definieren
KEY_LASER  = "A" # Button A (Laser)
KEY_THRUST = "X" # Button X (Thrust)
KEY_LEFT   = "L" # Cursor left
KEY_RIGHT  = "R" # Cursor right


# QwST-Pad initialisieren
try:
    qwstpad = QwSTPad(I2C(**I2C_PINS), I2C_ADDRESS)
except OSError:
    text_len = dvg.get_text_len("QWSTPAD", SCALE_1)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), HEIGHT / 2 - 16)
    dvg.draw_text("QWSTPAD", SCALE_1, RED, None)
    text_len = dvg.get_text_len("NOT CONNECTED", SCALE_1)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), HEIGHT / 2 + 16)
    dvg.draw_text("NOT CONNECTED", SCALE_1, RED, None)
    
    text_len = dvg.get_text_len("DARKSTAR WILL BE DESTROYED IN 10 SECONDS", SCALE_0)
    dvg.set_cursor(WIDTH / 2 - (text_len / 2), HEIGHT - 16)
    dvg.draw_text("DARKSTAR WILL BE DESTROYED IN ", SCALE_0, dvg.colors[9], None)
    dvg.draw_text("10", SCALE_0, RED, None)
    dvg.draw_text(" SECONDS", SCALE_0, dvg.colors[9], None)
    presto.update()
    
    time.sleep(10)
    
    raise SystemExit


highscores = read_highscores()


leds = {}
#          X    Y    Brightness
leds[0] = [240, 240, 0]
leds[1] = [240, 120, 0]
leds[2] = [240, 0,   0]
leds[3] = [120, 0,   0]
leds[4] = [0,   0,   0]
leds[5] = [0,   120, 0]
leds[6] = [0,   240, 0]


while True:
    level    = 0
    score    = 0
    ship     = SHIP()
    ufo      = False
    score_ship_bonus = SHIP_BONUS
    
    show_title()
    
    while ship.count > 0:
        
        level += 1
        
        show_level()
        
        shots = 0
        hits = 0
        
        dvg.asteroids.clear()
        dvg.asteroids_counter = 0
        for i in range(0, 3 + int(level * .5)):
            dvg.asteroids_counter += 1
            dvg.asteroids[dvg.asteroids_counter]  = ASTEROID(0, None, level)
        
        dvg.laser_counter = 0 #                                                Alle rumfliegenden Laser löschen
        dvg.laser.clear()
        
        laser_shot       = False
        laser_shot_ticks = 0
        laser_left       = False
        
        ship.reset() #                                                         Schiff in die Mitte setzen
        
        ufo = False #                                                          UFO gibts noch nicht
        ufo_time = int(time.time()) + UFO_SECONDS + randint(0,UFO_SECONDS_RANDOM)
        
        draw_score = True
        draw_ships = True
        
        ticks_start = time.ticks_ms()
        
        while len(dvg.asteroids) > 0 or type(ufo) is UFO:
            display.set_pen(BLACK)
            display.clear()
            
            buttons = qwstpad.read_buttons()
            left   = buttons[KEY_LEFT]
            right  = buttons[KEY_RIGHT]
            thrust = buttons[KEY_THRUST]
            laser  = buttons[KEY_LASER]
            
            # Wenn Rapidfire nicht zugelassen ist, dann muss der Laser nach jedem Schuss "Pause" machen, also der Button nicht gedrückt sein
            if laser == True:
                if LASER_RAPID_FIRE == False:
                    if laser_shot == True:
                        laser = False
                    else:
                        laser_shot = True
            else:
                laser_shot = False
            
            if laser == True:
                if ship.collision == True or ship.reset_me == True:
                    laser      = False
                    laser_shot = False
            if laser == True:
                if len(dvg.laser) >= LASER_MAX_COUNT:
                    laser      = False
                    laser_shot = False
            if laser == True:
                if (laser_shot_ticks + LASER_COOLDOWN_MS) >= ticks_start:
                    laser      = False
                    laser_shot = False
            if laser == True:
                shots             += 1
                dvg.laser_counter += 1
                laser_shot        =  True
                laser_shot_ticks  =  ticks_start
                laser_left        = not laser_left
                dvg.laser[dvg.laser_counter] = LASER(ship.x, ship.y, ship.speed_x, ship.speed_y, ship.grad, laser_left)
            
            if ship.reset_me == False:
                
                if ship.collision == True:
                    left = False
                    right = False
                    thrust = False
                    laser = False
                    ship.collision_counter += 1
                    if ship.collision_counter >= 60:
                        draw_ships = True
                        ship.count -= 1
                        ship.reset_me = True #                                 Damit das Schiff neu gesetzt wird
                        if ship.count == 0:
                            break
                else:
                    
                    if left == True:
                        ship.turn_left()
                    elif right == True:
                        ship.turn_right()
                    if thrust == True:
                        ship.thrust_on()
                    else:
                        ship.thrust_off()
                        ship.speed_x = ship.speed_x * SHIP_DECELERATION
                        ship.speed_y = ship.speed_y * SHIP_DECELERATION
                        if ship.speed_x > 0 and ship.speed_x < .1:
                            ship.speed_x = 0
                        elif ship.speed_x < 0 and ship.speed_x > -.1:
                            ship.speed_x = 0
                        if ship.speed_y > 0 and ship.speed_y < .1:
                            ship.speed_y = 0
                        elif ship.speed_y < 0 and ship.speed_y > -.1:
                            ship.speed_y = 0

            
            if score >= score_ship_bonus: #                                    Freischiff ergattert?
                draw_score = True
                draw_ships = True
                ship.count += 1
                score_ship_bonus = score_ship_bonus + SHIP_BONUS
            
            dvg.draw_asteroids() #                                             Alle Asteroiden zeichnen
            
            if ufo == False:
                if ufo_time <= int(time.time()):
                    if random() < .3:
                        ufo = UFO(-2)
                    else:
                        ufo = UFO(-1)
            
            if type(ufo) is UFO:
                ufo.draw(dvg)
                if ufo.collision_counter >= 30:
                    ufo = False
                    ufo_time = int(time.time()) + UFO_SECONDS + randint(0,UFO_SECONDS_RANDOM)
            
            dvg.draw_laser()
            
            if ship.reset_me == False and ship.collision_detected(dvg, ufo) == True and ship.collision == False:
                if ship.thrust == True:
                    ship.thrust = False
                ship.collision = True
                ship.collision_counter = 0
                check_ambilight(ship.x, ship.y, draw = False)
            
            if ship.reset_me == True:
                ship.reset()
                ship.reset_me = False
                for i in dvg.asteroids:
                    asteroid = dvg.asteroids[i]
                    a = abs(abs(ship.x) - abs(asteroid.x))
                    b = abs(abs(ship.y) - abs(asteroid.y))
                    c = sqrt(a**2 + b**2)
                    if c <= 64:
                        ship.reset_me = True
                if ship.reset_me == False:
                    ship.draw(dvg) #                                           Das Schiff zeichnen
            else:
                ship.draw(dvg) #                                               Das Schiff zeichnen
            
            # Prüfen, ob ein Laser einen Asteroiden oder das Ufo getroffen hat
            for i in dvg.laser.copy():
                laser = dvg.laser[i]
                laser_to_kill = False
                for j in dvg.asteroids:
                    asteroid = dvg.asteroids[j]
                    if asteroid.collision == False:
                        a = abs(abs(laser.x) - abs(asteroid.x))
                        b = abs(abs(laser.y) - abs(asteroid.y))
                        c = sqrt(a**2 + b**2)
                        if c <= asteroid.diameter:
                            check_ambilight(asteroid.x, asteroid.y, draw = False)
                            hits += 1
                            if asteroid.scale == 0:
                                draw_score = True
                                score += 20
                            elif asteroid.scale == -1:
                                draw_score = True
                                score += 50
                            else:
                                draw_score = True
                                score += 100
                            laser_to_kill = True
                            if asteroid.scale > -2:
                                dvg.asteroids_counter += 1
                                winkel = asteroid.winkel - randint(0, 60)
                                dvg.asteroids[dvg.asteroids_counter]  = ASTEROID(asteroid.scale - 1, None, level, winkel = winkel)
                                dvg.asteroids[dvg.asteroids_counter].x = asteroid.x
                                dvg.asteroids[dvg.asteroids_counter].y = asteroid.y
                            
                            # split only large asteroids in 2 smaller asteroids (to much traffic)
                            if len(dvg.asteroids) < 10 and asteroid.scale > -2:
                                dvg.asteroids_counter += 1
                                winkel = asteroid.winkel + randint(0, 60)
                                dvg.asteroids[dvg.asteroids_counter]  = ASTEROID(asteroid.scale - 1, None, level, winkel = winkel)
                                dvg.asteroids[dvg.asteroids_counter].x = asteroid.x
                                dvg.asteroids[dvg.asteroids_counter].y = asteroid.y
                            asteroid.collision = True
                            asteroid.collision_counter += 0
                            # asteroid.scale = -2
                            asteroid.rotation = 0
                            dvg.asteroids[j] = asteroid
                            break
                if type(ufo) is UFO:
                    if ufo.collision == False:
                        a = abs(abs(laser.x) - abs(ufo.x))
                        b = abs(abs(laser.y) - abs(ufo.y))
                        c = sqrt(a**2 + b**2)
                        if c <= ufo.diameter:
                            check_ambilight(ufo.x, ufo.y, draw = False)
                            hits += 1
                            if ufo.scale == -1:
                                draw_score = True
                                score += 200
                            elif ufo.scale == -2:
                                draw_score = True
                                score += 500
                            laser_to_kill = True
                            ufo.collision = True
                            ufo.collision_counter += 0
                            # ufo.scale = 0
                if laser_to_kill == True:
                    del dvg.laser[i]
            
            if draw_score == True or draw_ships == True:
                dvg.draw_background(False, draw_score, draw_ships, False) #      Punkte und oder Ships anzeigen
                draw_score = False
                draw_ships = False
            
            
            # Dauer des letzten Durchganges errechnen und anzeigen
            ticks_end = time.ticks_ms()
            duration = ticks_end - ticks_start
            if DEBUG == True:
                display.set_pen(BLACK)
                display.rectangle(WIDTH - (4 * 12 + 10), HEIGHT - 12, 4 * 12 + 9, 12)
                dvg.set_cursor(WIDTH - (4 * 12) - 10, HEIGHT - 1)
                # dvg.draw_text("{duration:5d}".format(duration = duration), SCALE_1, RED)
                dvg.draw_text("{asteroids_counter:5d}".format(asteroids_counter = len(dvg.asteroids)), SCALE_1, RED)
            
            if duration < 30:
                time.sleep_ms(30 - duration)
            
            ticks_start = time.ticks_ms()
            
            presto.update()
            
            draw_ambilight()
            dec_ambilight(draw = False)
            
            dvg.move_asteroids() #                       Alle Asteroiden bewegen
            
            if type(ufo) is UFO:
                ufo.move() #                             Ufo bewegen
            
            dvg.move_laser() #                           Alle Laser bewegen
            
            if ship.reset_me == False:
                ship.move()
            
            for i in dvg.laser.copy():
                laser = dvg.laser[i]
                if laser.lifetime <= 0:
                    del dvg.laser[i]
            
        if len(dvg.asteroids) == 0:
            show_post_level()
    
    show_gameover()
