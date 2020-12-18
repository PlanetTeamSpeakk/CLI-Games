from __main__ import *
from typing import Final
import random
import time
from termcolor import colored
from pynput.keyboard import KeyCode
import string

__name__ = "Hangman"
phases: tuple[str, ...] = ('''\
         
         
         
         
         
         
=========''', '''\
  
      |  
      |  
      |  
      |  
      |  
=========''', '''\
  +---+  
  |   |  
      |  
      |  
      |  
      |  
=========''', '''\
  +---+  
  |   |  
  O   |  
      |  
      |  
      |  
=========''', '''\
  +---+  
  |   |  
  O   |  
  |   |  
      |  
      |  
=========''', '''\
  +---+  
  |   |  
  O   |  
 /|   |  
      |  
      |  
=========''', '''\
  +---+  
  |   |  
  O   |  
 /|\\  |  
      |  
      |  
=========''', '''\
  +---+  
  |   |  
  O   |  
 /|\\  |  
 /    |  
      |  
=========''', '''\
  +---+  
  |   |  
  O   |  
 /|\\  |  
 / \\  |  
      |  
=========''')
words: Final[tuple[str, ...]] = tuple(line.strip().lower() for line in open(resource_path("hangman_words.txt"), "r").readlines())
word: str or None = None
letterscatter: list[str] = []
update: bool = False


def on_key_press(key):
    """Called by the main on_key_press function whenever a key gets pressed on the OS."""
    if isinstance(key, KeyCode) and key.char in string.ascii_letters and not key.char.lower() in letterscatter:
        i = -1
        while i == -1 or letterscatter[i] != " ":
            i = random.randint(0, len(letterscatter)-1)
        letterscatter[i] = key.char.lower()
        global update
        update = True


def determine_phase() -> int:
    """Determines the phase of the poor soul who's hanging."""
    phase = 0
    for letter in letterscatter:
        if letter is not " " and letter not in word: phase += 1
    return phase


def check_win() -> int:
    """Checks whether the player has won or lost yet."""
    return 2 if determine_phase() == len(phases)-1 else int(sum(letter in letterscatter for letter in str(word)) == len(str(word)))


def print_field(reveal=False):
    """Prints the hangman field."""
    printw()
    lines = phases[determine_phase()].split("\n")
    for line in lines:
        print((15-len(line)//2)*" " + line)
    print()
    s = ""
    global word
    word = str(word)
    for i in range(len(word)):
        s += word[i] if word[i] in letterscatter else "_" if not reveal else colored(word[i], color="red")
    print()
    print((15-len(word)//2)*" " + s)
    print()
    s = ""
    for i, letter in enumerate(letterscatter):
        s += (letter if letter not in word else " ") + ("\n" if i % (len(letterscatter) // 3) == 0 else "")
    for line in s.split("\n"):
        print((15 - len(letterscatter)//3 // 2) * " " + line)


def play():
    """Play Hangman"""
    global word, letterscatter, update
    letterscatter = [" "] * 20*3
    word = random.choice(words)
    set_dims(30, 20)
    update = True
    while True:
        if update:
            clear_term()
            win = check_win()
            print_field(win == 2)
            if win:
                print("You " + colored("won" if win == 1 else "lost", color="green" if win == 1 else "red") + "!")
                pause()
                break
            update = False
        time.sleep(0.001)
