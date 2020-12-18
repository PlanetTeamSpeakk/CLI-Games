from __main__ import *
import random
from queue import Queue
import time
import threading
from termcolor import colored
from pynput.keyboard import Key, KeyCode

# Huge thanks to https://stackoverflow.com/a/56581709 for basically spoonfeeding all the code
# needed to make and print the board. All I had to do was add user input, really.
__name__ = "Sudoku"
guesses: list[list[bool or None]] = []
board_editable: list[list[int]] = []
board: tuple[tuple[int, ...]] = ((),)
board_solution: tuple[tuple[int, ...]] = ((),)
base: Final[int] = 3
side: Final[int] = base*base
cursor: tuple[int, int] = (-1, -1)
do_queue = False
print_queue: Queue = Queue()
play_thread: Final[threading.Thread] = threading.current_thread()
game_ended: bool = False


def pattern(r: int, c: int) -> int:
    """Does some calculations used for generating the board."""
    return (base*(r % base)+r//base+c) % (base**2)


def fill_board():
    """Generates the board."""
    guesses.clear()
    for y in range(side):
        ls = []
        for x in range(side):
            ls.append(None)
        guesses.append(ls)
    r_base = range(base)
    rows = [g * base + r for g in shuffle(r_base) for r in shuffle(r_base)]
    cols = [g * base + c for g in shuffle(r_base) for c in shuffle(r_base)]
    nums = shuffle(range(1, base * base + 1))
    global board, board_solution, board_editable
    board = [[nums[pattern(r, c)] for c in cols] for r in rows]
    board_solution = to_tuple(board)
    for _ in random.sample(range(side**2), side**2 * 3//4):
        x = y = -1
        while x == -1 and y == -1 or board[y][x] == 0:
            x = random.randint(0, side-1)
            y = random.randint(0, side-1)
        board[y][x] = 0
    board_editable = board
    board = to_tuple(board)


def to_tuple(ls: list) -> tuple:
    """Converts a list and all its nested lists into tuples."""
    ls0 = []
    for el in ls:
        ls0.append(el if not isinstance(el, list) else to_tuple(el))
    return tuple(ls0)


def check() -> bool:
    """Checks if the player has won yet."""
    has_won = True
    for y in range(side):
        for x in range(side):
            if board[y][x] != board_editable[y][x]:
                guesses[y][x] = board_editable[y][x] == board_solution[y][x]
            if not guesses[y][x]: has_won = False
    return has_won


def on_key_press(key):
    """Called by the main on_key_press function whenever a key gets pressed on the OS."""
    global cursor, game_ended
    x = cursor[0]
    y = cursor[1]
    if x != -1 and y != -1 and not game_ended:
        if key == Key.up or isinstance(key, KeyCode) and key.char == 'w':
            y -= 1
        elif key == Key.down or isinstance(key, KeyCode) and key.char == 's':
            y += 1
        elif key == Key.left or isinstance(key, KeyCode) and key.char == 'a':
            x -= 1
        elif key == Key.right or isinstance(key, KeyCode) and key.char == 'd':
            x += 1
        elif not guesses[y][x] and board[y][x] == 0 and (key == Key.backspace or key == Key.delete or isinstance(key, KeyCode) and (key.vk == 110 or is_int(key.char) and int(key.char) != 0 or 97 <= key.vk <= 105)):
            guesses[y][x] = None
            board_editable[y][x] = 0 if key == Key.backspace or key == Key.delete or key.vk == 110 else int(key.char) if is_int(key.char) else key.vk - 96
            print_queue.put(True)
        elif key == Key.enter or key == Key.space:
            game_ended = check()
            print_queue.put(True)
        x = clamp(x, 0, side - 1)
        y = clamp(y, 0, side - 1)
        if (x, y) is not cursor:
            cursor = (x, y)
            print_queue.put(True)


def print_board():
    """Prints the board."""
    def expand_line(line):
        """Expand the line to the size of the board."""
        return line[0] + line[5:9].join([line[1:5] * (base - 1)] * base) + line[9:13]
    top_line     = expand_line("╔═══╤═══╦═══╗")
    num_holder   = expand_line("║ . │ . ║ . ║")
    divider      = expand_line("╟───┼───╫───╢")
    base_divider = expand_line("╠═══╪═══╬═══╣")
    bottom_line  = expand_line("╚═══╧═══╩═══╝")
    symbol = " 1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    nums = [[""] + [colored(symbol[spot], color="grey" if (x, y) == cursor else ("yellow" if guesses[y][x] is None else "green" if guesses[y][x] else "red") if board[y][x] != board_editable[y][x] else None, on_color="on_white" if (x, y) == cursor else None) for x, spot in enumerate(row)] for y, row in enumerate(board_editable)]
    printw(top_line)
    for r in range(1, side + 1):
        printw("".join(n + s for n, s in zip(nums[r - 1], num_holder.split("."))))
        printw([divider, base_divider, bottom_line][(r % side == 0) + (r % base == 0)])
    if game_ended:
        printw("You won! Press escape to go back.")


def printw(*args, **kwargs):
    """Printing is definitely not thread-safe, trust me, I've tested it, so to make it thread-safe, print commands have to be enqueued and printed on the main thread."""
    if threading.current_thread() != play_thread and do_queue:
        print_queue.put((printw, args, kwargs))
    else:
        printw_(*args, **kwargs)


def play():
    """Play Sudoku"""
    fill_board()
    global cursor, game_ended
    cursor = (side // 2, side // 2)
    set_dims(side * 4 + 1, side * 2 + 3)
    game_ended = False
    print_board()
    global do_queue
    do_queue = True
    while True:
        if print_queue.qsize() > 0:
            o = print_queue.get()
            if isinstance(o, tuple) and callable(o[0]):
                o[0](*o[1], **o[2])
            elif isinstance(o, str):
                printw(o)
            elif o:
                clear_term()
                print_board()
        time.sleep(0.001)
    do_queue = False
