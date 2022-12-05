import pyautogui as pg
import random
import time
from pyHM import mouse
from loguru import logger

class InputHelper:
    """Wrapper class to handle keyboard/mouse inputs based on input method."""
    def __init__(self, input_method, reaction_time_range, *args, **kwargs):
        self.INPUT_METHOD = input_method
        self.REACTION_TIME_RANGE = reaction_time_range
    

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
            pass
        elif self.INPUT_METHOD == 'arduino':
            pass


    def press_key(self, key):
        """Presses key(board input)."""
        logger.info(f'Pressing key: {key}')
        if self.INPUT_METHOD == 'virtual':
            pg.keyDown(key)
            time.sleep(random.uniform(self.REACTION_TIME_RANGE[0], self.REACTION_TIME_RANGE[1]))
            pg.keyUp(key)
        elif self.INPUT_METHOD == 'interception':
            pass
        elif self.INPUT_METHOD == 'arduino':
            pass