import pyautogui as pg
import random
import time
from pyHM import mouse
from loguru import logger
from utility.interception_py.interception import *
from utility.key_codes import KEYBOARD_MAPPING
from win32api import GetSystemMetrics


class InputHelper:
    """Wrapper class to handle keyboard/mouse inputs based on input method."""
    def __init__(self, input_method, reaction_time_range, *args, **kwargs):
        self.INPUT_METHOD = input_method
        self.REACTION_TIME_RANGE = reaction_time_range

        if self.INPUT_METHOD == 'interception':
            self.driver = interception()
            self.mouse_driver = self.get_driver_mouse()
            self.keyboard_driver = self.get_driver_keyboard()
            self.screen_width = GetSystemMetrics(0)
            self.screen_height = GetSystemMetrics(1)

        # Doesn't seem like there are any keycodes for these natively.
        self.KEY_MAP = {
            '!': '1',
            '@': '2',
            '#': '3',
            '$': '4',
            '%': '5',
            '^': '6',
            '&': '7',
            '*': '8',
            '(': '9',
            ')': '0',
            '-': '_',
            '=': '+'
        }


    def move_mouse(self, x, y):
        """Moves cursor to x,y on screen."""
        if self.INPUT_METHOD == 'virtual':
            time.sleep(random.uniform(self.REACTION_TIME_RANGE[0], self.REACTION_TIME_RANGE[1]))
            try:
                mouse.move(x,y)
            except Exception:
                logger.warning('Failed to move mouse')
            time.sleep(random.uniform(self.REACTION_TIME_RANGE[0], self.REACTION_TIME_RANGE[1]))
        elif self.INPUT_METHOD == 'interception':
            self.move_mouse_driver(x,y)
            pass
        elif self.INPUT_METHOD == 'arduino':
            pass


    def click_mouse(self):
        """Clicks mouse at current location."""
        if self.INPUT_METHOD == 'virtual':
            time.sleep(1 + random.uniform(self.REACTION_TIME_RANGE[0], self.REACTION_TIME_RANGE[1]))
            try:
                mouse.click()
            except Exception:
                logger.warning('Failed to click mouse')
            time.sleep(1 + random.uniform(self.REACTION_TIME_RANGE[0], self.REACTION_TIME_RANGE[1]))
        elif self.INPUT_METHOD == 'interception':
            self.click_mouse_driver()
        elif self.INPUT_METHOD == 'arduino':
            pass


    def press_key(self, key):
        """Presses key based on input type."""
        logger.info(f'Pressing key: {key}')
        if self.INPUT_METHOD == 'virtual':
            pg.keyDown(key)
            time.sleep(random.uniform(self.REACTION_TIME_RANGE[0], self.REACTION_TIME_RANGE[1]))
            pg.keyUp(key)
        elif self.INPUT_METHOD == 'interception':
            self.press_key_driver(key)
        elif self.INPUT_METHOD == 'arduino':
            pass


    def get_driver_mouse(self):
        """Returns the first mouse device"""
        # loop through all devices and return the first mouse.
        mouse = None
        for i in range(MAX_DEVICES):
            if interception.is_mouse(i):
                logger.success(f'Found mouse: {i}')
                mouse = i
                return mouse
        # exit if we can't find a mouse.
        if (mouse == None):
            logger.critical("No mouse found. Contact Gavin and change input method.")
            exit(1)


    def get_driver_keyboard(self):
        """Returns the first keyboard device"""
        keyboard = None
        # loop through all devices and return the first keyboard.
        for i in range(MAX_DEVICES):
            logger.debug(i)
            if interception.is_keyboard(i):
                logger.success(f'Found keyboard: {i}')
                keyboard = i
                return keyboard
        # Exit if we can't find a keyboard.
        if (keyboard == None):
            logger.critical("No keyboard found. Contact Gavin and change input method.")
            exit(2)


    def move_mouse_driver(self, x, y):
        """Moves the mouse to the screen coordinates and right clicks."""
        # we create a new mouse stroke, initially we use set right button down, we also use absolute move,
        # and for the coordinate (x and y) we use center screen
        mstroke = mouse_stroke(interception_mouse_state.INTERCEPTION_MOUSE_MOVE.value,
                                interception_mouse_flag.INTERCEPTION_MOUSE_MOVE_ABSOLUTE.value,
                                0,
                                int((0xFFFF * x) / self.screen_width),
                                int((0xFFFF * y) / self.screen_height),
                                0)
        self.driver.send(self.mouse_driver,mstroke) # Move mouse


    def click_mouse_driver(self):
        """Moves the mouse to the screen coordinates and right clicks."""
        # we create a new mouse stroke, initially we use set right button down, we also use absolute move,
        # and for the coordinate (x and y) we use center screen
        x, y = pg.position()
        mstroke = mouse_stroke(interception_mouse_state.INTERCEPTION_MOUSE_RIGHT_BUTTON_DOWN.value,
                                interception_mouse_flag.INTERCEPTION_MOUSE_MOVE_ABSOLUTE.value,
                                0,
                                int((0xFFFF * x) / self.screen_width),
                                int((0xFFFF * y) / self.screen_height),
                                0)
        self.driver.send(self.mouse_driver,mstroke) # we send the key stroke, now the right button is down
        # Add quick sleep so it's not instant
        time.sleep(random.uniform(self.REACTION_TIME_RANGE[0], self.REACTION_TIME_RANGE[1]))
        mstroke.state = interception_mouse_state.INTERCEPTION_MOUSE_RIGHT_BUTTON_UP.value # update the stroke to release the button
        self.driver.send(self.mouse_driver,mstroke) #button right is up


    def press_key_driver(self, hotkey):
        """Presses and releases the provided key"""
        hotkey_keycode = None
        # Check if hotkey is a special character requiring `shift + hotkey`
        if hotkey in self.KEY_MAP.keys():
            # Get number key that the hotkey maps to.
            hotkey_without_shift = self.KEY_MAP.get(hotkey)
            hotkey_keycode = KEYBOARD_MAPPING[hotkey_without_shift]
        # Check if hotkey is uppercase (requires shift + hotkey)
        elif hotkey.isupper():
            hotkey_keycode = KEYBOARD_MAPPING[hotkey.lower()]
        # If we set hotkey_keycode then we know we need to use `shift`
        if hotkey_keycode:
            # Shift key down
            driver_press = key_stroke(KEYBOARD_MAPPING['shift'], interception_key_state.INTERCEPTION_KEY_DOWN.value, 0)
            self.driver.send(self.keyboard_driver, driver_press)
        else:
            # hotkey_keycode not set so shift isn't required
            hotkey_keycode = KEYBOARD_MAPPING[hotkey]
        # Key down
        driver_press = key_stroke(hotkey_keycode, interception_key_state.INTERCEPTION_KEY_DOWN.value, 0)
        self.driver.send(self.keyboard_driver, driver_press)
        # Add quick sleep so it's not instant
        time.sleep(random.uniform(self.REACTION_TIME_RANGE[0], self.REACTION_TIME_RANGE[1]))
        # Key up
        driver_press.state = interception_key_state.INTERCEPTION_KEY_UP.value
        self.driver.send(self.keyboard_driver, driver_press)
        # try to release shift key
        # probably not the best way to do this
        try:
            driver_press = key_stroke(KEYBOARD_MAPPING['shift'], interception_key_state.INTERCEPTION_KEY_UP.value, 0)
            self.driver.send(self.keyboard_driver, driver_press)
        except Exception:
            # I imagine we only hit this if shift key isn't pressed down.
            # Don't have to do anything.
            pass
