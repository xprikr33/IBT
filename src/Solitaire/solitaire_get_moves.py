import solitaire_detection as sd
import solitaire_solve as ss

VALUE = 0
COLOR = 1
SUIT = 2

ACE = 1
KING = 13

UNKNOWNS = 0
FOUNDATIONS = 0
STOCKS = 0

WEIGHT_UNKNOWN = 0.5
WEIGHT_FOUNDATIONS = -2.0
WEIGHT_STOCK = 1.0

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

def is_opposite_color(card1, card2):
    """
    Funkce ověřuje, jestli mají 2 karty rozdílnou barvu
    """
    return card1[COLOR] != card2[COLOR]

def is_alternating_descending(card1, card2):
    """
    Funkce ověřuje, jestli má karta card1 hodnotu o 1 menší než karta card 2
    """
    if card1[VALUE] == "ret": return False
    return card1[VALUE] + 1 == card2[VALUE]

def can_move_to_foundation(card, foundation):
    """
    Funkce ověřuje, jestli mohu přesunout kartu na odpovídající vykládací hromádku foundation
    """
    if len(foundation) == 0 and card[VALUE] == ACE:
        buf = True
    elif len(foundation) > 0 and foundation[-1][VALUE] == card[VALUE] - 1:
        buf = True
    else:
        buf = False

    return buf

def get_unknown_count(game_board):
    """
    Funkce, která počítá počet neznámých karet na herní ploše
    """
    count = 0
    for card in game_board['stock']['cards']:
        if card[VALUE] == None:
            count += 1

    for column in game_board['tableau']:
        for card in column['cards']:
            if card[VALUE] == None:
                count += 1

    return count

def get_foundations_count(game_board):
    """
    Funkce, která počítá kolik karet je aktuálně vyloožených na hromádkách foundations
    """
    count = 0
    for suit, cards in game_board['foundations'].items():
        count += len(cards)

    return count

def get_stock_count(game_board):
    """
    Funkce která vrací počet karet na zásobníku stocku + hromádce waste
    """
    count = 0
    for card in game_board['stock']['cards']:
        if card[VALUE] == "ret":
            count = count
        else:
            count += 1

    for card in game_board['waste']['cards']:
        count += 1

    return count

def get_counts_for_heuristic(game_board):
    """
    Funkce, která získá všechny potřebné hodnoty pro výpočet heuristické funkce
    """
    unknown_count = get_unknown_count(game_board)
    foundations_count = get_foundations_count(game_board)
    stock_count = get_stock_count(game_board)

    return (unknown_count, foundations_count, stock_count)

def get_moves_on_tableau(possible_moves, game_board):
    """
    Získá množinu dostupných tahů, které lze provádět mezi sloupci na tableau
    """
    #Průchod přes všechny sloupce na tableau
    for i, column in enumerate(game_board['tableau']):
        
        # Sloupec je prázdný
        if not column['cards']:
            continue
        
        #Průchod přes všechny karty v prohledávaném sloupci
        for move_index in range(len(column['cards']) - 1, -1, -1):

            card_to_move = column['cards'][move_index]

            #Neprovádím tah s neznámou kartou
            if card_to_move[VALUE] == None:
                continue

            #Další průchod přes všechny sloupce, na které bude možné přesouvat kartu
            for j, target_column in enumerate(game_board['tableau']):

                #Vynechám stejný sloupec
                if i == j:
                    continue

                # Přesun krále na prázdný sloupec
                if not target_column['cards']:

                    # Pokud je karta král a nenachází se úplně na spod sloupce, přidáme tah
                    if card_to_move[VALUE] == KING and move_index != 0:  
                        
                        counts = get_counts_for_heuristic(game_board)
                        if column['cards'][move_index - 1][VALUE] == None:
                            heuristic = get_heuristic_value(counts[UNKNOWNS] - 1, counts[FOUNDATIONS], counts[STOCKS])  
                        else:                          
                            heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS], counts[STOCKS])
                        possible_moves.insert(0, ((TABLEAU_KING, heuristic),(i, j), move_index))

                    continue

                target_card = target_column['cards'][-1]

                #Vytvoření tahu, kde přesouvám kartu, nebo hromádku karet, mezi sloupci
                if is_opposite_color(card_to_move, target_card) and is_alternating_descending(card_to_move, target_card):

                    counts = get_counts_for_heuristic(game_board)
                    if column['cards'][move_index - 1][VALUE] == None:
                        heuristic = get_heuristic_value(counts[UNKNOWNS] - 1, counts[FOUNDATIONS], counts[STOCKS])  
                    else:                          
                        heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS], counts[STOCKS])
                    possible_moves.insert(0, ((TABLEAU, heuristic),(i, j), move_index))

    return possible_moves

def get_moves_on_foundation(possible_moves, game_board):
    """
    Získá množinu dostupných tahů, které lze provádět z vrcholů sloupců z tableau na vykládací hromádky foundations
    """
    #Průchod přes všechny sloupce na tableau
    for i, column in enumerate(game_board['tableau']):

        # Prázdný sloupec
        if not column['cards']:
            continue

        card_to_move = column['cards'][-1]

        #Průchod přes všechny vykládací hromádky foundations
        for suit, foundation in game_board['foundations'].items():

            card_to_move_suit = sd.number_to_symbol(card_to_move[SUIT])

            # Pokud má přesouvaná karta o 1 větší hodnotu, než karta na vrcholu příslušlé odkladové hromádky, 
            # jedná se o validní tah
            if card_to_move_suit == suit and can_move_to_foundation(card_to_move, foundation):

                counts = get_counts_for_heuristic(game_board)
                if len(column['cards']) == 1:
                    heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS] + 1, counts[STOCKS])
                elif column['cards'][-2][VALUE] == None:
                    heuristic = get_heuristic_value(counts[UNKNOWNS] - 1, counts[FOUNDATIONS] + 1, counts[STOCKS])  
                else:                          
                    heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS] + 1, counts[STOCKS])
                possible_moves.append(((TABLEAU_FOUNDATION, heuristic),(i , suit)))

    return possible_moves

def get_moves_from_foundation(possible_moves, game_board):
    """
    Získá množinu dostupných tahů, které lze provádět z vrcholů vykládacích hromádek z foundations na tableau
    """
    #Průchod přes všechny vykládací hromádky foundations
    for suit, foundation in game_board['foundations'].items():

        #Přeskočí prázdnou hromádku
        if not foundation:
            continue

        card_to_move = foundation[-1]

        #Průchod přes všechny sloupce na tableu
        for i, column in enumerate(game_board['tableau']):
            if not column['cards']:
                if card_to_move[VALUE] == KING:
                    counts = get_counts_for_heuristic(game_board)                        
                    heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS] - 1, counts[STOCKS])
                    possible_moves.append(((FROM_FOUNDATION_KING, heuristic), (suit, i)))

            else:
                target_card = column['cards'][-1]
                if is_opposite_color(card_to_move, target_card) and is_alternating_descending(card_to_move, target_card):
                    counts = get_counts_for_heuristic(game_board)
                    heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS] - 1, counts[STOCKS])
                    possible_moves.append(((FROM_FOUNDATION, heuristic), (suit, i)))

    return possible_moves

def get_moves_on_stock(possible_moves, game_board):
    """
    Získá množinu dostupných tahů, které lze provádět ze zásobníku zbylých karet stock
    """
    stock_flag = False

    #Průchod přes všechny karty v zásobníku zbylých karet stock
    for depth, stock_card in enumerate(game_board['stock']['cards']):

        if "ret" in stock_card and len(game_board['stock']['cards']) == 1 and ss.redeals_left != 0:
            counts = get_counts_for_heuristic(game_board)
            heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS], counts[STOCKS])
            possible_moves.append(((STOCK_RET, heuristic), "ret", "ret"))
            continue

        if len(game_board['stock']['cards']) == 1 and ss.redeals_left == 0:
            return possible_moves

        if None in stock_card:
            if stock_flag == False:
                counts = get_counts_for_heuristic(game_board)
                heuristic = get_heuristic_value(counts[UNKNOWNS] - 1, counts[FOUNDATIONS], counts[STOCKS])
                possible_moves.append(((STOCK_NEW, heuristic), None, None))
                stock_flag = True
            continue

        #Průchod přes sloupce na tableau
        for i, column in enumerate(game_board['tableau']):
            if not column['cards']:
                # Pokud je sloupec prázdný, přesunout lze pouze krále.
                if stock_card[0] == KING:
                    counts = get_counts_for_heuristic(game_board)
                    heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS], counts[STOCKS] - 1)
                    possible_moves.append(((STOCK_DEEP_KING, heuristic), i, depth))
            else:
                target_card = column['cards'][-1]
                if is_opposite_color(stock_card, target_card) and is_alternating_descending(stock_card, target_card):
                    counts = get_counts_for_heuristic(game_board)
                    heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS], counts[STOCKS] - 1)
                    possible_moves.append(((STOCK_DEEP, heuristic), i, depth))

        #Průchod přes vykládací hromádky foundations
        for suit, foundation in game_board['foundations'].items():
            
            card_to_move_suit = sd.number_to_symbol(stock_card[SUIT])

            if card_to_move_suit == suit and can_move_to_foundation(stock_card, foundation):

                counts = get_counts_for_heuristic(game_board)
                heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS] + 1, counts[STOCKS] - 1)
                possible_moves.append(((STOCK_FOUNDATION, heuristic), suit, depth))

    return possible_moves

def get_moves_on_waste(possible_moves, game_board):
    # Přesun karty z odklací hromádky na herní plochu
    if game_board['waste']['cards']:

        num_of_cards = len(game_board['waste']['cards'])

        for depth, waste_card in enumerate(game_board['waste']['cards']):

            if depth != 0:
                if ss.redeals_left == 0:
                    return possible_moves
                else:
                    depth = num_of_cards - depth + len(game_board['stock']['cards'])

            for i, column in enumerate(game_board['tableau']):

                if not column['cards']:
                    if waste_card[VALUE] == KING:
                        counts = get_counts_for_heuristic(game_board)
                        heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS], counts[STOCKS] - 1)
                        possible_moves.append(((WASTE_KING, heuristic), i, depth))

                else:

                    target_card = column['cards'][-1]

                    if is_opposite_color(waste_card, target_card) and is_alternating_descending(waste_card, target_card):
                        
                        counts = get_counts_for_heuristic(game_board)
                        heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS], counts[STOCKS] - 1)
                        possible_moves.append(((WASTE_TABLEAU, heuristic), i, depth))

            for suit, foundation in game_board['foundations'].items():
            
                card_to_move_suit = sd.number_to_symbol(waste_card[SUIT])

                if card_to_move_suit == suit and can_move_to_foundation(waste_card, foundation):

                    counts = get_counts_for_heuristic(game_board)
                    heuristic = get_heuristic_value(counts[UNKNOWNS], counts[FOUNDATIONS] + 1, counts[STOCKS] - 1)
                    possible_moves.append(((WASTE_FOUNDATION, heuristic), suit, depth))

    return possible_moves

def get_heuristic_value(unknown_cards_count, foundations_cards_count, stock_cards_count):
    """
    Vrací ohodnocení na základě počtu neznámých karet, počtu karet na stock + waste, počtu karet na foundations
    """
    return unknown_cards_count * WEIGHT_UNKNOWN + foundations_cards_count * WEIGHT_FOUNDATIONS + stock_cards_count * WEIGHT_STOCK

def get_possible_moves(game_board):
    """
    Funkce získávající všechny dostupné tahy pro aktuální konfiguraci herní plochy a jejich následné seřazení 
    na základě ohodnocení jednotlivých tahů
    """
    possible_moves = []
    possible_moves = get_moves_on_tableau(possible_moves, game_board)
    possible_moves = get_moves_on_foundation(possible_moves, game_board)
    possible_moves = get_moves_from_foundation(possible_moves, game_board)
    possible_moves = get_moves_on_stock(possible_moves, game_board)
    possible_moves = get_moves_on_waste(possible_moves, game_board)

    sorted_possible_moves = sort_possible_moves(possible_moves)

    return sorted_possible_moves

def sort_possible_moves(possible_moves):
    """
    Seřadí množinu dostupných tahů na základě jejich ohodnocení
    """
    sorted_possible_moves = sorted(possible_moves, key=sort_key, reverse=True)

    priority_count = sum(1 for move in sorted_possible_moves if move[0][0] == STOCK_RET)

    #Odstraní tah pro přetočení kartet z waste na stock, pokud je tento tah zbytečný
    if priority_count == 1:
        for move in sorted_possible_moves:
            if move[0][0] == STOCK_RET:
                sorted_possible_moves.remove(move)
                break

    return sorted_possible_moves
    
def sort_key(move):
    """
    Vrací ohodnocení, podle kterého je prováděno seřazování množiny tahů
    """
    return -move[0][1]
