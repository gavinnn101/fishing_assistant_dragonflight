import cv2 as cv
from datetime import datetime
import numpy as np
import sys
from mss import mss
from pyHM import mouse
import pyautogui as pg
from win32gui import FindWindow, GetWindowRect, GetClientRect, SetForegroundWindow
from loguru import logger
import random
import time
from util import get_duration


##################
# User Variables #
##################
DEBUG = True
INPUT_METHOD = 'virtual'
FISHING_HOTKEY = 'z'
MIN_CONFIDENCE = 0.50
TIMEOUT_THRESHOLD = 20  # Timeout in seconds
DIP_THRESHOLD = 7  # May need to adjust
##################
# User Variables #
##################

#####################
# Fishing variables #
#####################
template = cv.imread('bobber_dark.png', 0)
w, h = template.shape[::-1]
#####################
# Fishing variables #
#####################

#########################
# Game Client Variables #
#########################
game_window_name = "World of Warcraft"
game_window_class = "GxWindowClass"
game_window_handle = FindWindow(game_window_class, game_window_name)
game_window_rect = GetWindowRect(game_window_handle)  # left, top, right, bottom
game_size = GetClientRect(game_window_handle)

# # First set of offsets (30,8) will remove window title bar / border
# top_offset = 30
# bot_offset = 8
# Second set of offsets will only show middle of game window
top_offset = (game_size[2] // 2) - int((0.20 * game_size[2]))
bot_offset = (game_size[3] // 2) - int((0.30 * game_size[3]))
logger.info(f'Full Game Rect: {game_window_rect}')
game_window_rect = (
    game_window_rect[0] + bot_offset,
    game_window_rect[1] + top_offset,
    game_window_rect[2] - bot_offset,
    game_window_rect[3] - bot_offset
)
#########################
# Game Client Variables #
#########################


def find_bobber(screenshot, template):
    methods = ['cv.TM_CCOEFF_NORMED']  #, 'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED'
    match = cv.matchTemplate(screenshot, template, eval(methods[0]))
    results = cv.minMaxLoc(match) # (min_val, max_val, min_loc, max_loc)
    return (results[1], results[3]) # max_val, max_loc


def get_bobber_box(location):
    """Returns coordinates of box to watch around found bobber."""
    # Bobber coordinates
    top_left = location
    top_left = (top_left[0] - 20, top_left[1] - 20)  # position of box
    bottom_right = (top_left[0] + w + 40, top_left[1] + h + 20)  # size of box
    return (top_left, bottom_right)


def translate_coords(coords):
    """Translates game coords to screen coords."""
    return (coords[0] + w // 2 + game_window_rect[0], coords[1] + h // 2 + game_window_rect[1])


def move_mouse(x,y):
    """Moves cursor to x,y on screen."""
    if INPUT_METHOD == 'virtual':
        time.sleep(random.random())
        try:
            mouse.move(x,y)
        except Exception:
            logger.warning('Failed to move mouse')
        time.sleep(random.random())
    elif INPUT_METHOD == 'interception':
        pass
    elif INPUT_METHOD == 'arduino':
        pass

def click_mouse():
    """Clicks mouse at current location."""
    if INPUT_METHOD == 'virtual':
        time.sleep(1 + random.random())
        try:
            mouse.click()
        except Exception:
            logger.warning('Failed to click mouse')
        time.sleep(1 + random.random())
    elif INPUT_METHOD == 'interception':
        pass
    elif INPUT_METHOD == 'arduino':
        pass


def press_key(key):
    """Presses key(board input)."""
    logger.info(f'Pressing key: {key}')
    if INPUT_METHOD == 'virtual':
        pg.keyDown(key)
        time.sleep(random.random())
        pg.keyUp(key)
    elif INPUT_METHOD == 'interception':
        pass
    elif INPUT_METHOD == 'arduino':
        pass


def catch_fish(bobber_box):
    """Watches for change in bobber_y position and clicks when over threshold."""
    logger.info('Watching for catch')
    start_time = datetime.now()
    average_y_value = 0
    counter = 0
    total_y = 0
    box = (translate_coords(bobber_box[0]), translate_coords(bobber_box[1]))
    while get_duration(then=start_time, now=datetime.now(), interval='seconds') < TIMEOUT_THRESHOLD:
        with mss() as sct:
            # Take screenshot of the bobber_box area
            screenshot = sct.grab((box[0][0], box[0][1], box[1][0], box[1][1]))
            screenshot = cv.cvtColor(np.array(screenshot), cv.COLOR_BGR2GRAY)
            # Check that we found the bobber
            confidence, location = find_bobber(screenshot, template)
            logger.debug(f'Confidence: {confidence} | Location: {location}')
            if (confidence >= 0.30):
                # Get average y value
                counter += 1
                total_y += location[1]
                average_y_value = total_y // counter
                if DEBUG:
                    # Draw rectangle around bobber being tracked
                    bottom_right = (location[0] + w, location[1] + h)
                    cv.rectangle(screenshot, location, bottom_right, (0,255,0), 1)
                # Check if the new bobber_y_value is greater than our difference threshold
                logger.debug(f'Checking if {location[1]} - {average_y_value} >= {DIP_THRESHOLD}')
                if (location[1] - average_y_value >= DIP_THRESHOLD):
                    click_mouse()
                    break
        if DEBUG:
            cv.imshow('bobber debug', screenshot)
            key = cv.waitKey(1)
            if key == ord('q'):
                cv.destroyAllWindows()
                sys.exit()


def main():
    if not DEBUG:
        # Set log level to INFO
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    logger.info('Setting game window to foreground.')
    SetForegroundWindow(game_window_handle)
    # Wait for game window to enter foreground before starting to fish
    time.sleep(1)
    while True:
        # Cast fishing rod
        press_key(FISHING_HOTKEY)
        # Wait for bobber to appear
        time.sleep(2 + random.random())
        with mss() as sct:
            # Grab Screenshot of game window
            screenshot = sct.grab(game_window_rect)
            screenshot = cv.cvtColor(np.array(screenshot), cv.COLOR_BGR2GRAY)
            # Check game for bobber
            confidence, location = find_bobber(screenshot, template)
            logger.debug(f'Confidence: {confidence}')
            # Show Game window if DEBUG is enabled
            if DEBUG:
                cv.imshow('WoW Debug', screenshot)
                key = cv.waitKey(1)
                if key == ord('q'):
                    cv.destroyAllWindows()
                    sys.exit()
            # Check if the match is above our confidence threshold
            if confidence >= MIN_CONFIDENCE:
                logger.success(f"Bobber Found | Confidence: {confidence} | location: {location}")
                # Get box coordinates to watch around bobber
                bobber_box = get_bobber_box(location)
                # Get screen coords of new bobber
                screen_coords = translate_coords(location)
                # Move mouse to bobber
                logger.success(f'Moving mouse to: location: {location} | screen_coords: {screen_coords}')
                move_mouse(screen_coords[0], screen_coords[1])
                # Wait for catch
                catch_fish(bobber_box)


main()
