from __main__ import *
import random
import time
from termcolor import colored
from sys import argv
from typing import Final

__name__ = "Battleship"
term_width: Final[int] = 45
term_height: Final[int] = 39


def gen_board(sea: list[list[bool]], boats: list[tuple[tuple[int, int], tuple[int, int], int]], show_boats: bool = "--show-boats" in argv) -> str:
    """Generates the board string to be printed."""
    board = ""
    boat_coords = get_all_boat_coords(boats)
    for y in range(10):
        for x in range(10):
            pos = (x, y)
            boat = get_boat_at(boats, x, y) if pos in boat_coords else None
            board += (colored("BB" if show_boats and pos in boat_coords else letters[x] + str(y), boat[3][0] if boat is not None and show_boats else "green", attrs=boat[3][1] if show_boats and boat is not None else None) if not sea[y][x] else colored("XX", "yellow") if not (x, y) in boat_coords else colored("BB", "red")) + " "
        board = board.strip() + "\n"
    return board.strip()


def get_boat_at(boats: list[tuple[tuple[int, int], tuple[int, int], int]], x: int, y: int) -> tuple[int, int] or None:
    """Returns the boat that overlaps the given location or `None` if there isn't one."""
    pos = (x, y)
    for boat in boats:
        if pos in get_all_boat_coords([boat]):
            return boat


def print_board():
    """Prints the board."""
    clear_term()
    printw("Round " + str(int(game_round/2)))
    printw("Board of bot's sea (attacked by you):")
    printw(gen_board(bot_sea, bot_boats))
    printw()
    printw("Board of your sea (attacked by bot):")
    printw(gen_board(player_sea, player_boats, True))
    printw()
    printw("Your boats are at:")
    for boat in player_boats:
        printw(f"{format_xy(boat[0][0], boat[0][1])} to {format_xy(boat[1][0], boat[1][1])} hit {sum(1 if player_sea[pos[1]][pos[0]] else 0 for pos in get_all_boat_coords([boat]))}/{boat[2]} times")


def gen_sea() -> list[list[bool]]:
    """Generates an empty sea."""
    # [[False]*10]*10 doesn't work as every list is just a clone of the other, edit one, you edit the others.
    sea = []
    for x in range(10):
        ls = []
        for y in range(10):
            ls.append(False)
        sea.append(ls)
    return sea


difficulty = 0
letters: Final[str] = "ABCDEFGHIJ"

bot_sea = gen_sea()
player_sea = gen_sea()

possible_boats: Final[list[tuple[int, str, list or None]]] = [(5, "blue", None), (4, "magenta", None), (3, "cyan", None), (3, "magenta", ["bold"]), (2, "blue", ["bold"])]  # Official Hasbro Battleship boats https://en.wikipedia.org/wiki/Battleship_(game)
bot_boats = []
player_boats = []

medium_last_strike = None
medium_last_strike_success = False


def get_all_boat_coords(boats: list[tuple[tuple[int, int], tuple[int, int], int]]) -> list[tuple[int, int]]:
    """Returns all coordinates containing boats."""
    coords = []
    for boat in boats:
        direction = boat[0][0] < boat[1][0]
        for i in range(boat[2]):
            coords.append((boat[0][0] + (i if direction else 0), boat[0][1] + (i if not direction else 0)))
    return coords


def boat_in_range(boats: list[tuple[tuple[int, int], tuple[int, int], int]], pos1: tuple[int, int], pos2: tuple[int, int], length: int) -> bool:
    """Returns whether there's a boat in the given range."""
    coords_ch = get_all_boat_coords([(pos1, pos2, length)])
    all_coords = get_all_boat_coords(boats)
    for coord in coords_ch:
        if coord in all_coords:
            return True
    return False


def spread_boats(boats):
    """Spreads all boats across the sea, also makes sure None of them overlap."""
    boats.clear()
    for boat, colour, attrs in possible_boats:
        x = y = 0
        direction = False
        pos1 = pos2 = None
        init = True
        while init or 10 - (x if direction else y) < boat or boat_in_range(boats, pos1, pos2, boat):
            init = False
            x = random.randint(0, 9)
            y = random.randint(0, 9)
            direction = random.choice([True, False])
            pos1 = (x, y)
            pos2 = (x + (boat - 1 if direction else 0), y + (boat - 1 if not direction else 0))
        boats.append((pos1, pos2, boat, (colour, attrs)))


spread_boats(bot_boats)
spread_boats(player_boats)


def bot_bomb():
    """Let the bot bomb a spot."""
    printw("My turn!")
    time.sleep(1.5)
    pos = choose_spot()
    printw("I choose " + format_xy(pos[0], pos[1]) + ".")
    printw(colored("Boom!", "red") if has_boat(player_boats, pos[0], pos[1]) else colored("Splash!", "green"))
    player_sea[pos[1]][pos[0]] = True
    time.sleep(1.5)


def choose_spot(dif: int or None = None) -> tuple[int, int]:
    """Choose a spot for the bot to bomb.
    In case the difficulty is medium, it takes in account whether the last bomb was successful."""
    pos = None
    dif = difficulty if dif is None else dif
    if dif == 0:
        pos = None
        while pos is None or player_sea[pos[1]][pos[0]]:
            pos = (random.randint(0, 9), random.randint(0, 9))
    elif dif == 1:
        global medium_last_strike
        global medium_last_strike_success
        ub = get_unbombed_neighbours(player_sea, medium_last_strike[0], medium_last_strike[1]) if medium_last_strike is not None else None
        if not medium_last_strike_success or len(ub) == 0:
            pos = choose_spot(0)
            medium_last_strike = pos
            medium_last_strike_success = has_boat(player_boats, pos[0], pos[1])
        else:
            pos = medium_last_strike = random.choice(ub)
            medium_last_strike_success = has_boat(player_boats, pos[0], pos[1])
    return pos


def get_unbombed_neighbours(sea: list[list[bool]], x: int, y: int) -> list[tuple[int, int]]:
    """Returns the coordinates of all neighbours of the given spot that have not yet been bombed."""
    neighbours = []
    for neighbour in get_neighbours(x, y, 9, 9):
        if not sea[neighbour[1]][neighbour[0]]: neighbours.append(neighbour)
    return neighbours


def player_bomb():
    """Let the player bomb a spot."""
    printw("Your turn!")
    pos = ask_input(f"What spot would you like to bomb? (E.g. {format_xy(random.randint(0, 9), random.randint(0, 9))})", cast=lambda ans: pos_from_input(ans), post_check=lambda ans: "You have already bombed that spot, please try another." if bot_sea[ans[1]][ans[0]] else True)
    bot_sea[pos[1]][pos[0]] = True
    printw(colored("Boom!", "red") if has_boat(bot_boats, pos[0], pos[1]) else colored("Splash!", "green"))
    time.sleep(1.5)


def has_boat(boats: list[tuple[tuple[int, int], tuple[int, int], int]], x: int, y: int) -> bool:
    """Returns whether the given spot contains a boat."""
    return (x, y) in get_all_boat_coords(boats)


def format_xy(x: int, y: int) -> str:
    """Returns the string representation of the given spot."""
    return letters[x] + str(y)


def pos_from_input(s: str) -> tuple[int, int]:
    """Turns the string representation of a spot into its coordinates."""
    s = s.upper()
    if len(s) == 2 and s[0] in letters and is_int(s[1]) and 0 <= int(s[1]) < 10:
        return letters.index(s[0]), int(s[1])
    else:
        raise ValueError


def is_defeated(boats: list[tuple[tuple[int, int], tuple[int, int], int]], sea: list[list[bool]]) -> bool:
    """Returns whether the player or bot has been defeated."""
    defeated = True
    for pos in get_all_boat_coords(boats):
        if not sea[pos[1]][pos[0]]:
            defeated = False
            break
    return defeated


def check_win() -> int:
    """Checks if either the bot or the player has won yet."""
    return 2 if is_defeated(bot_boats, bot_sea) else 1 if is_defeated(player_boats, player_sea) else 0


def setup():
    """Resets all variables."""
    global bot_sea, player_sea
    global bot_boats, player_boats
    global game_round, turn, first
    bot_sea = gen_sea()
    player_sea = gen_sea()
    bot_boats = []
    player_boats = []
    spread_boats(bot_boats)
    spread_boats(player_boats)
    game_round = 2
    turn = random.choice([True, False])
    first = True
    set_title("Battleship")
    set_dims(term_width, term_height)


game_round = 2
turn = random.choice([True, False])
first = True


def play():
    """Play Battleship"""
    global difficulty, first, turn, game_round
    try:
        setup()
        difficulty = menu("What difficulty would you like to play at?", "Easy", "Medium", cast=lambda ans: 0 if ans == "Easy" else 1 if ans == "Medium" else 2, color="green")  # ask_input("What difficulty would you like to play at? Type 0 for easy, 1 for medium and 2 for hard.",  cast=lambda ans: int(ans), post_check=lambda ans: "Hard mode has not yet been implemented." if ans == 2 else 0 <= ans <= 2)
        printw(("Easy" if difficulty == 0 else "Medium" if difficulty == 1 else "Hard") + " it is!")
        try:
            time.sleep(1)
            printw("The objective is to sink all the enemy's boats which are the same as yours, but placed differently.")
            time.sleep(4.5)
        except KeyboardInterrupt:  # So you may skip the intro.
            pass
        while True:
            print_board()
            if first:
                printw(f"\n{'I' if not turn else 'You'} go first!")
                first = False
            else: printw()
            won = check_win()
            if won > 0:
                clear_term()
                printw(f"After {game_round} rounds...")
                printw(colored("You lost! :(", "red", attrs=["underline"]) if won == 1 else colored("You won! :D", "green", attrs=["underline"]))
                printw()
                printw("Thank you for playing!")
                printw("Game made by PlanetTeamSpeak")
                raise KeyboardInterrupt  # Will get caught, quitting the game.
            # FIXME Some stupid error when player quits if they go first and don't bomb anything and the whole process quits rather than going back to the menu.
            # FIXME edit: seems to occur in almost every game.
            # Honestly pulling out hairs on why this happens and I cannot seem to be able to fix it.
            if turn: player_bomb()
            else: bot_bomb()
            turn = not turn
            game_round += 1
    except (KeyboardInterrupt, EOFError):
        exit_game()
