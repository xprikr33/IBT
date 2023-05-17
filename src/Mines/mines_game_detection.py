#---------------------------------------------#
#Program pro automatické hrani hry Hledání min#
#Stanislav Přikryl (xprikr33)                 #
#2023                                         #
#---------------------------------------------#
import argparse
import pyautogui
import cv2
import numpy as np
import time
import subprocess
import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck
import math
from PIL import Image
import mines_play as mp
import psutil

#Definice konstant
DONE = 1
X_CORRECTION = 12
Y_CORRECTION = 7
UNEXPLORED = 0
FULLY_EXPLORED = 1

#Konstanty, reprezentující RGB hodnotu jednotlivých typů políček
NOTHING = (222, 222, 220)
UNKNOWN = (186, 189, 182)
ONE = (221, 250, 195)
TWO = (236, 237, 191)
THREE = (237, 218, 180)
FOUR = (237, 195, 138)
FIVE = (247, 161, 162)
SIX = (254, 167, 133)
SEVEN = (255, 125, 96)
EIGHT = (255, 50, 60)
GAMEOVER = (136, 138, 133)
MINE = (204, 0, 0)


#Definice funkcí
#-----------------------------------------------------------------------------------------------------------------------#
def get_game_info():
    """
    Ověří argumenty příkazové řádky
    """
    parser = argparse.ArgumentParser(description="Spustí GNOME Mines a odehraje zvolenou obtížnost. POZOR! Je zapotřebí mít klavesnici přepnutou na anglickou")
    parser.add_argument("size", choices=["s", "m", "l"], help="Povinný argument pro velikost (s, m, l)")
    parser.add_argument("-d", "--debug", action="store_true", help="Volitelný argument '-d' pro výpis průběhu hry do souboru game.log")
    args = parser.parse_args()

    return args

def open_mines():
    """
    Spustí hru GNOME Mines
    """
    subprocess.Popen(['gnome-mines'], shell=True)
    time.sleep(1)

def get_location_of_mines_window():
    """
    Inicializuje souřadnice okna hry do globální proměnné window_size
    """
    global window_size

    screen = Wnck.Screen.get_default()
    screen.force_update()
    window = screen.get_active_window()
    geometry = window.get_geometry()
    x, y = geometry.xp, geometry.yp
    window_size = (x, y, geometry.widthp, geometry.heightp) 
    
def start_game(args):
    """
    Spustí hru v požadované obtížnosti, nainicializuje globální proměnné informující o rozměru herní plochy a počtu min
    """
    global dim_x, dim_y, debug, mines

    if args.size == 's':
        dim_x, dim_y = 8, 8
        mines = 10
        pyautogui.press('1')
    elif args.size == 'm':
        dim_x, dim_y = 16, 16
        mines = 40
        pyautogui.press('2')
    else:
        dim_x, dim_y = 30, 16
        mines = 99
        pyautogui.press('3')
    
    if args.debug:
        debug = True
    else:
        debug = False

    time.sleep(1)

def take_screenshot():
    screenshot = pyautogui.screenshot(region= window_size)
    screenshot.save("screenshot.png")

def get_coordinates_of_matrix():
    """
    Detekuje a nainicializuje souřadnice herní matice
    """
    global matrix_size

    take_screenshot()
    img = cv2.imread('screenshot.png')
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    #Detekuje hrany na snímku herního pole a zvýrazní je
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    #Ze získaných hran zvýrazní poze hrany herní matice a jednotliné hrany uloží do samostatných proměnných
    lines = cv2.HoughLinesP(edges, 1, math.pi/180, 100, minLineLength=200, maxLineGap=15)

    horizontal_line, vertical_line = get_edges_of_matrix(lines)

    #Získání souřadnic pro herní matici a následná inicializace těchto rozměrů do proměnné matrix_size
    top_left_x = vertical_line[2] + window_size[0]
    top_left_y = vertical_line[3] + window_size[1]
    width = horizontal_line[2] - top_left_x + window_size[0]
    height = horizontal_line[1] - top_left_y + window_size[1]
    matrix_size = (top_left_x, top_left_y, width, height)
    
def get_edges_of_matrix(lines):
    """
    Funkce pro nalezení nejnižší horizontální a nejlevější vertikální hrany

    Argumenty:
    lines (list): seznam horizontálních a vertikálních hran, každá hrana je zastoupena seznamem
        obsahujícím tuple souřadnic (x1, y1, x2, y2)

    Návratové hodnoty:
    horizontal_line (tuple): souřadnice nejspodnější horizontální hrany
    vertical_line (tuple): souřadnice nejlevější horizontální hrany
    """
    #Inicializace proměnných pro sledování souřadnic
    max_ver_y = 0
    min_ver_x = 1920
    max_hor_y = 0
    min_hor_x = 1920

    #Inicializace proměnných pro detekované hrany
    vertical_line = None
    horizontal_line = None

    #Iterace přes všechny hrany
    for line in lines:
        x1, y1, x2, y2 = line[0]

        #Kontrola, zda je hrana horizontální
        if y1 == y2:
            if y1 > max_hor_y or x1 < min_hor_x:
                max_hor_y = y1
                min_hor_x = x1
                horizontal_line = (x1, y1, x2, y2)
            continue

        #Kontrola, zda je hrana vertikální a aktualizace proměnných
        if y2 > max_ver_y or x2 < min_ver_x:
            max_ver_y = y2
            min_ver_x = x2
            vertical_line = (x1, y1, x1, y2)

    return horizontal_line, vertical_line

def init_matrix():
    """
    Funkce, která nainicializuje herní plochu do trojrozměrné matice
    """
    global rozmer_policka

    #Vytvoří troj rozměrnou matici pro uchování souřadnic políčka a jeho stavu
    matrix = np.zeros((dim_x, dim_y, 4), dtype=int)
    rozmer_policka = matrix_size[2] / dim_x

    #Iterace přes celou matici a inicializace souřadnic jednotlivých políček
    for i in range(dim_x):
        for j in range(dim_y):

            #Nastaví x a y souřadnice políčka, reprezentující jeho polohu na ploše
            matrix[i, j, 0] = matrix_size[0] + i * rozmer_policka + X_CORRECTION
            matrix[i, j, 1] = matrix_size[1] + j * rozmer_policka + Y_CORRECTION

            #Nastavení flagu souřadnice na "neprozkoumaná"
            matrix[i, j, 3] = UNEXPLORED

    #Inicializace stavu jednotlivých políček matice
    matrix = scan_matrix(matrix)

    return matrix

def scan_matrix(matrix):
    """
    Funkce, která zjištuje aktuální stav jednotlivých políček herního pole

    """
    screen = Image.open("screenshot.png")

    #Iterace přes každé neprozkoumané políčko herního pole
    for i in range(dim_x):
        for j in range(dim_y):

            if matrix[i, j, 3] == UNEXPLORED:
                
                x = matrix[i, j, 0]
                y = matrix[i, j, 1]

                #Zjištění stavu políčka dle jeho barvy
                pixel = screen.getpixel((x - window_size[0], y - window_size[1]))
                matrix[i, j, 2] = ord(get_meaning_of_field(pixel, matrix, (x, y)))

                #Flag odkrytého políčka se nastaví na hodnotu, která říká, že se toto políčko dále nemusí procházet
                if matrix[i, j, 2] == ord('0'):
                    matrix[i, j, 3] = FULLY_EXPLORED

    return matrix

def get_meaning_of_field(pixel, matrix, cord):
    """
    Funkce, která zjistí v jakém stavu se nachází konkrétní políčko, dle jeho barvy
    """
    if pixel == NOTHING:
        return '0'
    elif pixel == UNKNOWN:
        return '?'
    elif pixel == ONE:
        return '1'
    elif pixel == TWO:
        return '2'
    elif pixel == THREE:
        return '3'
    elif pixel == FOUR:
        return '4'
    elif pixel == FIVE:
        return '5'
    elif pixel == SIX:
        return '6'
    elif pixel == SEVEN:
        return '7'
    elif pixel == EIGHT:
        return '8'
    elif pixel == GAMEOVER or pixel == MINE:
        print("Šlápl jsem na minu...")
        pyautogui.hotkey('ctrl', 'q')
        exit(0)
    else:
        pyautogui.hotkey('ctrl', 'q')
        if is_game_running():
            time_end = time.perf_counter()
            print("Podařilo se hru dohrát v rekordním čase a zapsat se tak do tabulky 10ti nejrychlejších her!")
            pyautogui.press("tab")
            pyautogui.press("enter")
            end_game(time_end, matrix)
        elif is_mine():
            print("Šlápl jsem na minu...")
            exit(0)
        else:
            print("Neplatné pole!")
            exit(0)

def is_game_running():
    """
    Funkce sloužící k ověření, zda-li hra stále běží
    """
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == "gnome-mines":
            return True
    return False

def is_mine():
    """
    Detekuje, jestli se na poslednim snimku obrazovky nenachazi rozslapnuta mina
    """
    image = Image.open("screenshot.png")

    for x in range(image.width):
        for y in range(image.height):
            pixel = image.getpixel((x, y))
            if pixel == MINE:
                return True
            
    return False

def show_matrix(matrix):
    """
    Funkce, která tiskne grafickou reprezentaci aktuálního stavu herního pole
    """
    print()
    for i in range(dim_y):
        print("+---"*dim_x, end="")
        print("+")
        print("|", end=" ")
        for j in range(dim_x):
            print(f"{chr(matrix[j, i, 2])} |", end=" ")
        print()
    print("+---"*dim_x, end="")
    print("+")
    print()

def get_new_screen(matrix):
    """
    Funkce, aktualizuje stav herní plochy
    """
    take_screenshot()
    matrix = scan_matrix(matrix)
    return matrix

def end_game(time_end, matrix):
    print("Byly nalezeny všechny miny")
    print("Doba hry: ", round(time_end - mp.time_start, 3), end=" sekund")
    pyautogui.hotkey('ctrl', 'q')
    exit(0)
