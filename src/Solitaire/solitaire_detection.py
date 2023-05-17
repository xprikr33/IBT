#----------------------------------------------------#
#Program pro automatické hrani hry Solitaire Klondike#
#Stanislav Přikryl (xprikr33)                        #
#2023                                                #
#----------------------------------------------------#
import subprocess
import time
import pyautogui
import cv2
import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck
import os
import numpy as np
from screeninfo import get_monitors

#Definice konstant sloužících pro zajištění přehlednosti kódu a funkčnosti programu na obrazovkách s různým rozlišením
REFERENCE_RES = (1920, 1080)

POSSIBLE_RES_0 = (1920, 1080)
POSSIBLE_RES_1 = (1680, 1050)
POSSIBLE_RES_2 = (1440, 900)
POSSIBLE_RES_3 = (1280, 1024)
POSSIBLE_RES_4 = (1280, 800)
POSSIBLE_RES_5 = (1280, 720)
POSSIBLE_RES_6 = (1024, 768)

possible_resolutions = {
    0: POSSIBLE_RES_0,
    1: POSSIBLE_RES_1,
    2: POSSIBLE_RES_2,
    3: POSSIBLE_RES_3,
    4: POSSIBLE_RES_4,
    5: POSSIBLE_RES_5,
    6: POSSIBLE_RES_6,
}

REFERENCE_RES_CARD_SIZE = (195, 304)

RES_0_CARD_SIZE = (195, 304)
RES_1_CARD_SIZE = (189, 296)
RES_2_CARD_SIZE = (160, 249)
RES_3_CARD_SIZE = (171, 268)
RES_4_CARD_SIZE = (140, 219)
RES_5_CARD_SIZE = (124, 194)
RES_6_CARD_SIZE = (134, 209)

card_resolutions = {
    0: RES_0_CARD_SIZE,
    1: RES_1_CARD_SIZE,
    2: RES_2_CARD_SIZE,
    3: RES_3_CARD_SIZE,
    4: RES_4_CARD_SIZE,
    5: RES_5_CARD_SIZE,
    6: RES_6_CARD_SIZE,    
}

REFERENCE_MARGIN = 50

RED = 0
BLACK = 1

VALUE = 0
COLOR = 1
SUIT = 2

HEARTS = 1
DIAMONDS = 2
CLUBS = 3
LEAVES = 4

ASCII_CORRECTION = 48
COORDS = 3
X = 0
Y = 1
WIDTH = 2
HEIGHT = 3


#Definice funkcí
#------------------------------------------------------------------------------------------------------------#
def start_solitaire():
    """
    Spustí hru Solitaire a přepne ji do režimu fullscreen
    """
    solitaire = subprocess.Popen(['sol'], shell=True)
    time.sleep(1)
    pyautogui.press('f11')

def get_location_of_solitaire_window():
    """
    Nainicializuje souřadnice okna hry
    """
    global window_size

    screen = Wnck.Screen.get_default()
    screen.force_update()
    window = screen.get_active_window()
    geometry = window.get_geometry()
    x, y = geometry.xp, geometry.yp

    window_size = (x, y, geometry.widthp, geometry.heightp)

def get_resolution_ratios():
    """
    Získá aktuální rozlišení monitoru, na kterém je spuštěná hra a nastaví 
    globální proměnné na hodnoty potřebné pro přemapování souřadnic a přeškálování
    obrázků karet
    """
    monitors = get_monitors()

    global current_resolution
    global current_card_size
    global current_screen_resolution_ratio
    global current_card_resolution_ratio

    for monitor in monitors:
        if (monitor.x <= window_size[X] < (monitor.x + monitor.width) and
            monitor.y <= window_size[Y] < (monitor.y + monitor.height)):
            current_resolution = (monitor.width, monitor.height)
            current_screen_resolution_ratio = (current_resolution[0] / REFERENCE_RES[0],
                                        current_resolution[1] / REFERENCE_RES[1])

    for index, res in possible_resolutions.items():
        if current_resolution == res:
            current_card_size = card_resolutions[index]
            current_card_resolution_ratio = current_card_size[1] / REFERENCE_RES_CARD_SIZE[1]
            return
        
    print("Obrazovka běží v nepodporovaném rozlišení!")
    exit(0)

def game_board_init():
    """
    Inicializace sturuktury pro ukládání stavu herní plochy
    """
    global column_width

    UNKNOWN_CARD = (None, None, None)
    MARGIN = REFERENCE_MARGIN * current_screen_resolution_ratio[1]
    top_margin = MARGIN + current_card_size[1]
    number_of_columns = 7
    column_width = current_resolution[0] // number_of_columns
    column_height = current_resolution[1] - top_margin

    initial_x = 0
    initial_y = top_margin
    column_positions = [(initial_x + i * column_width, initial_y) for i in range(number_of_columns)]

    global hearths_foundation_coords
    global clubs_foundation_coords
    global diamonds_foundation_coords
    global leaves_foundation_coords

    hearths_foundation_coords = (3 * column_width + column_width // 2, top_margin // 2)
    clubs_foundation_coords = (4 * column_width + column_width // 2, top_margin // 2)
    diamonds_foundation_coords = (5 * column_width + column_width // 2, top_margin // 2)
    leaves_foundation_coords = (6 * column_width + column_width // 2, top_margin // 2)


    game_board = {

        'tableau': [
            {
                'cards': [UNKNOWN_CARD] * i + [], 
                'region': (reg[X], reg[Y], column_width, column_height),
            } 
            for i, reg in enumerate(column_positions)
        ],

        'foundations': {
            'H': [],
            'C': [],
            'D': [],
            'L': []
        },

        'stock': {
                'cards': [("ret", "ret", "ret")] + [UNKNOWN_CARD] * 24
        },

        'waste': {
                'cards': [],
                'coords': (column_width + column_width // 2, top_margin //2),
                'region': (column_width, 0, column_width, top_margin+15)
        },
    }

    return game_board

def get_screenshot(reg):
    """
    Získá snímek obrazovky konkrétního regionu
    """
    time.sleep(0.3)
    screenshot = pyautogui.screenshot(region= reg)
    screenshot.save(f"screenshot.png")
    screenshot_gray = cv2.imread(f"screenshot.png", cv2.IMREAD_GRAYSCALE)
    return screenshot_gray

def get_card(card):
    """
    Získá snímek požadované karty a případně ji přeškáluje na aktuální rozlišení obrazovky
    """
    gray_card = cv2.imread(f"cards/{card}", cv2.IMREAD_GRAYSCALE)

    new_height = int(gray_card.shape[0] * current_card_resolution_ratio)
    new_width = int(gray_card.shape[1] * current_card_resolution_ratio)
    new_size = (new_width, new_height)
    resized_img = cv2.resize(gray_card, new_size, interpolation=cv2.INTER_AREA)

    return resized_img

def get_coords_of_card(loc, card):
    """
    Získá souřadnice nalezené karty
    """
    for pt in zip(*loc[::-1]):
            coor = (pt[0] + card.shape[1]//2, pt[1])

    return coor

def get_card_color_and_symbol(symbol):
    """
    Převádí písmeno symbolu na číslo barvy a číselo symbolu
    """
    if symbol == 'H': return RED, HEARTS
    elif symbol == 'D': return RED, DIAMONDS
    elif symbol == 'C': return BLACK, CLUBS
    elif symbol == 'L': return BLACK, LEAVES

def get_all_informations_about_found_card(card):
    """
    Získá barvu, symbol a hodnotu z názvu snímku karty
    """
    color, symbol = get_card_color_and_symbol(card.split()[0])
    val = card.split()[-1].split(".")[0]
    value = chr_to_num(val)

    return value, color, symbol

def chr_to_num(char):
    """
    Funkce převádějící hodnotu harty reprezentovanou znakem na číselnou hodnotu
    """
    num = None

    if char == 'A':
        num = 1
    elif char == 'J':
        num = 11
    elif char == 'Q':
        num = 12
    elif char == 'K':
        num = 13
    elif char == "10":
        num = 10
    else:
        num = ord(char) - ASCII_CORRECTION

    return num

def num_to_chr(num):
    """
    Funkce převádějící hodnotu harty reprezentovanou číslem na znak
    """
    char = None

    if num == 1:
        char = 'A'
    elif num == 11:
        char = 'J'
    elif num == 12:
        char = 'Q'
    elif num == 13:
        char = 'K'
    elif num == 10:
        char = '10'
    else:
        char = chr(num + ASCII_CORRECTION)

    return char

def number_to_symbol(number):
    """
    Funkce převádějící číslo vykládací hromádky foundation na odpovídající znak
    """
    if number == HEARTS:
        return 'H'
    elif number == DIAMONDS:
        return 'D'
    elif number == CLUBS:
        return 'C'
    elif number == LEAVES:
        return 'L'
    
def scan_card(screenshot, secret_cards):
    """
    Skenuje snímek obrazovky a hledá první novou kartu
    """
    for card in secret_cards:   

        card_template = get_card(card)
        result = cv2.matchTemplate(screenshot, card_template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= 0.93)

        if loc[0].size > 0:
            return card
        
    return None

def first_scan(game_board):
    """
    Funkce provádějící prvotní sken herní plochy, před provedením prvního tahu
    """
    secret_cards = os.listdir("cards")
    cards_to_remove = []
    uncovered_cards = []
    screenshot = get_screenshot(window_size)

    for card in secret_cards:   

        card_template = get_card(card)
        result = cv2.matchTemplate(screenshot, card_template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= 0.93)

        if loc[0].size > 0:

            coords = get_coords_of_card(loc, card_template)
            cards_to_remove.append(card)

            if card == "card.png":
                continue

            value, color, symbol = get_all_informations_about_found_card(card)
            uncovered_cards.append((value, color, symbol, coords))

    return game_board, uncovered_cards, cards_to_remove, secret_cards

def first_init(game_board, uncovered_cards):
    """
    První iniciaizace herní plochy před provedením prvního tahu
    """
    #Seřadí získané karty od nejlevější po tu nejvíce vpravo
    sorted_uncovered_cards = sorted(uncovered_cards, key=lambda card: card[COORDS][X])

    for i, card in enumerate(sorted_uncovered_cards):
        column = game_board['tableau'][i]
        column['cards'].append(card[:3])

    return game_board
