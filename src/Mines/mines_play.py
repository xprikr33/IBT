#---------------------------------------------#
#Program pro automatické hrani hry Hledání min#
#Stanislav Přikryl (xprikr33)                 #
#2023                                         #
#---------------------------------------------#
import mines_game_detection as mgd
import pyautogui
import numpy as np
import time
import sympy
import itertools
from math import comb

#Definice konstant
ASCII_CORRECTION = 48
DONE = 1
UNKNOWN = ord('?') - ASCII_CORRECTION
ONE = ord('1') - ASCII_CORRECTION
EIGHT = ord('8') - ASCII_CORRECTION
FLAG = ord('F') - ASCII_CORRECTION

#Definice globálních proměnných
mines_count = 0
time_start = 0

#Definice funkcí
#-----------------------------------------------------------------------------------------------------------

def click_safe(matrix, x, y):
    """
    Funkce obsluhující kliknutí levého tlačítka myši na bezpečné políčko
    """
    pyautogui.leftClick(matrix[x, y, 0] + mgd.rozmer_policka//2, matrix[x, y, 1]+mgd.rozmer_policka//2)
    matrix = mgd.get_new_screen(matrix)
    return matrix

def click_flag(matrix, x, y):
    """
    Funkce obsluhující kliknutí pravého tlačítka myši, pokládající vlaječku na políčko s minou
    """
    global mines_count
    matrix[x, y, 2] = ord('F')
    mines_count += 1
    pyautogui.rightClick(matrix[x, y, 0] + mgd.rozmer_policka//2, matrix[x, y, 1]+mgd.rozmer_policka//2)
    return matrix

def click_safe_debug(matrix, x, y):
    """
    Stejná funkce jako click_safe(), ale s přidáním debugovacích výpisů
    """
    if x == None or y == None:
        exit(0)
    print("------------------------------------------------------------------")
    print()
    print(f"Odkrývám políčko na souřadnicích x:{x+1} y:{y+1}")
    print(f"Nalezeno {mines_count} min z {mgd.mines}")
    pyautogui.leftClick(matrix[x, y, 0] + mgd.rozmer_policka//2, matrix[x, y, 1]+mgd.rozmer_policka//2)
    matrix = mgd.get_new_screen(matrix)
    uncovered = get_uncovered_percentage(matrix)
    print(f"{uncovered}% políček je odkryto")
    mgd.show_matrix(matrix)
    return matrix

def click_flag_debug(matrix, x, y):
    """
    Stejná funkce jako click_flag(), ale s přidáním debugovacích výpisů
    """
    global mines_count
    mines_count += 1
    print("------------------------------------------------------------------")
    print()
    print(f"Našel jsem minu na souřadnicích x:{x+1} y:{y+1}")
    print(f"Nalezeno {mines_count} min z {mgd.mines}")
    matrix[x, y, 2] = ord('F')
    pyautogui.rightClick(matrix[x, y, 0] + mgd.rozmer_policka//2, matrix[x, y, 1]+mgd.rozmer_policka//2)
    uncovered = get_uncovered_percentage(matrix)
    print(f"{uncovered}% políček je odkryto")
    mgd.show_matrix(matrix)
    return matrix

def get_uncovered_percentage(matrix):
    """
    Funkce, která počítá procentuální hodnotu reprezentující počet odkrytých políček herního pole
    """
    counter = 0
    for i in range(mgd.dim_x):
        for j in range(mgd.dim_y):
            if matrix[i, j, 2] != ord('?'):
                counter += 1
    percentige = (counter/(mgd.dim_x*mgd.dim_y))*100
    
    return round(percentige, 2)

def solve_mines(matrix):
    """
    Funkce provádějící hlavní logiku hry
    """
    global time_start
    time_start = time.perf_counter()
    global mines_count

    #Flagy pro ověřování potřeby počítat pravděpodobnosti
    probability_mines = False
    probability_safe = False

    if mgd.debug: mgd.show_matrix(matrix)

    #Provedení prvního prvního odhalení políčka, doprostřed matice
    if mgd.debug: matrix = click_safe_debug(matrix, mgd.dim_x // 2, mgd.dim_y // 2)
    else: matrix = click_safe(matrix, mgd.dim_x // 2, mgd.dim_y // 2)


    matrix = mgd.get_new_screen(matrix) 
    if mgd.debug: mgd.show_matrix(matrix)

    #Cyklus, ve kterém se provádí odehrání hledání min, dokud není hra dohraná, popřípadě, dokud se nešlápne na minu
    while True:   

        #Hledání min a bezpečných políček
        matrix, probability_mines = find_easiest_mines(matrix)
        matrix, probability_safe = find_safe_fields(matrix)

        #Nalezli jsme všechny miny, hra končí
        if mgd.mines == mines_count:
            time_end = time.perf_counter()
            mgd.end_game(time_end, matrix)
            break

        #Počítání pravděpodobnosti, není-li v této iteraci odhalena ani mina ani bezpečné políčko
        if probability_mines == True and probability_safe == True:
            if mgd.debug: print("Počítám pravděpodobnosti výskytu min")

            #Samotné počítání pravděpodobností
            prob_matrix = calc_probs(matrix, mgd.mines - mines_count)

            #Převedení vlaječek pro přehledný výpis v matici procent
            prob_matrix = convert_percentage_flags(prob_matrix, matrix)

            if mgd.debug:print_probs(prob_matrix)

            #Označí se všechny 100% políčka s minami vlaječkou
            matrix, clicked = click_100_flag(prob_matrix, matrix)

            #Nebylo li označeno žádné políčko s minou, odkryje se políčko s nejnižší pravděpodobností výskytu miny
            if not clicked:
                matrix = click_best_safe(prob_matrix, matrix)

            matrix = mgd.get_new_screen(matrix)

            probability_mines = False
            probability_safe = False 

        if not mgd.debug: matrix = mgd.get_new_screen(matrix)

def find_easiest_mines(matrix):
    """
    Funkce hledající 100% miny, na základě prozkoumávání sousedů prohledávaného políčka
    """
    global mines_count
    found_mine = False
    buff = False

    #Průchod hením polem
    for i in range(mgd.dim_x):
        for j in range(mgd.dim_y):
            value = matrix[i, j, 2]
            
            #Přeskočí se políčka s hodnotou 0, neodhalená políčka, políčka označená vlaječkou a prozkoumaná políčka
            if (value != ord('0') or value != ord('?') or value != ord('F')) and matrix[i, j, 3] != DONE:

                #Průzkum sousedních políček a zjišťování, jestli se mezi zbylými neodkrytými políčky nenachází miny
                matrix, found_mine = explore_neighbours_mines(matrix, i, j)
                if found_mine == True:
                    buff == True

                if mines_count == mgd.mines:
                    mgd.scan_matrix(matrix)
                    finish_game(matrix)
                             

    if buff == False:
        return matrix, True

    return matrix, False

def explore_neighbours_mines(matrix, x, y):
    """
    Funkce, prozkoumávající sousední políčka konkrétního políčka. Zjišťuje, jestli je poček sousedních neodkrytých políček
    roven číslu na prozkoumávaném políčku, od kterého je odečten počet okolních vlaječek
    """
    global mines_count
    found_mine = False
    value = matrix[x, y, 2]
    unknown_count = 0

    #Průchod přes sousedy prozkoumávaného políčka a počítání sousedních neodkrytých políček + políček s vlaječkou
    for i in range(max(0, x-1), min(mgd.dim_x, x+2)):
        for j in range(max(0, y-1), min(mgd.dim_y, y+2)):

            #Vynechání sebe sama
            if i == x and j == y:
                continue

            #Je li sousední buňka neodkrytá, nebo je na ní vlaječka, přičti 1
            if matrix[i, j, 2] == ord('?') or matrix[i, j, 2] == ord('F'):
                unknown_count += 1

    #Je-li počet neznámých políček + políček s vlaječkou roven číslu políčka prozkoumávaného, jsou všechna neznámá políčka označena vlaječkou
    if unknown_count == value - ASCII_CORRECTION:

        #Průchod přes sousední políčlka
        for i in range(max(0, x-1), min(mgd.dim_x, x+2)):
            for j in range(max(0, y-1), min(mgd.dim_y, y+2)):

                #Vynechání sebe sama
                if i == x and j == y:
                    continue

                #Neprozkoumané sousední políčko se označí vlaječkou
                if matrix[i, j, 2] == ord('?'):
                    matrix[i, j, 3] = DONE
                    matrix[x, y, 3] = DONE

                    if mgd.debug: matrix = click_flag_debug(matrix, i, j)
                    else: click_flag(matrix, i, j)

                    found_mine = True
                
                if matrix[i, j, 2] == ord('F'):
                    continue

        return matrix, found_mine
    
    return matrix, found_mine

def find_safe_fields(matrix):
    """
    Funkce hledající 100% bezpečná políčka, na základě prozkoumávání sousedů prohledávaného políčka
    """
    found_safe = False
    buff = False

    #Průchod herním polem
    for i in range(mgd.dim_x):
        for j in range(mgd.dim_y):
            value = matrix[i, j, 2]
            
            #Přeskočí se políčka s hodnotou 0, neodhalená políčka, políčka označená vlaječkou a prozkoumaná políčka
            if (value != ord('0') or value != ord('?') or value != ord('F')) and matrix[i, j, 3] != DONE:

                #Průzkum sousedních políček a zjišťování, jestli počet sousedních vlaječek souhlasí s číslem na prozkoumávaném políčku
                matrix, found_safe = explore_neighbours_safe(matrix, i, j)
                if found_safe == True:
                    buff = True

            
    if buff == False:
        return matrix, True
    
    return matrix, False

def explore_neighbours_safe(matrix, x, y):
    """
    Funkce, prozkoumávající sousední políčka konkrétního políčka. Zjišťuje, jestli je poček sousedních políček s vlaječkou
    roven čísle na prozkoumávaném políčku, pokud tomu tak je, může bezpečně odkrýt  zbývající sousední neodhalená políčka
    """
    found_safe = False
    value = matrix[x, y, 2]
    flags_count = 0

    #Průchod přes sousední políčka
    for i in range(max(0, x-1), min(mgd.dim_x, x+2)):
        for j in range(max(0, y-1), min(mgd.dim_y, y+2)):

            #Vynechání sebe sama
            if i == x and j == y:
                continue
            
            #Počítání sousedních vlaječek
            if matrix[i, j, 2] == ord('F'):
                flags_count += 1

    #Sedí li číslo na prozkoumávaném políčku s počtem sousedních vlaječek, odkryje zbylé neprozkoumané políčka
    if flags_count == value - ASCII_CORRECTION:

        #Průchod přes sousední políčka
        for i in range(max(0, x-1), min(mgd.dim_x, x+2)):
            for j in range(max(0, y-1), min(mgd.dim_y, y+2)):

                #Vynechání sebe sama
                if i == x and j == y:
                    continue

                #Je-li sousední políčko neznámé, je odkryto
                if matrix[i, j, 2] == ord('?'):
                    matrix[x, y, 3] = DONE
                    if mgd.debug: matrix = click_safe_debug(matrix, i, j)
                    else: matrix = click_safe(matrix, i, j)
                    found_safe = True
                    
    return matrix, found_safe

def finish_game(matrix):
    """
    Funkce, obsluhující dohrání hry v případě, že jsme nalezli všechny miny
    """
    matrix = mgd.get_new_screen(matrix)

    #Průchod herním polem
    for i in range(mgd.dim_x):
        for j in range(mgd.dim_y):

            #Vyklikání všech zbylých neodkrytých políček jako bezpečná políčka
            if matrix[i, j, 2] == ord('?'):
                if mgd.debug: matrix = click_safe_debug(matrix, i, j)
                else: matrix = click_safe(matrix, i, j)

    #Ukončení hry
    time_end = time.perf_counter()
    mgd.end_game(time_end, matrix)

def convert_percentage_flags(prob_matrix, matrix):
    """
    Funkce sloužící k úpravě matice pravděpodobností tak, aby bylo při výpisu jasné, kde se již nacházejí vlaječky, a kde prozkoumaná políčka
    """
    for i in range(mgd.dim_x):
        for j in range(mgd.dim_y):
            if chr(matrix[i, j, 2]) == 'F':
                prob_matrix[j][i] = FLAG + 2*ASCII_CORRECTION
            if prob_matrix[j][i] == None:
                prob_matrix[j][i] = ord("N") + ASCII_CORRECTION
    return prob_matrix

def print_probs(matrix):
    """
    Funkce, provádějící tisk matice s pravděpodobnostmi
    """
    for y, row in enumerate(matrix):
        print("+-----"*mgd.dim_x, end="")
        print("+")
        print("|", end=" ")
        for x, cell in enumerate(row):

            if cell == ord("N") + ASCII_CORRECTION: print(f" N  |", end=" ")

            elif cell == FLAG + 2*ASCII_CORRECTION: print(f" F  |", end=" ")

            elif round(cell*100) < 100 and round(cell*100) > 9: print(f" {round(cell*100)} |", end=" ")

            elif round(cell*100) == 100: print("100 |", end=" ") 

            elif round(cell*100) <= 9: print(f" {round(cell*100)}  |", end=" ") 
        print()
    print("+-----"*mgd.dim_x, end="")
    print("+")
    print()

def click_100_flag(prob_matrix, matrix):
    """
    Funkce, která vykliká všechny 100% políčka s minami na základě výpočtu pravděpodobnosti
    """
    global mines_count
    clicked = False

    #Průchod maticí s procenty
    for y, row in enumerate(prob_matrix):
        for x, cell in enumerate(row):

            #Nachází li se mezi procenty políčko se 100% pravděpodobností, že se pod ním nachází mina, označí se vlaječkou
            if round(cell*100) == 100:
                if mgd.debug: matrix = click_flag_debug(matrix, x, y)
                else: click_flag(matrix, x, y)

                matrix[x, y, 3] = DONE
                if mgd.debug: matrix = mgd.get_new_screen(matrix)
                clicked = True
                if mines_count == mgd.mines:
                    mgd.scan_matrix(matrix)
                    finish_game(matrix)

                break

    return matrix, clicked

def click_best_safe(prob_matrix, matrix):
    """
    Funkce provádějící odhalení políčka s nejnižší pravděpodobností výskytu miny
    """
    min_probability = float('inf')
    min_coordinates = (None, None)

    #Průchod přes matici s pravděpodobnostmi
    for y, row in enumerate(prob_matrix):
        for x, cell in enumerate(row):

            if cell != None:
                probability = round(cell*100)
                if probability < min_probability:
                    min_probability = probability
                    min_coordinates = (x, y)

    if mgd.debug: matrix = click_safe_debug(matrix, min_coordinates[0], min_coordinates[1])
    else: matrix = click_safe(matrix, min_coordinates[0], min_coordinates[1])

    matrix[min_coordinates[0], min_coordinates[1], 3] = DONE

    return matrix

def convert_matrix_to_list_of_lists(matrix):
    """
    Funkce převádějící herní pole ze struktury vytvořené pomocí np.zeroes na strukturu seznam seznamů
    """
    new_matrix = np.zeros((mgd.dim_y, mgd.dim_x), dtype=int)

    for i in range(mgd.dim_x):
        for j in range(mgd.dim_y):
            new_matrix[j, i] = matrix[i, j, 2] - ASCII_CORRECTION

    new_matrix_list = new_matrix.tolist()
    return new_matrix_list

def gen_known_matrix():
    """
    Funkce která vytváří prázdnou matici o rozměrech aktuálního herního pole
    """
    matrix = []
    for i in range(mgd.dim_y):
        matrix.append([None] * mgd.dim_x)
    return(matrix)
#_________________________________________________________________________________________________________________________________________
#Zde začínají funkce převzaté z volně dostupného repoziráže, dostupného na: https://github.com/PedroKKr/Minesweeper-probability-calculator
#Funkce byly upraveny pro mnou definouvanou strukturu pro hení pole hledání min
#_________________________________________________________________________________________________________________________________________

def surrounds(coords):
    """
    Funkce, která vrací seznam souřadnic sousedních buněk nacházejících se v rozmezíí matice
    """
    y, x = coords[0], coords[1]

    neighbours = [(y + 1, x), (y + 1, x + 1), (y, x + 1), (y - 1, x), (y - 1, x - 1), (y, x - 1), (y + 1, x - 1),
                     (y - 1, x + 1)]
    surrounding_neighbours = []

    for sqr in neighbours:
        if is_inside(sqr):
            surrounding_neighbours.append(sqr)
    return(surrounding_neighbours)

def is_inside(coords):
    """
    Funkce, která kontoluje, jestli se políčko se souřadnicemi coords nachází v herním poli
    """
    if 0 <= coords[0] < mgd.dim_y and 0 <= coords[1] < mgd.dim_x:
        return (True)
    else:
        return (False)

def gen_groups(solution, parameters):
    """
    Funkce, rozkládající parametrické řešení soustavy lineárních rovnic do skupin parametrů, které se navzájem neovlivňují
    """

    groups = []
    for i in range(len(parameters)):
        groups.append([])
    for i,par in enumerate(parameters):
        groups[i].append(par)
        for eq in solution:
            if eq.coeff(par) != 0:
                for par2 in parameters:
                    if eq.coeff(par2) != 0 and par2!=par and par2 not in groups[i]:
                        groups[i].append(par2)
    for par in parameters:
        hasit = []
        for i,group in enumerate(groups):
            if par in group and group not in hasit:
                hasit.append(group)
        if len(hasit) > 1:
            newgroup = []
            for group in hasit:
                groups.remove(group)
                for par2 in group:
                    if par2 not in newgroup:
                        newgroup.append(par2)
            groups.append(newgroup)
    return(groups)

def foo(l,n):
    #Generuje všechny kombinace seznamu l symbolů o délce n
    yield from itertools.product(*([l] * n))

def get_fields_by_set_idea(actual_matrix, new_matrix):
    """
    Funkce která prochází sousedící dvojice políček a zjišťuje, jestli se mezi jejich neodhalenými políčky nenachází mina
    """
    border_fields = []

    #Průchod herním polem
    for y, row in enumerate(actual_matrix):
        for x, cell in enumerate(row):

            #Pokud políčko obsahuje číslo a v jeho okolí se nachází minimálně jedno neprozkoumané pole, vloží se do seznamu border_fiels
            if cell > 0 and cell < 9 and UNKNOWN in [actual_matrix[sqr[0]][sqr[1]] for sqr in surrounds((y, x))]:
                border_fields.append((y, x))

    #Průchod přes všechny hraniční políčka, která obsahují číslo a v jejich okolí se nachází nějaký nenulový počet neprozkoumaných políček
    for field in border_fields:

        #Vytvoření seznamu sousedních hraničních políček pro aktuální políčko
        surr_borders = [x for x in surrounds((field[0], field[1])) if x in border_fields]

        #Vytvoření seznamu sousedních neprozkoumaných políček pro aktuální políčko
        surr_unknown = [x for x in surrounds((field[0], field[1])) if 
                       actual_matrix[x[0]][x[1]] == UNKNOWN and type(actual_matrix[x[0]][x[1]]) != float]
        
        #Vytvoří hodnotu, která reprezentuje číslo políčka, od kterého se odečte počet sousedních min s vlaječkami, 
        #i takovými o kterých je čerstvě zjištěno, že se pod nimi nachází mina
        field_val = actual_matrix[field[0]][field[1]] - len([x for x in surrounds((field[0], field[1])) if
                                               actual_matrix[x[0]][x[1]] == FLAG or (
                                                           type(actual_matrix[x[0]][x[1]]) == float and actual_matrix[x[0]][
                                                       x[1]] == 1.0)])
        
        #Pro každou dvojici aktuálního políčka + sousedního hraničního políčka se pokusí zjistit, jestli se v jejich okolí nenacháází 100% miny 
        #nebo bezpečná políčka
        for adjacent_field in surr_borders:

            #Vytvoří seznam neodhalených políček sousedního přilehlého políčka
            adj_sur_unknown = [x for x in surrounds((adjacent_field[0], adjacent_field[1])) if
                              actual_matrix[x[0]][x[1]] == UNKNOWN and type(actual_matrix[x[0]][x[1]]) != float]
            
            #Vytvoří hodnotu, která reprezentuje číslo sousedního přilehlého políčka, od kterého se odečte počet sousedních min s vlaječkami, 
            #i takovými o kterých je čerstvě zjištěno, že se pod nimi nachází mina
            adj_field_val = actual_matrix[adjacent_field[0]][adjacent_field[1]] - len([x for x in surrounds((adjacent_field[0], adjacent_field[1])) if
                                                              actual_matrix[x[0]][x[1]] == FLAG or (
                                                                          type(actual_matrix[x[0]][x[1]]) == float and
                                                                          actual_matrix[x[0]][x[1]] == 1.0)])
            
            #Vytvoří seznam neprozkoumaných políček sousedního přilehlého políčka, který neobsahuje neodhalená políčka prozkoumávaného políčka
            only_adj_sur = [x for x in adj_sur_unknown if x not in surr_unknown]

            #Vytvoří seznam neprozkoumaných políček prozkoumávaného políčka, který neobsahuje neodhalená políčka sousedního přilehlého políčka
            only_sur = [x for x in surr_unknown if x not in adj_sur_unknown]

            #je-li upravená hodnota sousedního přilehlého políčka - upravená hodnota prozkoumávaného políčka 
            #rovna počtu neprozkoumaných políček přilehlého sousedního políčka, můžeme s jistotou označit políčka ze seznamu only_sur za 100%
            #bezpečná a políčka ze seznamu only_adj_sur za políčka jednoznačně obsahující minu
            if adj_field_val - field_val == len(only_adj_sur):
                for sqr2 in only_adj_sur:
                    new_matrix[sqr2[0]][sqr2[1]] = 1.0
                for sqr2 in only_sur:
                    new_matrix[sqr2[0]][sqr2[1]] = 0.0

    return new_matrix

def calc_probs(matrix, rem_mines):
    new_matrix = gen_known_matrix()
    actual_matrix = convert_matrix_to_list_of_lists(matrix)

    new_matrix = get_fields_by_set_idea(actual_matrix, new_matrix)

    #Získá všechna hraniční políčka, o kterých stále není známo, jestli jsou minami nebo ne
    border_sqrs = []
    for y, row in enumerate(actual_matrix):
        for x, cell in enumerate(row):
            if cell >= ONE and cell <= EIGHT:
                border_sqrs += [x for x in surrounds((y, x)) if
                                actual_matrix[x[0]][x[1]] == UNKNOWN and type(new_matrix[x[0]][x[1]]) != float]
                
    newborders_sqrs = []
    for x in border_sqrs:
        if x not in newborders_sqrs:
            newborders_sqrs.append(x)
    border_sqrs = newborders_sqrs

    #Získá políčka která nejsou hraniční a jsou neznámá
    unbordered_sqrs = []
    for y, row in enumerate(actual_matrix):
        for x, cell in enumerate(row):
            if cell == UNKNOWN and ((y,x) not in border_sqrs) and type(new_matrix[y][x]) != float:
                unbordered_sqrs.append((y,x))

    #Vytvoří lineární rovnici pro každé políčko obsahující číslo
    equation_matrix = []
    for y, row in enumerate(actual_matrix):
        for x, cell in enumerate(row):
            if cell >= ONE and cell <= EIGHT:
                equation = [0] * (len(border_sqrs) + 1)
                for sqr in [x for x in surrounds((y, x)) if actual_matrix[x[0]][x[1]] == UNKNOWN and type(new_matrix[x[0]][x[1]]) != float]:
                    equation[border_sqrs.index(sqr)] = 1
                equation[-1] = cell - len([x for x in surrounds((y,x)) if actual_matrix[x[0]][x[1]] == FLAG or new_matrix[x[0]][x[1]] == 1.0])
                equation_matrix.append(equation)

    #Pokud existují neznámé pravděpodobnosti pro některá z políček, počítá tyto pravděpodobnosti
    if len(border_sqrs) > 0:

        # Pojmenuje každé hraniční políčko a1, a2, a3 ...
        symbolstr = ''
        for i in range(len(border_sqrs)):
            symbolstr += f'a{i}, '
        symbolstr = symbolstr[:-2]
        variables = sympy.symbols(symbolstr)

        #Řeší systém lineárních rovnic
        solution = sympy.linsolve(sympy.Matrix(equation_matrix),variables).args[0]

        #Určuje parametry řešení rovnic
        parameters = []
        for i in range(len(border_sqrs)):
            try:
                if solution.args[i] == variables[i]:
                    parameters.append(variables[i])
            except TypeError:
                continue

        #Získá konstanty všech řešní rovnic
        constants = solution.subs(list(zip(parameters, [0] * len(parameters))))

        #Rozdělí řešení do skupin které jsou si na sobě navzájem nezávislé
        groups = gen_groups(solution,parameters)

        #Získá rovnice patřící do každé skupiny, vytvoří novou skupinu pro výrazy obsahující pouze konstanty
        eq_groups = []
        for i in range(len(groups)+1):
            eq_groups.append([])

        eq_groups_num = []  #Číslo skupiny do které patří každý výraz v řešení
        for i, eq in enumerate(solution):
            num = 0
            for j, group in enumerate(groups):
                for par in group:
                    if eq.coeff(par) != 0:
                        eq_groups[j].append(eq)
                        num = j
                        break
                    elif eq == constants[i]:
                        num = len(groups)
                        eq_groups[num].append(eq)
                        break
                else:
                    continue
                break
            eq_groups_num.append(num)

        #Seřadí seznam hraničních políček a seznam řešení rovnic tak, aby si při indexaci navzájem odpovídali
        border_sqrs = [x for _, x in sorted(zip(eq_groups_num, border_sqrs), key=lambda pair: pair[0])]
        solution = [x for _, x in sorted(zip(eq_groups_num, solution), key=lambda pair: pair[0])]

        groups = groups + [[]] #Přidá novou skupinu, která obsahuje parametry pro výrazy které mají pouze konstanty, což je prázdná skupina
        alleq_groups = []  #Bude obsahovat všechna možná řešení pro každou skupinu
        for i,eqgroup in enumerate(eq_groups):
            f = sympy.lambdify(groups[i], eqgroup)
            local_possible_solutions = []
            for possibility in foo([0, 1], len(groups[i])):
                localsolution = f(*possibility)
                valid = True
                for x in localsolution:
                    # Obsahuje všechna možná řešení pro každou skupinu
                    if x != 1 and x != 0:
                        valid = False
                        break
                if valid:
                    local_possible_solutions.append(localsolution)
            alleq_groups.append(local_possible_solutions)

        #Pokud je příliž mnoho parametrů tak nepokračuje, protože to může trvat příliž dlouho
        #Počet parametrů lze měnit v závislosti na výkonu počítače
        if len(parameters) < 35:
            #Počet min, které byly odhaleny na základě předešlé metody využívající množiny
            alreadyFoundMines = 0
            for y,row in enumerate(new_matrix):
                for x,cell in enumerate(row):
                    if cell == 1.0 and actual_matrix[y][x] != FLAG:
                        alreadyFoundMines += 1

            numberOfPossibilities = {}                  #Slovník pro opětovné použití některých velkých hodnot již vypočítaných pomocí comb()
            problist = [0]*len(border_sqrs)             #Pravděpodobnosti každého příslušného hraničního políčka obsahující minu
            unbordered_prob = 0                         #Pravděpodobnost, že každé nehraniční políčko obsahuje minu
            total = 1                                   #Celkový počet možných konfigurací min
            num_possibilities = 0                       #Počet možných stavů hraničních políček

            #Generuje všechny možné kombinace všech možných řešení pro každou skupinu
            for c in itertools.product(*[list(range(len(x))) for x in alleq_groups]):
                result = []
                for x in [alleq_groups[i][j] for i, j in enumerate(c)]:
                    result = result + x   #Vzhledem k tomu, že byla hraniční políčka seřazena podle čísel skupiny, lze možná řešení skupiny pouze sečíst do seznamu

                val = sum(result)
                if val <= rem_mines - alreadyFoundMines:  #Počet min v současném možném řešení nemůže být větší než počet zbývajících min
                    if val not in numberOfPossibilities:
                        numberOfPossibilities[val] = comb(len(unbordered_sqrs), rem_mines - val - alreadyFoundMines)
                    total += numberOfPossibilities[val]
                    unbordered_prob += (rem_mines - val - alreadyFoundMines)
                    num_possibilities += 1
                    for i, x in enumerate(result):
                        problist[i] += x * numberOfPossibilities[val]

            problist = [x/total for x in problist]
            if len(unbordered_sqrs) > 0:
                unbordered_prob /= num_possibilities*len(unbordered_sqrs)

            #Nahradí každou nalezenou pravděpodobnost v matici pravděpodobností new_matrix
            for i,sqr in enumerate(border_sqrs):
                new_matrix[sqr[0]][sqr[1]] = problist[i]
            for i,sqr in enumerate(unbordered_sqrs):
                new_matrix[sqr[0]][sqr[1]] = unbordered_prob
        else:
            #V případě, že by bylo parametrů příliš mnoho, alespoň některá políčka určitě obsahují miny, 
            #protože řešení lineárního systému dalo, že jsou to konstanty 1.0 nebo 0.0
            for i in range(len(border_sqrs)):
                if solution.args[i] == sympy.core.numbers.Zero:
                    new_matrix[border_sqrs[i][0]][border_sqrs[i][1]] = 0.0
                elif solution.args[i] == sympy.core.numbers.One:
                    new_matrix[border_sqrs[i][0]][border_sqrs[i][1]] = 1.0
    else:
        if mgd.debug: print("Metoda výpočtu pomocí soustavy lineárních rovnic nebyla potřeba")
    return(new_matrix)
#_______________________________________________________________________________________________________
#Zde končí funkce převzaté ze svobodně dostupného repoziráže, dostupného na: https://github.com/PedroKKr/Minesweeper-probability-calculator
#_______________________________________________________________________________________________________ 
