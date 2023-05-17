#----------------------------------------------------#
#Program pro automatické hrani hry Solitaire Klondike#
#Stanislav Přikryl (xprikr33)                        #
#2023                                                #
#----------------------------------------------------#
import solitaire_detection as sd
import solitaire_solve as ss

#Definice konstan
VALUE = 0
COLOR = 1
SUIT = 2

HEARTH_SYMBOL = "\U00002661"
CLUBS_SYMBOL = "\U00002663"
DIAMONDS_SYMBOL = "\U00002662"
LEAVES_SYMBOL = "\U00002660"

#Definice funkcí
#----------------------------------------------------------------------------------------------------
def suit_to_symbol(suit):
    """
    Funkce převádějící číselnou hodnotu vykládací hromádky foundation na znak reprezentující symbol této hromádky
    """
    if suit == sd.HEARTS or suit == 'H': return HEARTH_SYMBOL
    elif suit == sd.CLUBS or suit == 'C': return CLUBS_SYMBOL
    elif suit == sd.DIAMONDS or suit == 'D': return DIAMONDS_SYMBOL
    else: return LEAVES_SYMBOL

def value_correction(value):
    """
    Funkce upravující hodnoty těch karet, jejichž hodnota není reprezentována číslem, ale znakem
    """
    if value == 1:
        return "A"
    elif value == 11:
        return "J"
    elif value == 12:
        return "Q"
    elif value == 13:
        return "K"
    else:
        return value

def print_stock(game_board):
    """
    Funkce zabezpečující tisk zásobníku zbylých karet stock
    """
    print("STOCK: ", end="")
    for card in game_board['stock']['cards']:
        if card[VALUE] == "ret":
            continue
        elif card[VALUE] == None:
            print("[ ?? ] ", end="")
            continue

        val = sd.num_to_chr(card[VALUE])
        suit = suit_to_symbol(card[SUIT])

        if val == "10": 
            print(f"[10{suit} ] ", end="")
        else:
            print(f"[ {val}{suit} ] ", end="")
    print()

def print_waste(game_board):
    """
    Funkce zabezpečující tisk odkládací hromádky waste
    """
    print("WASTE: ", end="")
    for card in game_board['waste']['cards']:

        val = sd.num_to_chr(card[VALUE])
        suit = suit_to_symbol(card[SUIT])

        if val == "10": print(f"[10{suit} ] ", end="")
        else: print(f"[ {val}{suit} ] ", end="")
    print()

def print_foundations(game_board):
    """
    Funkce zabezpečující tisk vykládacích hromádek foundations
    """
    print("FOUNDATIONS:")
    for suit, cards in game_board['foundations'].items():
        suit_to_print = suit_to_symbol(suit)
        print(f"{suit_to_print} : ", end= "")
        for card in cards:
            val = sd.num_to_chr(card[VALUE])
            suit = suit_to_symbol(card[SUIT])
            if val == "10":
               print(f" [10{suit} ]", end="")
            else:
                print(f" [ {val}{suit} ]", end="")
        print()

def print_tableaou(game_board):
    """
    Funkce zabezpečující tisk herních sloupců na tableau
    """
    max_column_length = max(len(column['cards']) for column in game_board['tableau'])
    print("TABLEAU:")
    for row in range(max_column_length):
        for column in game_board['tableau']:

            if row < len(column['cards']):
                card = column['cards'][row]

                if card[VALUE] is None:
                    print("[ ?? ]", end="  ")

                else:
                    suit = suit_to_symbol(card[SUIT])

                    if card[VALUE] == 10: 
                        print(f"[10{suit} ]", end="  ")

                    else:
                        val = sd.num_to_chr(card[VALUE])
                        print(f"[ {val}{suit} ]", end="  ")

            else:
                print(" " * 6, end="  ")

        print()

def print_game_board(game_board):
    """
    Funce zabezpečující tisk kompletní herní plochy
    """
    print("HERNÍ PLOCHA:")
    print_stock(game_board)
    print_waste(game_board)
    print_foundations(game_board)
    print_tableaou(game_board)
    print("\n\n\n")

def print_possible_moves(game_board, moves):
    """
    Funkce zabezpečující tisk množiny dostupných tahů
    """
    print("MOŽNÉ TAHY:")

    for move in moves:
        move_name = move[0]

        if move_name == ss.TABLEAU_KING:

            from_column = move[1][0]
            from_column_print = move[1][0] + 1
            to_column =  move[1][1]
            to_column_print = move[1][1] + 1
            if move[2] == 0:
                print(f"    - K z {from_column_print}. sloupce -> {to_column_print}. sloupec")
            else:
                num_of_cards = len(game_board['tableau'][from_column]['cards']) - move[2]
                print(f"    - K + {num_of_cards - 1} z {from_column_print}. sloupce -> {to_column_print}. sloupec")

        elif move_name == ss.TABLEAU:

            from_column_print = move[1][0] + 1
            from_column = move[1][0]
            to_column_print = move[1][1] + 1
            to_column = move[1][1]
            target_card = value_correction(game_board['tableau'][to_column]['cards'][-1][VALUE])
            target_card_symbol = suit_to_symbol(game_board['tableau'][to_column]['cards'][-1][SUIT])

            if move[2] == len(game_board['tableau'][from_column]['cards']) - 1:
                moving_card = value_correction(game_board['tableau'][from_column]['cards'][-1][VALUE])
                moving_card_symbol = suit_to_symbol(game_board['tableau'][from_column]['cards'][-1][SUIT])
                print(f"    - {moving_card}{moving_card_symbol} z {from_column_print}. sloupce -> {target_card}{target_card_symbol} na {to_column_print}. sloupci")

            else:
                num_of_cards = len(game_board['tableau'][from_column]['cards']) - move[2] - 1
                moving_card = value_correction(game_board['tableau'][from_column]['cards'][-num_of_cards][VALUE])
                moving_card_symbol = suit_to_symbol(game_board['tableau'][from_column]['cards'][-num_of_cards][SUIT])
                print(f"    - {moving_card} + {num_of_cards} z {from_column_print}. sloupce -> {target_card}{target_card_symbol} na {to_column_print}. sloupci")

        elif move_name == ss.TABLEAU_FOUNDATION:

            from_column_print = move[1][0] + 1
            from_column = move[1][0]
            card_to_move = value_correction(game_board['tableau'][from_column]['cards'][-1][VALUE])

            suit = move[1][1]
            foundation_symbol = suit_to_symbol(suit)
            print(f"    - {card_to_move}{foundation_symbol} z {from_column_print}. sloupce -> {foundation_symbol}")

        elif move_name == ss.FROM_FOUNDATION_KING:

            to_column = move[1][1] + 1
            suit = move[1][0]
            foundation_symbol = suit_to_symbol(suit)
            print(f"    - K{foundation_symbol} z {foundation_symbol} -> {to_column}. sloupec")

        elif move_name == ss.FROM_FOUNDATION:

            to_column = move[1][1] + 1
            suit = move[1][0]
            card_to_move = value_correction(game_board['foundations'][suit][-1][VALUE])
            foundation_symbol = suit_to_symbol(suit)
            print(f"    - {card_to_move}{foundation_symbol} z {foundation_symbol} -> {to_column}. sloupec")

        elif move_name == ss.STOCK_NEW:
            print(f"    - Nová karta")

        elif move_name == ss.STOCK_DEEP_KING:

            to_column = move[1] + 1
            deep = move[2]
            print(f"    - K ze STOCK -> {to_column}. sloupec ({deep}x klik)")

        elif move_name == ss.STOCK_DEEP:

            to_column = move[1] + 1
            deep = move[2]
            target_card = game_board['tableau'][to_column - 1]['cards'][-1]
            target_card_symbol = suit_to_symbol(target_card[SUIT])
            card_to_move = game_board['stock']['cards'][deep]
            moving_card_symbol = suit_to_symbol(card_to_move[SUIT])
            print(f"    - {value_correction(card_to_move[VALUE])}{moving_card_symbol} ze STOCK -> {value_correction(target_card[VALUE])}{target_card_symbol} na {to_column}. sloupci ({deep}x klik)")

        elif move_name == ss.STOCK_FOUNDATION:

            suit = move[1]
            foundation_symbol = suit_to_symbol(suit)
            deep = move[2]
            card_to_move = game_board['stock']['cards'][deep]
            print(f"    - {value_correction(card_to_move[VALUE])}{foundation_symbol} ze STOCK -> {foundation_symbol} ({deep}x klik)")

        elif move_name == ss.WASTE_KING:

            to_column = move[1] + 1
            deep = move[2]
            len_of_stock = len(game_board['stock']['cards'])
            position_of_card = deep - len_of_stock
            if deep == 0:
                card_to_move = game_board['waste']['cards'][0]
                card_to_move_symbol = suit_to_symbol(card_to_move[SUIT])
                print(f"    - K{card_to_move_symbol} z WASTE -> {to_column}. sloupec ({deep}x klik")
            else:
                card_to_move = game_board['waste']['cards'][position_of_card]
                card_to_move_symbol = suit_to_symbol(card_to_move[SUIT])
                print(f"    - K{card_to_move_symbol} z WASTE -> {to_column}. sloupec ({deep}x klik")

        elif move_name == ss.WASTE_TABLEAU:
            
            to_column = move[1] + 1
            deep = move[2]
            len_of_stock = len(game_board['stock']['cards'])
            position_of_card = deep - len_of_stock
            target_card = game_board['tableau'][to_column - 1]['cards'][-1]
            target_card_symbol = suit_to_symbol(target_card[SUIT])
            if deep == 0:
                card_to_move = game_board['waste']['cards'][0]
                card_to_move_symbol = suit_to_symbol(card_to_move[SUIT])
                print(f"    - {value_correction(card_to_move[VALUE])}{card_to_move_symbol} z WASTE -> {value_correction(target_card[VALUE])}{target_card_symbol} na {to_column}. sloupci ({deep}x klik)")
            else:
                card_to_move = game_board['waste']['cards'][position_of_card]
                card_to_move_symbol = suit_to_symbol(card_to_move[SUIT])
                print(f"    - {value_correction(card_to_move[VALUE])}{card_to_move_symbol} z WASTE -> {value_correction(target_card[VALUE])}{target_card_symbol} na {to_column}. sloupci ({deep}x klik)")

        elif move_name == ss.WASTE_FOUNDATION:

            suit = move[1]
            foundation_symbol = suit_to_symbol(suit)
            deep = move[2]
            len_of_stock = len(game_board['stock']['cards'])
            position_of_card = deep - len_of_stock
            if deep == 0:
                card_to_move = game_board['waste']['cards'][0]
                print(f"    - {value_correction(card_to_move[VALUE])}{foundation_symbol} z WASTE -> {foundation_symbol} ({deep}x klik)")
            else:
                card_to_move = game_board['waste']['cards'][position_of_card]
                print(f"    - {value_correction(card_to_move[VALUE])}{foundation_symbol} z WASTE -> {foundation_symbol} ({deep}x klik)")

        elif move_name == ss.STOCK_RET:
            print(f"    - Karty z WASTE na STOCK")

        else:
            print()
    print()