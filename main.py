# Written by PlanetTeamSpeak
# https://github.com/PlanetTeamSpeakk

import os
import random
import sys
from typing import Final
from sys import stdout
from termcolor import colored, ATTRIBUTES, HIGHLIGHTS, COLORS, RESET
from pynput.keyboard import Key, Listener, Controller, KeyCode
from win32gui import GetForegroundWindow
import time


os.system("color")  # Making sure that we can use colours and other ANSI escape sequences. (Such as the ones used in #ask_input)
win: Final[bool] = os.name == "nt"
orig_dims: Final[tuple] = tuple(os.get_terminal_size())
games = {}
formattings: Final[tuple] = tuple([colored("", colour).replace(RESET, "") for colour in COLORS.keys()] + [colored("", on_color=colour).replace(RESET, "") for colour in HIGHLIGHTS.keys()] + [colored("", attrs=[attr]).replace(RESET, "") for attr in ATTRIBUTES.keys()] + [RESET])
term_title = None
term_wdw: Final[int] = GetForegroundWindow()  # Wouldn't mind a better solution seeing as this assumes the terminal bound to this process is the active foreground window when it's ran. One such solution would be to make our own GUI resembling a terminal which would probably fix quite some issues too...
is_paused: bool = False
current_game = None
menu_selection = -1
menu_max = -1
menu_selection_made = False
int_menu_option = -1
int_menu_option_max = -1
int_menu_values = {}
int_menu_exit = False
int_menu_alteration = True


def set_dims(width, height):
    """Set the dimensions of the terminal window."""
    if win: os.system(f"mode con: cols={width} lines={height}")
    else: print(f"\x1b[8;{width};{height}t")


def is_int(s):
    """Check if the given object can be cast to an integer."""
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


def clear_term():
    """Clear the terminal."""
    os.system("cls" if win else "reset")


def set_title(title):
    """Set the terminal's title."""
    if win: os.system("title " + title)
    else: print("\33]0;" + title + "\a", end='', flush=True)
    global term_title
    term_title = title


def pause():
    """Pause until the user presses a key."""
    global is_paused
    is_paused = True
    printw("Press any key to continue...")
    while is_paused:
        time.sleep(0.001)


def unpause():
    global is_paused
    is_paused = False


# Copied from my other code I wrote for my computer science class (https://repl.it/@PlanetTeamSpeak/Opdrachten#main.py)
# (Although at this point it's heavily altered.)
# Deliberately rarely used anymore though.
# noinspection PyBroadException
def ask_input(question, cast=lambda ans: ans, post_check=None, pre_check=None):
    """Ask the user for input."""
    question += "\n> "
    lines = len(wrap_lines(question))
    while True:
        qlines = wrap_lines(question)
        raw_ans = ans = ""
        try:
            for i, line in enumerate(qlines):
                if i != len(qlines)-1: print(line)
                else: raw_ans = ans = input(line)
        except EOFError:
            return None
        accept = False
        error = "That answer was not accepted"
        pre_accept = pre_check is None or pre_check(ans)
        if isinstance(pre_accept, str):
            error = pre_accept
            pre_accept = False
        if pre_accept:
            try:
                ans = cast(ans)
                accept = post_check(ans) if post_check is not None else True
                if isinstance(accept, str):
                    error = accept
                    accept = False
            except Exception:
                pass
        if not accept:
            lines += len("> " + raw_ans) // os.get_terminal_size()[0]  # The answer is wrapped by the width of the terminal, not on spaces.
            clear_lines(lines)
            print(colored(error, "red"))
            lines = len(wrap_lines(question)) + len(wrap_lines(error))
        else:
            break
    return ans


def clear_lines(lines):
    """Clear the given amount of lines from the terminal."""
    stdout.write("\033[F\033[K" * lines)


# Credits to https://stackoverflow.com/a/6340578
def traverse(o, tree_types=(list, tuple)):
    """Combine all lists/tuples in the given list/tuple into one single list."""
    if isinstance(o, tree_types):
        for value in o:
            for subvalue in traverse(value, tree_types):
                yield subvalue
    else:
        yield o


def join_nicely(*args):
    """Join the given args into a string separated by commas, but using 'and' for the last element."""
    args = [o for o in traverse(args)]
    size = len(args)
    s = ""
    for i, arg in enumerate(args):
        s += str(arg) + (" and " if i == size-2 else ", ")
    return s[:-2]


def reg_game(*modules):
    """Register a game in the registry."""
    for mod in traverse(modules):
        games[mod.__name__] = mod


def get_game(name):
    """Get a game by its name."""
    return games[name] if name in games else None


def printw_(*args, **kwargs):
    """Print a string wrapping on spaces."""
    for line in wrap_lines(args):
        print(line, **kwargs)


printw = printw_


def wrap_lines(*args):
    """Wrap a string on spaces."""
    s = " ".join([str(o) for o in traverse(args)])
    raw_lines = s.split("\n")
    split_lines = [line.split(" ") for line in raw_lines]
    tw = os.get_terminal_size()[0]
    lines = []
    for line in split_lines:
        sline = ""
        for word in line:
            if len(strip_formattings((sline + " " + word).strip())) <= tw:
                sline += " " + word
            else:
                lines.append(sline[(1 if len(sline) > 0 and sline[0] == " " else 0):])
                sline = word
        lines.append(sline[(1 if len(sline) > 0 and sline[0] == " " else 0):])
    return lines


def strip_formattings(s):
    """Remove all ANSI formattings from a string."""
    for formatting in formattings:
        s = s.replace(formatting, "")
    return s


def clamp(i: int, minv: int, maxv: int) -> int:
    """Clamps an integer between two values."""
    return maxv if i < minv else minv if i > maxv else i


def get_neighbours(x, y, max_x, max_y, include_corners=False):
    """Returns all direct neighbours of the given position, can optionally return neighbours direct neighbours have in common too."""
    neighbours = []
    max_x -= 1
    max_y -= 1
    if x > 0: neighbours.append((x - 1, y))
    if x < max_x: neighbours.append((x + 1, y))
    if y > 0: neighbours.append((x, y - 1))
    if y < max_y: neighbours.append((x, y + 1))
    if include_corners:
        if x > 0 and y > 0: neighbours.append((x - 1, y - 1))
        if x > 0 and y < max_y: neighbours.append((x - 1, y + 1))
        if x < max_x and y > 0: neighbours.append((x + 1, y - 1))
        if x < max_x and y < max_y: neighbours.append((x + 1, y + 1))
    return neighbours


def ensure_length(*args, max_length, append=False):
    """Ensures the given string is of the given length by either prepending or appending it with spaces."""
    s = " ".join([str(arg) for arg in traverse(args)])
    return (s if append else "") + " "*(max(max_length-len(strip_formattings(s)), 0)) + (s if not append else "")


def send_eof():
    """Sends EOF character although unused.
    Used to terminate stdin reading."""
    with keyboard.pressed(Key.ctrl_l):
        keyboard.press('z' if win else 'd')
    keyboard.press(Key.enter)


def on_key_press(key):
    """Called by pynput every time a key is pressed on the OS."""
    if GetForegroundWindow() == term_wdw:
        if is_paused: unpause()
        elif key == Key.esc:
            with keyboard.pressed(Key.ctrl_l):
                keyboard.press('c')
                keyboard.release('c')
        global menu_selection, menu_selection_made, int_menu_values, int_menu_option, int_menu_option_max, int_menu_exit, int_menu_alteration
        if menu_selection >= 0:
            if key == Key.up or isinstance(key, KeyCode) and key.char == 'w':
                menu_selection -= 1
            elif key == Key.down or isinstance(key, KeyCode) and key.char == 's':
                menu_selection += 1
            elif key == Key.space or key == Key.enter:
                menu_selection_made = True
            if menu_selection < 0: menu_selection = menu_max-1
            if menu_selection >= menu_max: menu_selection = 0
        if int_menu_option >= 0:
            i = list(int_menu_values.keys())[int_menu_option]
            if key == Key.up or isinstance(key, KeyCode) and key.char == 'w':
                int_menu_values[i] += 1
                int_menu_alteration = True
            elif key == Key.down or isinstance(key, KeyCode) and key.char == 's':
                int_menu_values[i] -= 1
                int_menu_alteration = True
            elif key == Key.left or isinstance(key, KeyCode) and key.char == 'a':
                int_menu_option -= 1
                int_menu_alteration = True
            elif key == Key.right or isinstance(key, KeyCode) and key.char == 'd':
                int_menu_option += 1
                int_menu_alteration = True
            elif key == Key.space or key == Key.enter:
                int_menu_exit = True
            if int_menu_option < 0: int_menu_option = int_menu_option_max-1
            if int_menu_option >= int_menu_option_max: int_menu_option = 0
        if hasattr(current_game, "on_key_press") and current_game.on_key_press is not on_key_press:
            current_game.on_key_press(key)


def on_key_release(key):
    """Called by pynput every time a key is released by the OS."""
    if hasattr(current_game, "on_key_release") and current_game.on_key_release is not on_key_release:
        current_game.on_key_release(key)


def exit_game():
    """Called when a game is exited."""
    try:
        printw("\nGoodbye!")
        pause()
        clear_term()
        set_dims(orig_dims[0], orig_dims[1])
    except (KeyboardInterrupt, EOFError):
        exit_game()


def shuffle(s):
    """Returns a shuffled version of a list or tuple."""
    return random.sample(s, len(s))


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    return os.path.join(getattr(sys, "_MEIPASS", os.environ.get("_MEIPASS2", os.path.abspath("."))), relative_path)


def menu(title, *options, prefix="  ", cast=lambda ans: ans, **colourkwargs):
    """Creates a menu for the user to select from.
    Blocks until the user has made a selection by pressing either space or enter."""
    global menu_selection, menu_max, menu_selection_made
    menu_selection_made = False
    menu_selection = 0
    current_selection = -1
    title += " (Alter selection with the arrow keys, press enter to select)"
    printw(title)
    options = list(traverse(options))
    menu_max = len(options)
    lines = 0
    while True:
        if menu_selection != current_selection:
            current_selection = menu_selection
            clear_lines(lines)
            lines = 0
            for i, option in enumerate(options):
                s = prefix + colored(str(i + 1) + ".", color="grey" if menu_selection == i else None, on_color="on_white" if menu_selection == i else None) + " " + colored(option, **colourkwargs)
                print(s)
                lines += len(wrap_lines(s))
        if menu_selection_made: break  # Still an infinite loop so the menu still gets to update before quitting once the user made a selection.
        time.sleep(0.001)
    menu_selection = menu_max = -1
    menu_selection_made = False
    return cast(options[current_selection])


def int_menu(title, options: dict[str], **colourkwargs):  # dict[name, tuple[min, max]]
    """A menu containing a set amount of sliders for integer values.
    Way too complicated for what it's trying to achieve if you ask me."""
    def _int_menu_get(func):  # Declaring function here because this is the only place where it's used.
        """Gets the value of an option.
        Returns the value itself if it's not a function, otherwise it runs it."""
        if isinstance(func, tuple): return func
        kwargs = {}
        for varname in func.__code__.co_varnames:
            if varname in int_menu_values:
                kwargs[varname] = int_menu_values[varname]
        return func(**kwargs)
    global int_menu_option, int_menu_option_max, int_menu_values, int_menu_alteration
    int_menu_option = 0
    int_menu_option_max = len(options)
    int_menu_values = options.copy()
    int_menu_alteration = True
    for key in int_menu_values:
        if callable(int_menu_values[key]):
            int_menu_values[key] = _int_menu_get(int_menu_values[key])
        int_menu_values[key] = int_menu_values[key][0]
    title += " (select option with arrow left and right keys, use arrow up and down keys to alter, press enter to finish)"
    printw(title)
    print("\n"*4)  # Printing 5 empty lines, 4 are boutta be deleted anyway.
    while True:
        if int_menu_alteration or int_menu_exit:
            clear_lines(4)
            lines = [""] * 4
            lines[0] += " " * 2
            for i, option in enumerate(options):
                int_menu_values[option] = max(min(int_menu_values[option], _int_menu_get(options[option])[1]), _int_menu_get(options[option])[0])  # Making sure it's between bounds.
                width = len(str(_int_menu_get(options[option])[1]))
                padding = len(str(option))-width+1
                max_length = width+padding+2
                lines[0] += ensure_length(colored(option, **colourkwargs), max_length=max_length)
                lines[1] += ensure_length(colored("\u25B2"*width, color="grey" if int_menu_option == i else None, on_color="on_white" if int_menu_option == i else None), max_length=max_length)
                lines[2] += ensure_length(str(int_menu_values[option]).zfill(width), max_length=max_length)
                lines[3] += ensure_length(colored("\u25BC"*width, color="grey" if int_menu_option == i else None, on_color="on_white" if int_menu_option == i else None), max_length=max_length)
            for line in lines: printw(" "*(os.get_terminal_size()[0]//2-len(strip_formattings(line).strip())//2) + line.strip())
            int_menu_alteration = False
        if int_menu_exit: break
        time.sleep(0.001)
    int_menu_option = int_menu_option_max = -1
    int_menu_alteration = True
    try:
        return int_menu_values
    finally:
        int_menu_values = {}


if __name__ == '__main__':
    """Where all the magic happens."""
    Listener(on_press=on_key_press, on_release=on_key_release).start()
    keyboard = Controller()
    import battleship   # Only reason I am manually importing these instead of going through all files in the same directory and just importing those by name
    import minesweeper  # is because PyInstaller wouldn't include them that way and I cannot get it to do it anyway. :)
    import sudoku       # But oh well, this works just as well anyway.
    import rps
    import hangman
    reg_game(battleship, minesweeper, sudoku, rps, hangman)
    try:
        while True:
            set_title("CLI Games")
            set_dims(60, orig_dims[1])
            clear_term()
            printw(f"You can always {colored('safely exit', 'green', attrs=['bold'])} from any point in any game and this menu by pressing {colored('escape', 'green', attrs=['underline'])}.")
            # Except for when you're playing battleship and it's the first round and you go first for some reason.
            # Or during minesweeper
            printw(f"you can also use {colored('escape', 'green', attrs=['underline'])} to {colored('skip intros', 'green', attrs=['bold'])}.")
            printw()
            game = menu("What game would you like to play?", list(games.keys()), cast=lambda ans: get_game(ans), color="green")
            clear_term()
            current_game = game
            game.play()
    except (KeyboardInterrupt, EOFError):
        exit_game()
