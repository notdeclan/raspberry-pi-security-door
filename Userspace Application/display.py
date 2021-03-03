import subprocess
import time
from abc import abstractmethod, ABC
from datetime import datetime
from threading import Thread

import Adafruit_SSD1306
from PIL import Image, ImageDraw, ImageFont

font = ImageFont.load_default()


class Screen(ABC):
    """
    Base Screen class

    Abstract and Should not be initialized without being inherited
    """

    @abstractmethod
    def render(self, draw: ImageDraw.Draw):
        """
        Called by Display if screen is active
        :param draw: ImageDraw to draw on
        """
        pass


class InformationScreen(Screen):
    """
    Information Screen
    Displays time, arm state, and device id
    """

    def __init__(self, states):
        self.states = states

    def render(self, draw: ImageDraw.Draw):
        current_time = datetime.now().strftime("%H:%M:%S")
        arm_state = "ARMED" if self.states["arm_state"] else "DISARMED"
        id = f'ID: {self.states["deviceId"]}'

        # Display Time
        w, h = draw.textsize(current_time)
        draw.text(((128 - w) / 2, 0), current_time, font=font, fill=255)
        # Display Arm State
        w, h = draw.textsize(arm_state)
        draw.text(((128 - w) / 2, (32 - h) / 2), arm_state, font=font, fill=255)
        # Display Device Id
        w, h = draw.textsize(id)
        draw.text(((128 - w) / 2, 20), id, font=font, fill=255)


class KeypadScreen(Screen):
    """
    Keyboard Screen
    Displays currently typed keypad keys
    """

    def __init__(self, code: []):
        self.code = code

    def render(self, draw: ImageDraw.Image):
        # Display Title
        title = "PASSCODE"
        w, h = draw.textsize(title)
        draw.text(((128 - w) / 2, 7), title, font=font, fill=255)

        # Display Entered Pin code
        code = ' '.join(str(i) for i in self.code)
        w, h = draw.textsize(code)
        draw.text(((128 - w) / 2, 18), code, font=font, fill=255)


class MessageScreen(Screen):
    """
    Message Screen
    Displays message in center of screen
    """

    def __init__(self, message):
        self.message = message

    def render(self, draw: ImageDraw.Draw):
        w, h = draw.textsize(self.message)
        draw.text(((128 - w) / 2, (32 - h) / 2), self.message, font=font, fill=255)


class SetupScreen(Screen):
    """
    Setup Screen
    Displays SETUP MODE and ID if device does not have a passcode_hash
    """

    def __init__(self, states):
        self.states = states

    def render(self, draw: ImageDraw.Draw):
        title = "SETUP MODE"
        id = self.states['deviceId']
        # Display Arm State
        w, h = draw.textsize(title)
        draw.text(((128 - w) / 2, (32 - h) / 2), title, font=font, fill=255)

        # Display Id
        w, h = draw.textsize(id)
        draw.text(((128 - w) / 2, 20), id, font=font, fill=255)


class Display(Thread):
    """
    Display

    Used to render screens upon the I2C OLED Display
    """

    def __init__(self, update_frequency=0.1):
        super().__init__(daemon=True)

        self._display = Adafruit_SSD1306.SSD1306_128_32(rst=None)
        self._display.begin()
        self._display.clear()
        self._display.display()

        self._screen = None
        self.update_frequency = update_frequency

    def set_screen(self, screen: Screen):
        if not screen == self._screen:
            self._screen = screen

    def run(self):
        width = self._display.width
        height = self._display.height

        image = Image.new('1', (width, height))
        draw = ImageDraw.Draw(image)

        while True:
            # Clear Screen
            draw.rectangle((0, 0, width, height), outline=0, fill=0)

            # Render Screen is set
            if self._screen:
                self._screen.render(draw)

            # Display Image on Screen
            self._display.image(image)
            self._display.display()
            time.sleep(self.update_frequency)