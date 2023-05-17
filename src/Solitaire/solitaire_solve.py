#----------------------------------------------------#
#Program pro automatické hrani hry Solitaire Klondike#
#Stanislav Přikryl (xprikr33)                        #
#2023                                                #
#----------------------------------------------------#
import time
import copy
import sys
import pyautogui
import json
import hashlib
import solitaire_detection as sd
import solitaire_printing as sp
import solitaire_get_moves as sgm

#Definice konstant
VALUE = 0
COLOR = 1
SUIT = 2

ACE = 1
KING = 13

HEARTS = 1
DIAMONDS = 2
LEAVES = 4

X = 0
Y = 1
WIDTH = 2
HEIGHT = 3

ADD = 0
REMOVE = 1

TABLEAU_KING = 0
TABLEAU = 1
TABLEAU_FOUNDATION = 2
STOCK_RET = 12
STOCK_NEW = 5
STOCK_DEEP_KING = 6
STOCK_DEEP = 7
STOCK_FOUNDATION = 8 
WASTE_KING = 9
WASTE_TABLEAU = 10
WASTE_FOUNDATION = 11
FROM_FOUNDATION = 4
FROM_FOUNDATION_KING = 3 

GAP_COLUMN_0_TO_7 = 61
GAP_COLUMN_8 = 52
GAP_COLUMN_9 = 46
GAP_COLUMN_10 = 41
GAP_COLUMN_11 = 37
GAP_COLUMN_12 = 33
GAP_COLUMN_13 = 31
GAP_COLUMN_14 = 28
GAP_COLUMN_15 = 26
GAP_COLUMN_16 = 24
GAP_COLUMN_17 = 23
GAP_COLUMN_18 = 22
GAP_COLUMN_19 = 20

cards_gap= {
    0: GAP_COLUMN_0_TO_7,
    1: GAP_COLUMN_0_TO_7,
    2: GAP_COLUMN_0_TO_7,
    3: GAP_COLUMN_0_TO_7,
    4: GAP_COLUMN_0_TO_7,
    5: GAP_COLUMN_0_TO_7,
    6: GAP_COLUMN_0_TO_7,  
    7: GAP_COLUMN_0_TO_7,
    8: GAP_COLUMN_8,  
    9: GAP_COLUMN_9,  
    10: GAP_COLUMN_10,  
    11: GAP_COLUMN_11,  
    12: GAP_COLUMN_12,  
    13: GAP_COLUMN_13,  
    14: GAP_COLUMN_14,  
    15: GAP_COLUMN_15,  
    16: GAP_COLUMN_16,  
    17: GAP_COLUMN_17,  
    18: GAP_COLUMN_18,  
    19: GAP_COLUMN_19,  
}

BOTTOM_CARD_Y = 383

redeals_left = 2
undo_count = []    

#Defincie funkcí
#-----------------------------------------------------------------------------------------------------------------
def get_coords_of_card(game_board, column, deep):
    """
    Získá souřadnice konkrétní karty nacházející se na tableau
    """

    number_of_cards = len(game_board['tableau'][column]['cards'])
    gap = cards_gap[number_of_cards] * sd.current_screen_resolution_ratio[1]
    x_coord = column * sd.column_width + sd.column_width // 2
    bottom_card_y = BOTTOM_CARD_Y * sd.current_screen_resolution_ratio[1]

    if deep == 0: 
        y_coord = (gap * (number_of_cards - 1)) + bottom_card_y
    else:
        want = number_of_cards - deep - 1
        y_coord = (gap * want) + bottom_card_y

    return x_coord, y_coord

def waste_update(game_board, card, operation):
    """
    Funkce aktualizující stav odkládací hromádky waste, na základě toho jestli na waste kartu odkládáme, 
    nebo jestli z ní kartu odebíráme pro provedení tahu
    """
    if operation == ADD:
        game_board['waste']['cards'].insert(0, card)
    elif operation == REMOVE:
        game_board['waste']['cards'].pop()

    return game_board

def stock_update(game_board, ret): 
    """
    Funkce aktualizující stav zásobníku zbylých karet stoc, na základě toho jestli se ze zásobníku karta odebírá na waste,
    nebo jestli se vrací hromádka waste na stock
    """     
    if ret == True:
        game_board['stock']['cards'] += game_board['waste']['cards'][::-1]
        game_board['waste']['cards'] = []
    else:    
        game_board['stock']['cards'].pop()

    return game_board

def scan_new_waste(game_board):
    """
    Funkce obsluhující skenování nové karty ze zásobníku stock, která byla přetočena na hrmomádku waste
    """
    w_reg = game_board['waste']['region']
    w_reg_corr = (w_reg[X] + sd.window_size[X], w_reg[Y], w_reg[WIDTH], w_reg[HEIGHT])
    screenshot = sd.get_screenshot(w_reg_corr)
    
    new_card_name = sd.scan_card(screenshot, hidden_cards)

    card = sd.get_all_informations_about_found_card(new_card_name)

    game_board = waste_update(game_board ,card, ADD)

    game_board = stock_update(game_board, False)

    return game_board

def move_cards(from_x, from_y, to_x, to_y):
    """
    Přesun karet z jednoho místa na druhé
    """
    pyautogui.moveTo(from_x + sd.window_size[X],from_y, 0.2)
    pyautogui.dragTo(to_x + sd.window_size[X], to_y, 0.2,button="left")

def click_stock(game_board):
    """
    Funkce obsluhující přetočení karty ze zásobníku stock na waste
    """
    pyautogui.hotkey('ctrl', 'd')
    time.sleep(0.2)

    #Byla odhalena neznámá karta
    if game_board['stock']['cards'][-1][VALUE] == None:
        game_board = scan_new_waste(game_board)

    #Přetáčíme karty z waste zpět na zásobník stock
    elif game_board['stock']['cards'][-1][VALUE] == "ret":
        if redeals_left != 0:
            game_board = stock_update(game_board, True)
        else:
            game_board = game_board

    #Přetáčím již známou kartu na waste
    else:
        card = game_board['stock']['cards'].pop(1)
        game_board = waste_update(game_board, card, ADD)

    return game_board

def scan_tableau_column(game_board, column):  
    """
    Funkce provádějící skenování sloupce na tableau
    """
    #Sloupec je prázdný, skenování není potřebné
    if len(game_board['tableau'][column]['cards']) == 0:
        return game_board
    #Je odhalena nová karta, potřebuji skenovat
    elif game_board['tableau'][column]['cards'][-1][VALUE] == None:
        game_board = game_board 
    #Není odhalena nová karta, skenování není potřebné
    else:
        return game_board

    t_reg = game_board['tableau'][column]['region']
    t_reg_corr = (t_reg[X] + sd.window_size[X], t_reg[Y], t_reg[WIDTH], t_reg[HEIGHT])

    screenshot = sd.get_screenshot(t_reg_corr)
    
    new_card_name = sd.scan_card(screenshot, hidden_cards)

    card = sd.get_all_informations_about_found_card(new_card_name)

    game_board['tableau'][column]['cards'].pop()
    game_board['tableau'][column]['cards'].append(card)

    return game_board

def foundation_update(game_board, card):
    """
    Funkce která vkládá kartu na příslušnou vykládací hromádku foundation
    Tato funkce provádí úpravu struktury herní plochy
    """
    suit = sd.number_to_symbol(card[SUIT])
    foundation = game_board['foundations'][suit]
    foundation.append(card)

    return game_board

def make_move_to_correct_foundation(game_board, column, suit):
    """
    Funkce provádějící přesun karty z vrcholu sloupce z tableau nebo z waste na příslušnou hromádku foundation
    Tato funkce provádí tah ve hře
    """
    if suit == "H":
        coords = sd.hearths_foundation_coords
    elif suit == "C":
        coords = sd.clubs_foundation_coords
    elif suit == "D":
        coords = sd.diamonds_foundation_coords
    else:
        coords = sd.leaves_foundation_coords

    if column == "waste":
        move_cards(game_board['waste']['coords'][X], game_board['waste']['coords'][Y],
             coords[X], coords[Y])
    else:
        coord_x, coord_y = get_coords_of_card(game_board, column, 0)
        move_cards(coord_x, coord_y,
             coords[X], coords[Y])        

def make_move_from_foundation(game_board, column, suit):
    """
    Funkce provádějící přesun karty z vrcholu vykládací hromádky foundation na vrchol sloupce na tableau
    Tato funkce provádí tah ve hře
    """
    if suit == "H":
        coords = sd.hearths_foundation_coords
    elif suit == "C":
        coords = sd.clubs_foundation_coords
    elif suit == "D":
        coords = sd.diamonds_foundation_coords
    else:
        coords = sd.leaves_foundation_coords

    coord_x, coord_y = get_coords_of_card(game_board, column, 0)
    move_cards(coords[X], coords[Y], coord_x, coord_y)   

def move_card_to_foundation(game_board, move):
    """
    Funkce obsluhující tah TABLEAU_FOUNDATION (Přesun karty z tableau na foundation)
    """
    column = move[1][0]
    suit = move[1][1]

    make_move_to_correct_foundation(game_board, column, suit)

    card = game_board['tableau'][column]['cards'].pop()

    game_board = scan_tableau_column(game_board, column)

    game_board = foundation_update(game_board, card)

    return game_board

def move_king_on_tableau(game_board, move):
    """
    Funkce obsluhující tah TABLEAU_KING (Přesun karty krále z tableau na prázdný sloupec)
    """
    from_column = move[1][0]
    to_column = move[1][1]

    deep = len(game_board['tableau'][from_column]['cards']) - move[2] - 1

    from_x, from_y = get_coords_of_card(game_board, from_column, deep)
    to_x, to_y = get_coords_of_card(game_board, to_column, 0)

    move_cards(from_x, from_y, to_x, to_y)

    cards_to_move = []

    for i in range(deep + 1):
        cards_to_move.append(game_board['tableau'][from_column]['cards'].pop())

    game_board = scan_tableau_column(game_board, from_column)

    cards_to_move.reverse()

    for card in cards_to_move:
        game_board['tableau'][to_column]['cards'].append(card)

    return game_board

def move_cards_on_tableau(game_board, move):
    """
    Funkce obsluhující tah TABLEAU(Přesun karty/karet ze jednoho sloupce na jinýc sloupec na tableau)
    """
    from_column = move[1][0]
    to_column = move[1][1]

    deep = len(game_board['tableau'][from_column]['cards']) - move[2] - 1

    from_x, from_y = get_coords_of_card(game_board, from_column, deep)
    to_x, to_y = get_coords_of_card(game_board, to_column, 0)

    move_cards(from_x, from_y, to_x, to_y)

    cards_to_move = []

    for i in range(deep + 1):
        cards_to_move.append(game_board['tableau'][from_column]['cards'].pop())

    game_board = scan_tableau_column(game_board, from_column)

    cards_to_move.reverse()

    for card in cards_to_move:
        game_board['tableau'][to_column]['cards'].append(card)

    return game_board

def move_king_from_foundation(game_board, move):
    """
    Funkce obsluhující tah FROM_FOUNDATION_KING (Přesun karty krále z vrcholu hromádky foundation na prázdný sloupec na tableau)
    """
    to_column = move[1][1]
    suit = move[1][0]

    make_move_from_foundation(game_board, to_column, suit)

    foundation = game_board['foundations'][suit]
    card_to_move = foundation.pop()

    game_board['tableau'][to_column]['cards'].append(card_to_move)

    return game_board

def move_card_from_foundation(game_board, move):
    """
    Funkce obsluhující tah FROM_FOUNDATION (Přesun karty z vrcholu foundation na vrchol sloupce na tableau)
    """
    to_column = move[1][1]
    suit = move[1][0]

    make_move_from_foundation(game_board, to_column, suit)

    foundation = game_board['foundations'][suit]
    card_to_move = foundation.pop()

    game_board['tableau'][to_column]['cards'].append(card_to_move)

    return game_board

def move_king_from_stock(game_board, move):
    """
    Funkce obsluhující tah STOCK_DEEP_KING (Přesun karty krále ze zásobníku stock)
    """
    depth = move[2]

    if depth != 0:
        for x in range(depth):
            game_board = click_stock(game_board)

    game_board = move_king_from_waste(game_board, (move[0], move[1], 0))

    return game_board

def move_card_from_stock(game_board, move):
    """
    Funkce obsluhující tah STOCK_DEEP (Přesun karty ze zásobníku stock na tableau)
    """
    depth = move[2]

    if depth != 0:
        for x in range(depth):
            game_board = click_stock(game_board)

    game_board = move_card_from_waste_to_tableau(game_board, (move[0], move[1], 0))

    return game_board

def move_card_from_stock_to_foundation(game_board, move):
    """
    Funkce obsluhující tah STOCK_DEEP_FOUNDATION (Přesun karty ze zásobníku stock na foundation)
    """
    depth = move[2]

    if depth != 0:
        for x in range(depth):
            game_board = click_stock(game_board)

    game_board = move_card_from_waste_to_foundation(game_board, (move[0], move[1], 0))

    return game_board

def move_king_from_waste(game_board, move):
    """
    Funkce obsluhující tah WASTE_KING (Přesun karty krále z waste)
    """
    to_column = move[1]
    depth = move[2]

    if depth != 0:
        for x in range(depth):
            game_board = click_stock(game_board)

    from_x, from_y = game_board['waste']['coords']
    to_x, to_y  = get_coords_of_card(game_board, to_column, 0)
    move_cards(from_x, from_y, to_x, to_y)

    card_to_move = game_board['waste']['cards'].pop(0)

    game_board['tableau'][to_column]['cards'].append(card_to_move)

    return game_board

def move_card_from_waste_to_tableau(game_board, move):
    """
    Funkce obsluhující tah WASTE_TABLEAU (Přesun karty z waste na tableau)
    """
    to_column = move[1]
    depth = move[2]

    if depth != 0:
        for x in range(depth):
            game_board = click_stock(game_board)

    from_x, from_y = game_board['waste']['coords']
    to_x, to_y  = get_coords_of_card(game_board, to_column, 0)
    move_cards(from_x, from_y, to_x, to_y)

    card_to_move = game_board['waste']['cards'].pop(0)

    game_board['tableau'][to_column]['cards'].append(card_to_move)

    return game_board

def move_card_from_waste_to_foundation(game_board, move):
    """
    Funkce obsluhující tah WASTE_FOUNDATION (Přesun karty z waste na foundation)
    """
    suit = move[1]
    depth = move[2]

    if depth != 0:
        for x in range(depth):
            game_board = click_stock(game_board)

    card_to_move = game_board['waste']['cards'].pop(0)
    make_move_to_correct_foundation(game_board, "waste", suit)
    foundation_update(game_board, card_to_move)

    return game_board

def game_board_hash(game_board):
    """
    Funkce která převede slovník herní plochy na string, ze kterého se následně vytvoří hash který vrací
    """
    game_board_string = json.dumps(game_board, sort_keys=True)
    return hashlib.sha256(game_board_string.encode('utf-8')).hexdigest()

def is_final_state(game_board):
    """
    Funkce která zjistí z aktuálního stavu herní plochy, jestli se nejedná o stav cílový
    """
    for suit, cards in game_board['foundations'].items():
        if len(cards) == 13:
            continue
        else:
            return False
        
    return True

def do_move(game_board, best_move):
    """
    Funkce obsluhující provádění jednotlivých tahů
    """
    global redeals_left
    global undo_count

    move_name = best_move[0][0]

    if move_name == TABLEAU_FOUNDATION:
        new_game_board = move_card_to_foundation(game_board, best_move)
        undo_count.append((1, False))

    elif move_name == TABLEAU_KING:

        from_column = best_move[1][0]

        count_of_cards_to_move = len(game_board['tableau'][from_column]['cards'])

        if (count_of_cards_to_move == best_move[2]):
            return None
        
        new_game_board = move_king_on_tableau(game_board, best_move)
        undo_count.append((1, False))

    elif move_name == TABLEAU:

        from_column = best_move[1][0]
        to_column = best_move[1][1]
        card_under = -1 + best_move[2]

        if (game_board['tableau'][from_column]['cards'][card_under][VALUE] ==
        game_board['tableau'][to_column]['cards'][-1][VALUE]):
            return None
        
        new_game_board = move_cards_on_tableau(game_board, best_move)
        undo_count.append((1, False))

    elif move_name == FROM_FOUNDATION_KING:
        new_game_board = move_king_from_foundation(game_board, best_move)
        undo_count.append((1, False))

    elif move_name == FROM_FOUNDATION:
        new_game_board = move_card_from_foundation(game_board, best_move)
        undo_count.append((1, False))

    elif move_name == STOCK_DEEP_KING:
        click = best_move[2]
        new_game_board = move_king_from_stock(game_board, best_move)
        undo_count.append((click + 1, False))

    elif move_name == STOCK_DEEP:
        click = best_move[2]
        new_game_board = move_card_from_stock(game_board, best_move)
        undo_count.append((click + 1, False))

    elif move_name == STOCK_FOUNDATION:
        click = best_move[2]
        new_game_board = move_card_from_stock_to_foundation(game_board, best_move)
        undo_count.append((click + 1, False))

    elif move_name == WASTE_KING:
        click = best_move[2]
        if click == 0:
            new_game_board = move_king_from_waste(game_board, best_move)
            undo_count.append((click + 1, False))
        else:
            new_game_board = move_king_from_waste(game_board, best_move)
            undo_count.append((click + 1, True))
            redeals_left -= 1
            
    elif move_name == WASTE_TABLEAU:
        click = best_move[2]
        if click == 0:
            new_game_board = move_card_from_waste_to_tableau(game_board, best_move)
            undo_count.append((click + 1, False))
        else:
            new_game_board = move_card_from_waste_to_tableau(game_board, best_move)
            undo_count.append((click + 1, True))
            redeals_left -= 1

    elif move_name == WASTE_FOUNDATION:
        click = best_move[2]
        if click == 0:
            new_game_board = move_card_from_waste_to_foundation(game_board, best_move)
            undo_count.append((click + 1, False))
        else:
            new_game_board = move_card_from_waste_to_foundation(game_board, best_move)
            undo_count.append((click + 1, True))
            redeals_left -= 1

    elif move_name == STOCK_NEW:
        new_game_board = click_stock(game_board)
        undo_count.append((1, False))

    elif move_name == STOCK_RET:

        if redeals_left == 0:
            print("Nelze znovu procházet balíček zbylých karet!")
            new_game_board = None
        else:
            print(f"Přetáčím karty z balíčku waste na balíček stock, zbývá {redeals_left} pretočení")
            new_game_board = click_stock(game_board)
            redeals_left -= 1
            undo_count.append((1, True))

    return new_game_board

def ret():
    """
    Funkce obsluhující vracení se na předchozí tahy
    """
    global undo_count
    global redeals_left
    undo = undo_count.pop()
    for x in range(undo[0]):
        click_return()

    if undo[1] == True:
        redeals_left += 1

def click_return():
    pyautogui.hotkey('ctrl', 'z')
    time.sleep(0.2)

def dfs_iter(init_node):
    """
    Funkce provádějící odehrání hry pomocí modifikovaného algoritmu DFS, který provádí iteračně
    """
    global undo_count
    open_list = [init_node]
    closed_list = set()

    #Hraje dokud nenajde cíl, nebo dokud neprojde všechny stavy hry
    while open_list:

        #Získá aktuální stav
        game_board, moves = open_list[-1]

        sp.print_game_board(game_board)
        sp.print_possible_moves(game_board, moves)

        #Ověří, jestli se nejedná o stav cílový
        if is_final_state(game_board):
            total_count_of_states = len(closed_list)
            return game_board, total_count_of_states
        
        #Pro aktuální stav hry nejsou žádné nevyzkoušené tahy, vrací se zpět
        if not moves:
            print("Pro tuto konfiguraci, jsem nenalezl žádné další tahy! Vracím se na předchozí tah!")
            open_list.pop()
            ret()
            continue

        #Vytvoří hash aktuálního stavu a vloží jej do množiny closed_list
        game_hash = game_board_hash(game_board)
        if game_hash not in closed_list:
            closed_list.add(game_board_hash(game_board))

        #Tvoří kopii herní plochy
        game_board_2 = copy.deepcopy(game_board)

        #Provede tah s nejlepším ohodnocením
        move = moves.pop(0)
        new_game_board = do_move(game_board_2, move)

        #Tah byl zbytečný a pokračuje další iterací
        if new_game_board == None:
            continue

        #Nachází li se v nové konfiguraci, doposud neprozkoumané, expanduje tímto směrem
        if game_board_hash(new_game_board) not in closed_list:
            new_moves = sgm.get_possible_moves(new_game_board)
            open_list[-1] = (game_board, moves)
            open_list.append((copy.deepcopy(new_game_board), new_moves))
        else:
            print("V této konfiguraci jsem se už nacházel, vracím se na předchozí tah!")
            ret()

    return None, None, None

def play_game(game_board, secret_cards): 
    """
    Funkce obsluhující odehrání hry
    """
    global hidden_cards
    global undo_count
    hidden_cards = secret_cards

    initial_game_board = game_board

    init_node = (copy.deepcopy(initial_game_board), sgm.get_possible_moves(initial_game_board))

    time_start = time.perf_counter()

    original_stdout = sys.stdout
    
    with open("game.log", "w") as file:
        sys.stdout = file
        res, total_count_of_states = dfs_iter(init_node)


    if res is not None:
        sys.stdout = original_stdout
        print("Řešení nalezeno! ", end="")
        time.sleep(2)
        pyautogui.press('left')
        pyautogui.press('enter')
        time_end = time.perf_counter()
        print(time_end - time_start, len(undo_count), total_count_of_states)
        exit(0)
    else:
        sys.stdout = original_stdout
        print("Řešení NEnalezeno! ", end="")
        time_end = time.perf_counter()
        print(time_end - time_start)
        pyautogui.hotkey('ctrl', 'w')
        exit(0)