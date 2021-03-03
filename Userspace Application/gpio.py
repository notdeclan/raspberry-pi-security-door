import time
from threading import Thread

import RPi.GPIO as GPIO

from states import States

GPIO.setmode(GPIO.BCM)


class Alarm(Thread):

    def __init__(self, states: States, pin: int = 18):
        super(Alarm, self).__init__(daemon=True)
        self.pin = pin
        self.states = states

    def run(self):
        GPIO.setup(self.pin, GPIO.OUT)
        while True:
            if self.states['alarm_state'] or (self.states['arm_state'] and self.states['door_state']):
                GPIO.output(self.pin, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(self.pin, GPIO.LOW)
                time.sleep(0.1)
            else:
                GPIO.output(self.pin, GPIO.LOW)


class Keypad:
    def __init__(self, row_pins: [] = None, column_pins: [] = None):
        if column_pins is None:
            column_pins = [6, 13, 19, 26]

        if row_pins is None:
            row_pins = [4, 17, 27, 22]

        self.keys = [
            [1, 2, 3, 'A'],
            [4, 5, 6, 'B'],
            [7, 8, 9, 'C'],
            ['*', 0, '#', 'D']
        ]

        self.row_pins = row_pins
        self.column_pins = column_pins

    def get_key(self):
        for j in range(len(self.column_pins)):
            GPIO.setup(self.column_pins[j], GPIO.OUT)
            GPIO.output(self.column_pins[j], GPIO.LOW)

        for i in range(len(self.row_pins)):
            GPIO.setup(self.row_pins[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Scan rows for pushed key/button
        row_value = -1
        for i in range(len(self.row_pins)):
            value = GPIO.input(self.row_pins[i])
            if value == 0:
                row_value = i

        if row_value < -1 or row_value > 3:
            self.exit()
            return

        # Convert columns to input
        for j in range(len(self.column_pins)):
            GPIO.setup(self.column_pins[j], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        # Switch the i-th row_pins found from scan to output
        GPIO.setup(self.row_pins[row_value], GPIO.OUT)
        GPIO.output(self.row_pins[row_value], GPIO.HIGH)

        column_value = -1
        for j in range(len(self.column_pins)):
            value = GPIO.input(self.column_pins[j])
            if value == 1:
                column_value = j

        if column_value < 0 or column_value > 3:
            self.exit()
            return

        self.exit()
        return self.keys[row_value][column_value]

    def exit(self):
        for pin in range(len(self.row_pins)):
            GPIO.setup(self.row_pins[pin], GPIO.IN, pull_up_down=GPIO.PUD_UP)

        for pin in range(len(self.column_pins)):
            GPIO.setup(self.column_pins[pin], GPIO.IN, pull_up_down=GPIO.PUD_UP)
