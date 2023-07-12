# Simple Computer Railway Access Module - SCRAM

from time import ticks_ms, ticks_diff, sleep
from machine import Pin, PWM
from neopixel import NeoPixel as Neopixel

class Activity:
    def __init__(self, target, work):
        self._target = target
        self._work = work
        
class Button:
    DEBOUNCE_TIME = 1000 # 1 second
    
    def __init__(self, id, pin, button_pressed_list):
        self.id = id
        self.button_pressed_list = button_pressed_list
        self.last_pressed = ticks_ms()
        
        self.button = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        self.button.irq(trigger = machine.Pin.IRQ_RISING, handler = lambda pin: Button._pressed(self))
        
    def _pressed(self):
        now = ticks_ms()
        if ticks_diff(now, self.last_pressed) > Button.DEBOUNCE_TIME and self not in self.button_pressed_list:
            self.last_pressed = now
            self.button_pressed_list.append(self)

class Servo:
    # Express MIN and MAX in terms of percentage of duty cycle across the frequency
    # in this case MIN is 3% of 1/50 (1/FREQ) or 600,000ns and MAX is 12% of 1/50 or
    # 2,400,000ns
    FREQ = 50
    MIN = int(1000000000 / FREQ / 100 * 3)
    MAX = int(1000000000 / FREQ / 100 * 12)
    MID = int(MIN + ((MAX - MIN) / 2))
    OFF = 0

    def __init__(self, pin):
        self.control = PWM(Pin(pin))
        self.control.freq(Servo.FREQ)
        self.position_duty_cycle = None
    
    def center(self):
        self._set_position(self.MID)
        
    def minimum(self):
        self._set_position(self.MIN)
    
    def maximum(self):
        self._set_position(self.MAX)
    
    def move_to_percentage(self, percentage):
        if percentage < 0:
            p = 0
        elif percentage > 100:
            p = 100.0
        else:
            p = float(percentage)
        duty_cycle = self.MIN + int(((self.MAX - self.MIN) / 100.0) * p)
        self._set_position(duty_cycle)
    
    def get_position_as_percentage(self):
        offset = self.position_duty_cycle - self.MIN
        if offset != 0:
            return offset / (self.MAX - self.MIN) * 100.0
        else:
            return 0
        
    def move_to_degree(self, degree):
        if degree < -90:
            d = -90
        elif degree > 90:
            d = 90
        else:
            d = degree
        duty_cycle = self.MIN + int(((self.MAX - self.MIN) / 180.0) * (d + 90.0))
        self._set_position(duty_cycle)
    
    def get_position_as_degree(self):
        offset = self.position_duty_cycle - self.MIN
        if offset != 0:
            return (offset / (self.MAX - self.MIN) * 180.0) - 90.0
        else:
            return -90
    
    def finish(self):
        self.control.deinit()
        
    def idle(self):
        self.control.duty_ns(0)
    
    def _set_position(self, position):
        self.position_duty_cycle = int(position)
        self.control.duty_ns(self.position_duty_cycle)

# Signals were going to be servo driven, then 12v relay, finally moved 'off stage'
# and may be done as Neopixels at some stage in the future
# class Signal:
#     MAX_DOWN = 90
#     MIN_DOWN = 10
#     MAX_LIFT = 10
#     MIN_LIFT = 45
#     LIFT_BOUNCES = 2
#     DROP_BOUNCES = 4
#     
#     def __init__(self, control_pin, danger_position = 90, clear_position = 45, drop_speed = 75 / 1000, lift_speed = 25 / 1000, to_idle_period = 250, set_to = '-'):
#         if danger_position > self.MAX_DOWN:
#             self.danger_position = self.MAX_DOWN
#         elif danger_position < self.MIN_DOWN:
#             self.danger_position = self.MIN_DOWN
#         else:
#             self.danger_position = danger_position
#         
#         if clear_position < self.MAX_LIFT:
#             self.clear_position = self.MAX_LIFT
#         elif clear_position >= self.MIN_LIFT:
#             self.clear_position = self.MIN_LIFT
#         else:
#             self.clear_position = clear_position
#         
#         if self.clear_position > self.danger_position:
#             self.center_position = self.danger_position + ((self.clear_position - self.danger_position) / 2)
#         else:
#             self.center_position = self.clear_position + ((self.danger_position - self.clear_position) / 2)
#         
#         self.control_pin = control_pin
#         self.servo = Servo(control_pin)
# 
#         self.lift_speed = lift_speed # Degrees per milisecond
#         self.drop_speed = drop_speed
#         self.lift_bounces = self.LIFT_BOUNCES
#         self.drop_bounces = self.DROP_BOUNCES
#         self.targets = []
#         self.target_ndx = 0
#         self.lift_targets = []
#         self.drop_targets = []
#         for ndx in range(self.lift_bounces + 1):
#             self.lift_targets.append(self.clear_position)
#             self.lift_targets.append(self.clear_position + (self.lift_speed * (self.lift_bounces - ndx) * 100))
#         for ndx in range(self.drop_bounces + 1):
#             self.drop_targets.append(self.danger_position)
#             self.drop_targets.append(self.danger_position - (self.drop_speed * (self.drop_bounces - ndx) * 25))
#         
#         self.move_start_ms = 0
#         self.current_position = 0
#         self.start_position = 0
#         self.target_position = 0
#         self.requested_position = ''
#         self.init_set_to = set_to
#         self.set_target_position(set_to)
#         self._move_to(self.target_position)
#         # Give it 2/50 of a second to move
#         sleep(1.0 / 50.0 * 2.0)
#         self.servo.idle()
#         self.direction = 0
#         self.to_idle_period = to_idle_period
#         self.to_idle_start_ms = 0
#     
#     def _move_to(self, position):
#         self.current_position = position
#         self.servo.move_to_degree(position)
#     
#     def danger(self):
#         self.requested_position = 'danger'
#         self.targets = self.drop_targets
#         self.target_ndx = 0
#         self.set_target(self.targets[self.target_ndx])
#     
#     def clear(self):
#         self.requested_position = 'clear'
#         self.targets = self.lift_targets
#         self.target_ndx = 0
#         self.set_target(self.targets[self.target_ndx])
# 
#     def center(self):
#         self.requested_position = 'center'
#         self.targets = None
#         self.set_target(self.center_position)
# 
#     def update(self):
#         if self.direction:
#             t = ticks_ms() - self.move_start_ms
#             if self.direction > 0:
#                 next_position = self.start_position + (self.drop_speed * t * self.direction)
#                 if next_position > self.target_position:
#                     next_position = self.target_position
#             else:
#                 next_position = self.start_position + (self.lift_speed * t * self.direction)
#                 if next_position < self.target_position:
#                     next_position = self.target_position
#             
#             self._move_to(next_position)
#             
#             if self.target_position == self.current_position:
#                 # Reached target, if bouncing then set next bounce target
#                 if self.targets and self.target_ndx < len(self.targets) - 1:
#                     self.target_ndx += 1
#                     self.set_target(self.targets[self.target_ndx])
#                 else:
#                     # Reached target so indicate stopping movement by setting direction to zero
#                     # and starting settle timer
#                     self.direction = 0
#                     self.to_idle_start_ms = ticks_ms()
#             
#         if self.to_idle_start_ms:
#             t = ticks_ms() - self.to_idle_start_ms
#             if self.to_idle_period < t:
#                 # Reached the end of the settle period, put the servo into idle and
#                 # set the settle finish indicator
#                 self.servo.idle()
#                 self.to_idle_start_ms = 0
# 
#     def is_moving_to_target(self):
#         return self.direction != 0
# 
#     def is_on_target(self):
#         return not self.is_moving_to_target()
# 
#     def is_settling(self):
#         return self.to_idle_start_ms != 0
# 
#     def is_settled(self):
#         return not self.is_settling()
# 
#     def is_active(self):
#         return self.is_moving_to_target() or self.is_settling()
#     
#     def is_passive(self):
#         return not self.is_active()
# 
#     def set_target_position(self, flag):
#         f = flag.lower()
#         if f == 'd':
#             self.set_target(self.danger_position)
#         elif f == 'c':
#             self.set_target(self.clear_position)
#         elif f == '-':
#             self.set_target(self.center_position)
# 
#     def set_target(self, target):
#         if self.current_position != target:
#             self.start_position = self.current_position
#             self.target_position = target
#             self.move_start_ms = ticks_ms()
#             if self.target_position < self.current_position:
#                 self.direction = -1
#             else:
#                 self.direction = 1

class Indicators:
    
    BLACK = (0, 0, 0, 0)
    RED = (50, 0, 0, 0)
    GREEN = (0, 50, 0, 0)
    YELLOW = (45, 27, 0, 0)
    
    def __init__(self, indicator_count = 6, state_machine = 0, pin = 18, mode = 'GRB'):
        self.id = id
        self.count = indicator_count
        self.pixels = Neopixel(Pin(pin), indicator_count, bpp = 4)
        self.set_passive()
    
    def set_color(self, indicator, color):
        self.pixels.__setitem__(indicator, color)
        
    def black(self, indicator):
        self.set_color(indicator, Indicators.BLACK)
    
    def red(self, indicator):
         self.set_color(indicator, Indicators.RED)
         
    def green(self, indicator):
        self.set_color(indicator, Indicators.GREEN)
        
    def yellow(self, indicator):
        self.set_color(indicator, Indicators.YELLOW)
    
    def is_active(self):
        return self.active
    
    def is_passive(self):
        return not self.is_active()
    
    def set_active(self):
        self.active = True
    
    def set_passive(self):
        self.active = False
    
    def update(self):
        if self.is_active():
            self.pixels.write()
            self.set_passive()

class WestPointsIndicators:
    def __init__(self, indicators):
        self.indicators = indicators
        self.set_passive()
    
    def is_active(self):
        return self.active or self.indicators.is_active()
    
    def is_passive(self):
        return not self.is_active()
    
    def set_active(self):
        self.indicators.set_active()
        self.active = True
    
    def set_passive(self):
        self.active = False
    
    def update(self):
        if self.indicators.is_active():
            self.indicators.update()
            self.set_passive()
    
    def start_of_day(self):
        self.indicators.red(0)
        self.indicators.red(1)
        self.indicators.set_active()
    
    def transition(self):
        self.indicators.yellow(0)
        self.indicators.yellow(1)
        self.indicators.set_active()
    
    def normal(self):
        self.indicators.green(0)
        self.indicators.red(1)
        self.indicators.set_active()
    
    def reverse(self):
        self.indicators.red(0)
        self.indicators.green(1)
        self.indicators.set_active()

class EastPointsIndicators:
    def __init__(self, indicators):
        self.indicators = indicators
        self.set_passive()
    
    def is_active(self):
        return self.active
    
    def is_passive(self):
        return not self.is_active()
    
    def set_active(self):
        self.active = True
    
    def set_passive(self):
        self.active = False
        
    def update(self):
        if self.indicators.is_active():
            self.indicators.update()
            self.set_passive()
    
    def start_of_day(self):
        self.indicators.red(4)
        self.indicators.red(5)
        self.indicators.set_active()
    
    def transition(self):
        self.indicators.yellow(4)
        self.indicators.yellow(5)
        self.indicators.set_active()
    
    def normal(self):
        self.indicators.green(4)
        self.indicators.red(5)
        self.indicators.set_active()
    
    def reverse(self):
        self.indicators.red(4)
        self.indicators.green(5)
        self.indicators.set_active()
    
class SouthPointsIndicators:
    def __init__(self, indicators):
        self.indicators = indicators
        self.set_passive()
    
    def is_active(self):
        return self.active
    
    def is_passive(self):
        return not self.is_active()
    
    def set_active(self):
        self.active = True
    
    def set_passive(self):
        self.active = False
    
    def update(self):
        if self.indicators.is_active():
            self.indicators.update()
            self.set_passive()
    
    def start_of_day(self):
        self.indicators.red(2)
        self.indicators.red(3)
        self.indicators.set_active()
    
    def transition(self):
        self.indicators.yellow(2)
        self.indicators.yellow(3)
        self.indicators.set_active()
    
    def normal(self):
        self.indicators.green(2)
        self.indicators.red(3)
        self.indicators.set_active()
    
    def reverse(self):
        self.indicators.red(2)
        self.indicators.green(3)
        self.indicators.set_active()
    
class Points:
    MAX_THROW = 45
    
    def __init__(self, control_pin, left_max = 35, right_max = 35, move_speed = 30 / 1000, to_idle_period = 250, set_to = 'c', invert = False):
        if left_max > self.MAX_THROW:
            self.left_max = -self.MAX_THROW
        elif left_max < 0:
            self.left_max = 0
        else:
            self.left_max = -left_max
            
        if right_max > self.MAX_THROW:
            self.right_max = self.MAX_THROW
        elif right_max < 0:
            self.right_max = 0
        else:
            self.right_max = right_max
        
        self.control_pin = control_pin
        self.servo = Servo(control_pin)
        
        self.move_speed = move_speed # Degrees per milisecond
        
        self.move_start_ms = 0
        self.current_position = 0
        self.start_position = 0
        self.target_position = 0
        self.init_set_to = set_to
        self.invert = invert
        self.set_target_throw(set_to)
        self._move_to(self.target_position)
        # Give it 2/50 of a second to move
        sleep(1.0 / 50.0 * 2.0)
        self.servo.idle()
        self.direction = 0
        self.to_idle_period = to_idle_period
        self.to_idle_start_ms = 0

    def _move_to(self, position):
        self.current_position = position
        # If the degree position needs to be inverted because of what the Servo
        # thinks of as left and right are the opposite of how we want the tracks
        # from the turnout to run
        degree = position
        if self.invert:
            degree *= -1
        self.servo.move_to_degree(degree)

    def throw_left(self):
        self.set_target_throw('l')
        
    def throw_right(self):
        self.set_target_throw('r')
        
    def center(self):
        self.set_target_throw('c')
    
    # The normal and reverse settings of the points model the way points are
    # thought of in the real world, normal is straight on and reverse is a
    # turn off. The arbitrary decision was made for the throw left to be
    # straight on and throw right to be reverse because 'right' and 'reverse'
    # both have an initial 'r' and 'r' also looks a bit like a a set of
    # points with the branch to the right
    def normal(self):
        self.throw_left()
    
    def reverse(self):
        self.throw_right()

    def is_moving_to_target(self):
        return self.direction != 0
    
    def is_on_target(self):
        return not self.is_moving_to_target()
    
    def is_settling(self):
        return self.to_idle_start_ms != 0
    
    def is_settled(self):
        return not self.is_settling()
    
    def is_active(self):
        return self.is_moving_to_target() or self.is_settling()

    def is_passive(self):
        return not self.is_active()

    def set_target_throw(self, hand):
        h = hand.lower()
        if h == 'r':
            self.set_target(self.right_max)
        elif h == 'l':
            self.set_target(self.left_max)
        elif h == 'c':
            self.set_target(0)

    def set_target(self, target):
        if self.current_position != target:
            self.start_position = self.current_position
            self.target_position = target
            self.move_start_ms = ticks_ms()
            if self.target_position < self.current_position:
                self.direction = -1
            else:
                self.direction = 1

    def update(self):
        if self.direction:
            t = ticks_ms() - self.move_start_ms
            next_position = self.start_position + (self.move_speed * t * self.direction)
            if self.direction > 0:
                if next_position > self.target_position:
                    next_position = self.target_position
            else:
                if next_position < self.target_position:
                    next_position = self.target_position
            
            self._move_to(next_position)
            
            if self.target_position == self.current_position:
                # Reached target so indicate stopping movement by setting direction to zero
                # and starting settle timer
                self.direction = 0
                self.to_idle_start_ms = ticks_ms()
            
        if self.to_idle_start_ms:
            t = ticks_ms() - self.to_idle_start_ms
            if self.to_idle_period < t:
                # Reached the end of the settle period, put the servo into idle and
                # set the settle finish indicator
                self.servo.idle()
                self.to_idle_start_ms = 0

class Note:
    B0 = 31
    C1 = 33
    CS1 = 35
    D1 = 37
    DS1 = 39
    E1 = 41
    F1 = 44
    FS1 = 46
    G1 = 49
    GS1 = 52
    A1 = 55
    AS1 = 58
    B1 = 62
    C2 = 65
    CS2 = 69
    D2 = 73
    DS2 = 78
    E2 = 82
    F2 = 87
    FS2 = 93
    G2 = 98
    GS2 = 104
    A2 = 110
    AS2 = 117
    B2 = 123
    C3 = 131
    CS3 = 139
    D3 = 147
    DS3 = 156
    E3 = 165
    F3 = 175
    FS3 = 185
    G3 = 196
    GS3 = 208
    A3 = 220
    AS3 = 233
    B3 = 247
    C4 = 262
    CS4 = 277
    D4 = 294
    DS4 = 311
    E4 = 330
    F4 = 349
    FS4 = 370
    G4 = 392
    GS4 = 415
    A4 = 440
    AS4 = 466
    B4 = 494
    C5 = 523
    CS5 = 554
    D5 = 587
    DS5 = 622
    E5 = 659
    F5 = 698
    FS5 = 740
    G5 = 784
    GS5 = 831
    A5 = 880
    AS5 = 932
    B5 = 988
    C6 = 1047
    CS6 = 1109
    D6 = 1175
    DS6 = 1245
    E6 = 1319
    F6 = 1397
    FS6 = 1480
    G6 = 1568
    GS6 = 1661
    A6 = 1760
    AS6 = 1865
    B6 = 1976
    C7 = 2093
    CS7 = 2217
    D7 = 2349
    DS7 = 2489
    E7 = 2637
    F7 = 2794
    FS7 = 2960
    G7 = 3136
    GS7 = 3322
    A7 = 3520
    AS7 = 3729
    B7 = 3951
    C8 = 4186
    CS8 = 4435
    D8 = 4699
    DS8 = 4978
    REST = 0

class Tunes:
    tune_index = -1
    
    def next():
        Tunes.tune_index += 1
        if Tunes.tune_index >= 3:
            Tunes.tune_index = 0
        
        if Tunes.tune_index == 0:
            return Tunes.hedwig()
        elif Tunes.tune_index == 1:
            return Tunes.starwars()
        elif Tunes.tune_index == 2:
            return Tunes.startrek()
        else:
            return None
    
    def hedwig():
        return (250,
                [(Note.REST, 2), (Note.D4, 4), (Note.G4, -4), (Note.AS4, 8), (Note.A4, 4), (Note.G4, 2),
                (Note.D5, 4), (Note.C5, -2), (Note.A4, -2), (Note.G4, -4), (Note.AS4, 8), (Note.A4, 4),
                (Note.F4, 2), (Note.GS4, 4), (Note.D4, -1), (Note.D4, 4), (Note.G4, -4), (Note.AS4, 8),
                (Note.A4, 4), (Note.G4, 2), (Note.D5, 4), (Note.F5, 2), (Note.E5, 4), (Note.DS5, 2),
                (Note.B4, 4), (Note.DS5, -4), (Note.D5, 8), (Note.CS5, 4), (Note.CS4, 2), (Note.B4, 4),
                (Note.G4, -1), (Note.AS4, 4), (Note.D5, 2), (Note.AS4, 4), (Note.D5, 2), (Note.AS4, 4),
                (Note.DS5, 2), (Note.D5, 4), (Note.CS5, 2), (Note.A4, 4), (Note.AS4, -4), (Note.D5, 8),
                (Note.CS5, 4), (Note.CS4, 2), (Note.D4, 4), (Note.D5, -1), (Note.REST, 4), (Note.AS4,4),
                (Note.D5, 2), (Note.AS4, 4), (Note.D5, 2), (Note.AS4, 4), (Note.F5, 2), (Note.E5, 4),
                (Note.DS5, 2), (Note.B4, 4), (Note.DS5, -4), (Note.D5, 8), (Note.CS5, 4), (Note.CS4, 2),
                (Note.AS4, 4), (Note.G4, -1)])
    
    def starwars():
        return (200,
                [(Note.AS4, 8), (Note.AS4, 8), (Note.AS4, 8), (Note.F5, 2), (Note.C6, 2), (Note.AS5, 8),
                (Note.A5, 8), (Note.G5, 8), (Note.F6, 2), (Note.C6, 4), (Note.AS5, 8), (Note.A5, 8),
                (Note.G5, 8), (Note.F6, 2), (Note.C6, 4), (Note.AS5, 8), (Note.A5, 8), (Note.AS5, 8),
                (Note.G5, 2), (Note.C5, 8), (Note.C5, 8), (Note.C5, 8), (Note.F5, 2), (Note.C6,2),
                (Note.AS5, 8), (Note.A5, 8), (Note.G5, 8), (Note.F6, 2), (Note.C6, 4), (Note.AS5, 8),
                (Note.A5, 8), (Note.G5, 8), (Note.F6, 2), (Note.C6, 4), (Note.AS5, 8), (Note.A5, 8),
                (Note.AS5, 8), (Note.G5, 2), (Note.C5, -8), (Note.C5, 16), (Note.D5, -4), (Note.D5, 8),
                (Note.AS5, 8), (Note.A5, 8), (Note.G5, 8), (Note.F5, 8), (Note.F5, 8), (Note.G5, 8),
                (Note.A5, 8), (Note.G5, 4), (Note.D5, 8), (Note.E5, 4), (Note.C5, -8), (Note.C5,16),
                (Note.D5, -4), (Note.D5, 8), (Note.AS5, 8), (Note.A5, 8), (Note.G5, 8), (Note.F5, 8),
                (Note.C6, -8), (Note.G5, 16), (Note.G5, 2), (Note.REST, 8), (Note.C5, 8), (Note.D5, -4),
                (Note.D5, 8), (Note.AS5, 8), (Note.A5, 8), (Note.G5, 8), (Note.F5, 8), (Note.F5, 8),
                (Note.G5, 8), (Note.A5, 8), (Note.G5, 4), (Note.D5, 8), (Note.E5, 4), (Note.C6, -8),
                (Note.C6, 16), (Note.F6, 4), (Note.DS6, 8), (Note.CS6, 4), (Note.C6, 8), (Note.AS5, 4),
                (Note.GS5, 8), (Note.G5, 4), (Note.F5, 8), (Note.C6, 1)])

    def startrek():
        return (150,
                [(Note.D4, -8), (Note.G4, 16), (Note.C5, -4), (Note.B4, 8), (Note.G4, -16), (Note.E4, -16),
                (Note.A4, -16), (Note.D5, 2)])

if __name__ == '__main__':
    from time import sleep
    
    tempo = 0
    whole_note_duration = 0
    
    def tone(buzzer, freq, duration):
        if freq > 0:
            buzzer.freq(freq)
            buzzer.duty_u16(1000)
        sleep(duration)
        buzzer.duty_u16(0)
    
    def play(note):
        divider = note[1]
        if divider > 0:
            duration = whole_note_duration / divider
        elif divider < 0:
            # dotted note
            duration = whole_note_duration / divider * (-1.5)
        
        tone(feedback_buzzer, note[0], duration * 0.9)
        sleep(duration * 0.1)        

    def process(tasks):
        if isinstance(tasks, list):
            for t in tasks:
                start_task(t)
            while any_active(tasks):
                for t in tasks:
                    update_task(t)
        elif isinstance(tasks, Activity):
            t = tasks
            start_task(t)
            while t._target.is_active():
                update_target(t)            

    def start_task(task):
        if isinstance(task, list):
            process(task)
        elif isinstance(task, str):
            print('Processing', task)
        elif isinstance(task, Activity):
            task._work()
    
    def update_task(task):
        if isinstance(task, Activity):
            task._target.update()
    
    def any_active(tasks):
        active = False
        
        for t in tasks:
            if isinstance(t, Activity):
                if t._target.is_active():
                    active = True
                    break
        
        return active
    
    feedback_buzzer = PWM(Pin(22))

    pressed_button_list = []
    buttons = []
    buttons.append(Button('A', 2, pressed_button_list))
    buttons.append(Button('B', 3, pressed_button_list))
    buttons.append(Button('C', 4, pressed_button_list))
    buttons.append(Button('D', 5, pressed_button_list))
    buttons.append(Button('S', 16, pressed_button_list))
    buttons.append(Button('X', 17, pressed_button_list))
        
    west_points = Points(15, invert = True)
    east_points = Points(12, invert = True)
    south_points = Points(13, invert = True)
    
    indicators = Indicators(6, pin = 1, mode = 'GRBW') # Neopixels controlled by pin 1
    
    west_points_indicators = WestPointsIndicators(indicators)
    east_points_indicators = EastPointsIndicators(indicators)
    south_points_indicators = SouthPointsIndicators(indicators)
    
    start_of_day = [ ['Start of day',
                      Activity(west_points_indicators, west_points_indicators.start_of_day),
                      Activity(east_points_indicators, east_points_indicators.start_of_day),
                      Activity(south_points_indicators, south_points_indicators.start_of_day),
                      Activity(east_points, east_points.normal),
                      Activity(west_points, west_points.normal),
                      Activity(south_points, south_points.normal)] ]
    
    main_line_to_platform = [ ['Main line to platform'],
                              [Activity(west_points_indicators, west_points_indicators.transition),
                               Activity(east_points_indicators, east_points_indicators.transition)],
                              [Activity(west_points, west_points.normal), Activity(east_points, east_points.normal)],
                              [Activity(west_points_indicators, west_points_indicators.normal),
                               Activity(east_points_indicators, east_points_indicators.normal)] ]

    main_line_from_platform = [ ['Main line from platform'],
                                [Activity(west_points_indicators, west_points_indicators.transition),
                                 Activity(east_points_indicators, east_points_indicators.transition)],
                                [Activity(west_points, west_points.normal), Activity(east_points, east_points.normal)],
                                [Activity(west_points_indicators, west_points_indicators.normal),
                                 Activity(east_points_indicators, east_points_indicators.normal)] ]
    
    loop_line = [ ['Loop line'],
                  [Activity(west_points_indicators, west_points_indicators.transition),
                   Activity(east_points_indicators, east_points_indicators.transition),
                   Activity(south_points_indicators, south_points_indicators.transition)],
                  [Activity(west_points, west_points.reverse),
                   Activity(east_points, east_points.reverse),
                   Activity(south_points, south_points.normal)],
                  [Activity(west_points_indicators, west_points_indicators.reverse),
                   Activity(east_points_indicators, east_points_indicators.reverse),
                   Activity(south_points_indicators, south_points_indicators.normal)] ]
    
    goods_line = [ ['Goods line'],
                   [Activity(west_points_indicators, west_points_indicators.transition),
                    Activity(south_points_indicators, south_points_indicators.transition)],
                   [Activity(south_points, south_points.reverse),
                    Activity(west_points, west_points.reverse)],
                   [Activity(west_points_indicators, west_points_indicators.reverse),
                    Activity(south_points_indicators, south_points_indicators.reverse)] ]
    
    
    print('All servos at neutral')
    print('Waiting for 2 seconds')
    sleep(2)
    
    print('Start of day, signals at danger, all points straight through')
    process(start_of_day)
    sleep(2)
    
#     print('Exercise routes')
#     for ndx in range(4):
#         button = buttons[ndx]
#         print('Route', button.id)
#         if button.id == 'A':
#             print('Main line to platform')
#             process(main_line_to_platform)
#         elif button.id == 'B':
#             print('Main line from platform')
#             process(main_line_from_platform)
#         elif button.id == 'C':
#             print('Loop line')
#             process(loop_line)
#         elif button.id == 'D':
#             print('Goods line')
#             process(goods_line)
#         sleep(2)
#     
#     print('Return to start of day')
#     process(start_of_day)
    
#     while True:
#         button = input('Select a route from keyboard (A, B, C, D, S - Start of day, X - move on): ')
#         if button == 'x':
#             break
#         elif button == 'a':
#             print('Main line to platform')
#             process(main_line_to_platform)
#         elif button == 'b':
#             print('Main line from platform')
#             process(main_line_from_platform)
#         elif button == 'c':
#             print('Loop line')
#             process(loop_line)
#         elif button == 'd':
#             print('Goods line')
#             process(goods_line)
#         elif button == 'e':
#             print('Test 1')
#             process(test_1)
#         elif button == 'f':
#             print('Test 2')
#             process(test_2)
#         elif button == 's':
#             print('Start of day')
#             process(start_of_day)

    feedback = False
    feedback_alter_count = 0
    easter_egg_count = 0
    print('Select a route by a button')
    while True:
        if len(pressed_button_list) > 0:
            # process the button press and remove button from the list
            button = pressed_button_list.pop(0)
            
            # Handle setting of feedback buzzer, three 'start of day' in a row
            # flips the setting
            if button.id == 'S':
                feedback_alter_count += 1
            else:
                feedback_alter_count = 0
                
            if feedback_alter_count == 3:
                feedback = not feedback
                
            if feedback:
                tone(feedback_buzzer, 659, 0.2)
            
            # Handle easter egg tunes, press route A twice, route B once, route a twice and route B once
            # and the next tune in sequence will be played
            if button.id == 'A' and (easter_egg_count == 0 or easter_egg_count == 1 or easter_egg_count == 3 or easter_egg_count == 4):
                easter_egg_count += 1
            elif button.id == 'B' and (easter_egg_count == 2 or easter_egg_count == 5):
                easter_egg_count += 1
            else:
                easter_egg_count = 0
            if easter_egg_count == 6:
                tempo, tune = Tunes.next()
                whole_note_duration = 100 * 4 / tempo
                for note in tune:
                    play(note)
                easter_egg_count = 0
                
            if button.id == 'A':
                print('route A')
                process(main_line_to_platform)
            elif button.id == 'B':
                print('route B')
                process(main_line_from_platform)
            elif button.id == 'C':
                print('route C')
                process(loop_line)
            elif button.id == 'D':
                print('route D')
                process(goods_line)
            elif button.id == 'S':
                print('Start of day')
                process(start_of_day)
            elif button.id == 'X':
                print('Exiting')
                break
