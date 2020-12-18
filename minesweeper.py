from __main__ import *
from typing import Final
import random
from termcolor import colored
from pynput.keyboard import Key, KeyCode
from queue import Queue
import time
import threading
from sys import argv


def kc_init_new(*args, **kwargs):
    try:
        kc_init(*args, **kwargs)
    except KeyError:
        pass


kc_init = KeyCode.__init__
KeyCode.__init__ = kc_init_new


class MSDifficulty:
    BEGINNER = INTERMEDIATE = EXPERT = CUSTOM = None

    def __init__(self, name: str, get_values):
        self.name: Final[str] = name
        self.get_values = get_values


MSDifficulty.BEGINNER = MSDifficulty("beginner", lambda: (9, 9, 10))
MSDifficulty.INTERMEDIATE = MSDifficulty("intermediate", lambda: (16, 16, 40))
MSDifficulty.EXPERT = MSDifficulty("expert", lambda: (30, 16, 99))
MSDifficulty.CUSTOM = MSDifficulty("custom", lambda: tuple(int_menu("Please select the width, height and the amount of mines", {"width": (9, 99), "height": (9, 99), "mines": lambda width, height: (width*height//9, width*height//3)}).values()))
MSDifficulty.values = (MSDifficulty.BEGINNER, MSDifficulty.INTERMEDIATE, MSDifficulty.EXPERT, MSDifficulty.CUSTOM)

__name__ = "Minesweeper"
board_width: int = 0
board_height: int = 0
board_mines: int = 0
mines: list[list[bool]] = []
board: list[list[int]] = []  # 0 is unopened, 1 is opened, 2 is flagged and 3 is questioning
cursor: tuple[int, int] = (-1, -1)
queue: Final[Queue] = Queue()
play_thread: Final[threading.Thread] = threading.current_thread()
locked_keys: list[Key or KeyCode] = []
colours: list[dict] = [{"color": "cyan", "attrs": ["bold"]}, {"color": "green", "attrs": ["bold"]}, {"color": "red", "attrs": ["bold"]}, {"color": "blue"}, {"color": "red"}, {"color": "cyan"}, {"color": "grey"}, {"color": "grey", "attrs": ["bold"]}]
smiley: str = ":)"
defeat: bool = False
time_passed: int = 0
do_queue: bool = False
first: bool = True
ignore_keys: bool = True  # To not make the screen flicker due to loads of updates when starting a new game.


def spread_mines():
    """Spreads all mines randomly across the board."""
    mines.clear()
    board.clear()
    for y in range(board_height):
        ls = []
        ls1 = []
        for x in range(board_width):
            ls.append(False)
            ls1.append(0)
        mines.append(ls)
        board.append(ls1)
    for i in range(board_mines):
        pos = None
        while pos is None or mines[pos[1]][pos[0]]:
            pos = (random.randint(0, board_width-1), random.randint(0, board_height-1))
        mines[pos[1]][pos[0]] = True


def gen_board(show_mines: bool = False) -> str:
    """Generates the board string to be printed.
    Can optionally also reveal the locations of the mines."""
    show_mines = show_mines or "--show-mines" in argv
    s = ""
    for y in range(board_height):
        for x in range(board_width):
            pos = (x, y)
            minecount = get_neighbouring_minecount(x, y)
            args = colours[minecount-1].copy()
            args["color"] = "grey" if pos == cursor else args["color"]
            s += colored(colored(str(minecount), **args) if board[y][x] == 1 else colored("M", "grey" if pos == cursor else "red" if defeat else "yellow") if mines[y][x] and show_mines else colored("F" if board[y][x] == 2 else "?", "grey" if (x, y) == cursor else "yellow" if not defeat else "green" if mines[y][x] else "red") if board[y][x] > 1 else colored("X", "grey" if pos == cursor else "white"), on_color="on_white" if (x, y) == cursor and not defeat else None)
        s += "\n"
    return s.strip()


def print_board(show_mines: bool = False):
    """Prints the board."""
    clear_term()
    printw(ensure_length(get_mines_left(), max_length=len(str(board_mines))) + ensure_length(smiley, max_length=board_width//2-len(str(board_mines))) + ensure_length(format_seconds(), max_length=board_width//2))
    printw(gen_board(show_mines))


def format_seconds() -> str:
    """Formats seconds into minutes and seconds."""
    return f"{time_passed // 60}:{'{:02d}'.format(time_passed % 60)}"


def setup():
    """Resets all variables and asks the user for a difficulty."""
    global ignore_keys
    ignore_keys = True
    difficulty = menu("What difficulty would you like to play at?", [dif.name for dif in MSDifficulty.values], cast=lambda ans: dict(zip(list(dif.name for dif in MSDifficulty.values), MSDifficulty.values))[ans.lower()], color="green")
    set_title("Minesweeper - " + difficulty.name)
    global board_width, board_height, board_mines
    board_width, board_height, board_mines = difficulty.get_values()
    set_dims(board_width, board_height+2)
    global cursor
    cursor = (board_width//2, board_height//2)
    spread_mines()
    global first, defeat, time_passed, smiley
    first = True
    defeat = False
    time_passed = 0
    smiley = ":)"
    ignore_keys = False


def printw(*args, **kwargs):
    """Printing is definitely not thread-safe, trust me, I've tested it, so to make it thread-safe, print commands have to be enqueued and printed on the main thread."""
    if threading.current_thread() != play_thread:
        queue.put((printw, args, kwargs))
    else:
        printw_(*args, **kwargs)


def get_neighbouring_minecount(x, y) -> int:
    """Gets the amount of mines neighbouring the given position."""
    return sum(1 if mines[neighbour[1]][neighbour[0]] else 0 for neighbour in get_neighbours(x, y, board_width, board_height, True))


def get_mines_left() -> int:
    """Calculates the amount of mines that have not yet been flagged on the board."""
    return board_mines - sum([1 if board[y][x] == 2 else 0 for x in range(board_width) for y in range(board_height)])


def open_spot(x: int, y: int, refresh: bool = True):
    """Opens a spot on the board."""
    if board[y][x] == 0:
        global first
        if first:
            # No matter where you start, the first spot you open will always have 0 mines nearby.
            neighbours = [(x, y)] + get_neighbours(x, y, board_width, board_height, True)
            count = 0
            for pos in neighbours:
                if mines[pos[1]][pos[0]]:
                    count += 1
                    mines[pos[1]][pos[0]] = False
            for i in range(count):
                pos = None  # Moving the mines so you at least have something to start with.
                while pos is None or mines[pos[1]][pos[0]]:
                    pos = (random.randint(0, board_width - 1), random.randint(0, board_height - 1))
                mines[pos[1]][pos[0]] = True
            first = False
        global smiley
        if mines[y][x]:
            smiley = "X("
            global defeat, cursor
            cursor = (-1, -1)
            defeat = True
        else:
            smiley = ":O"
            board[y][x] = 1
            if get_neighbouring_minecount(x, y) == 0:
                for neighbour in get_neighbours(x, y, board_width, board_height, True):
                    open_spot(neighbour[0], neighbour[1], False)
            if refresh:
                queue.put(True)


def flag_spot(x: int, y: int):
    """Flags a spot on the board."""
    if board[y][x] == 0 or board[y][x] == 2 or board[y][x] == 3:
        board[y][x] = 2 if board[y][x] == 0 else 0
        queue.put(True)


def question_spot(x: int, y: int):
    """Questions a spot on the board."""
    if board[y][x] == 0 or board[y][x] == 2 or board[y][x] == 3:
        board[y][x] = 3 if board[y][x] == 0 else 0
        queue.put(True)


def on_key_press(key: str or KeyCode):
    """Called by the main on_key_press function whenever a key is pressed on the OS."""
    if key not in locked_keys and not ignore_keys:
        global cursor
        x = cursor[0]
        y = cursor[1]
        if x != -1 and y != -1:
            global smiley
            smiley = ":)"
            if key == Key.up or isinstance(key, KeyCode) and key.char == 'w':
                y -= 1
            elif key == Key.down or isinstance(key, KeyCode) and key.char == 's':
                y += 1
            elif key == Key.left or isinstance(key, KeyCode) and key.char == 'a':
                x -= 1
            elif key == Key.right or isinstance(key, KeyCode) and key.char == 'd':
                x += 1
            elif key == Key.space or key == Key.enter:
                open_spot(cursor[0], cursor[1])
            elif key == Key.backspace:
                flag_spot(cursor[0], cursor[1])
            elif isinstance(key, KeyCode) and (key.char == '\\' or key.char == '?' or key.char == '/'):
                question_spot(cursor[0], cursor[1])
            x = clamp(x, 0, board_width - 1)
            y = clamp(y, 0, board_height - 1)
            if (x, y) is not cursor:
                cursor = (x, y)
                queue.put(True)
            locked_keys.append(key)


def on_key_release(key: str or KeyCode):
    """Called by the main on_key_press function whenever a key is released on the OS."""
    if key in locked_keys: locked_keys.remove(key)


def play():
    """Play Minesweeper"""
    global time_passed
    set_title("Minesweeper")
    setup()
    print_board()
    last_time = time.time()
    global do_queue
    do_queue = True
    while True:
        if defeat:
            set_dims(board_width, board_height+4)
            print_board(True)
            pause()
            break
        if time.time() - last_time >= 1:
            time_passed += 1
            print_board()
            last_time = time.time()
        if queue.qsize() > 0:
            o = queue.get()
            if isinstance(o, tuple) and callable(o[0]):
                o[0](*o[1], **o[2])
            elif isinstance(o, str):
                printw(o)
            elif o:
                clear_term()
                print_board()
        time.sleep(0.001)
    do_queue = True
