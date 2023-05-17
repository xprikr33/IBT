#----------------------------------------------------#
#Program pro automatické hrani hry Solitaire Klondike#
#Stanislav Přikryl (xprikr33)                        #
#2023                                                #
#----------------------------------------------------#
import solitaire_detection as sd
import solitaire_solve as ss

#Spustí hru AisleRiot Solitaire a přepne ji do režimu celé obrazovky
sd.start_solitaire()

#Získá souřadnice a rozměr okna hry
sd.get_location_of_solitaire_window()

#Získá poměry rozlišení
sd.get_resolution_ratios()

#Inicializace struktury pro herní plochu
game_board = sd.game_board_init()

#První skenování herní plochy před provedením prvního tahu
game_board, uncovered_cards, cards_to_remove, secret_cards = sd.first_scan(game_board)

#První inicializace herní polochy před provedením prvního tahu
game_board = sd.first_init(game_board, uncovered_cards)

#Odstraní nalezených karet ze seznamu nenalezených karet
secret_cards = [card for card in secret_cards if card not in cards_to_remove]

#Samotné odehrání hry
game_board = ss.play_game(game_board, secret_cards)