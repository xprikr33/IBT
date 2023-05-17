1. Nainstalujte níže vypsané hry, v případě že jsou hry již předinstalovány pokračujte dalším krokem.
    -   GNOME-Mines.
    -   AisleRiot Solitaire.

2. První spuštění hry AisleRiot Solitaire.
    -   Spusťte hru.
    -   Ujistěte se, že jsou v záložce "View" zaškrtnutá políčka: Toolbar, Statusbar.
    -   Ujistěte se, že je ve stejné záložce "View" zvolen Card Style: Bonded.
    -   Ujistěte se, že je v záložce "Klondike" zvolena pouze možnost: Single card deals.

3. První spuštění hry GNOME-Mines
    -   Ujistěte se, že je v nastavení ve složce Appearance zvolená první možnost, kde mají políčka pod čísly různou barvu.
    -   Pro zajištění bezproblémového běhu programu, ukončete hru v režimu celé obrazovky.

4. Instalace potřebných knihoven
    -   pyautogui
    -   pillow
    -   scrot
    -   python3-tk
    -   python3-dev
    -   python-wnck
    -   screeninfo
    -   opencv-python
    -   pstutil
    -   sympy

    POZNÁMKA:   Různé linuxové distribuce mohou mít některé z knihoven předinstalovány,
                některé z knihoven mohou vyžadovat instalaci dalších modulů, popřípadě
                mohou být vyžadovány úpravy týkající se oprávnění.

5.  Spuštění programu pro automatické hraní hry AisleRiot Solitaire
    -   Spouštějte příkazem ze složky obsahující zdrojové soubory programu: python3 solitaire.py

6.  Spuštění programu pro automatické hraní hry GNOME-Mines
    -   Ujistěte se, že je vaše klávesnice přepnutá do angličtiny
    -   Spouštějte příkazem ze složky obsahující zdrojové soubory programu: python3 mines.py {s, m, l} [-d]
    -   Parametry s, m, l volíte obtížnost hry
    -   Volitelný parametr -d aktivuje tisk jednotlivých stavů hry, přesměrovaný do souboru game.log
