#---------------------------------------------#
#Program pro automatické hrani hry Hledání min#
#Stanislav Přikryl (xprikr33)                 #
#2023                                         #
#---------------------------------------------#
import pyautogui
import sys
import mines_game_detection as mgd
import mines_play as mp

#Zjistí velikost herního pole zadaného v parametrech uživatelem
args = mgd.get_game_info()

#Spustí hru GNOME Mines
mgd.open_mines()

#Získá souřadnice a velikost okna hry
mgd.get_location_of_mines_window()

#Spustí hru ve zvolené obtížnosti
mgd.start_game(args)

#Posune kurzor stranou, aby nenarušoval herní pole
pyautogui.FAILSAFE = False
pyautogui.moveTo(0, 300)

#Získá souřadnice a velikost herního pole
mgd.get_coordinates_of_matrix()

#Počáteční inicializace herního pole
matrix = mgd.init_matrix()

#Řešení hry
with open("game.log", "w") as file:
    sys.stdout = file
    mp.solve_mines(matrix)
