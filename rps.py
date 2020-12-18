from __main__ import *
from typing import Final
import time
import os
import random
from termcolor import colored
from pynput.keyboard import Key, KeyCode

__name__ = "Rock Paper Scissors"
rock_ascii: Final[str] = """\
    _______  
---'   ____) 
      (_____)
      (_____)
      (____) 
---.__(___)  \
"""
paper_ascii: Final[str] = """\
    _______       
---'   ____)____  
          ______) 
          _______)
         _______) 
---.__________)   \
"""
scissors_ascii: Final[str] = """\
    _______       
---'   ____)____  
          ______) 
       __________)
      (____)      
---.__(___)       \
"""

rockm_ascii: Final[str] = """\
  _______    
 (____   '---
(_____)      
(_____)      
 (____)      
  (___)__.---\
"""
paperm_ascii: Final[str] = """\
       _______    
  ____(____   '---
 (______          
(_______          
 (_______         
   (__________.---\
"""
scissorsm_ascii: Final[str] = """\
       _______    
  ____(____   '---
 (______          
(__________       
      (____)      
       (___)__.---\
"""


impossible = False
player_selection = -1
selection_made = False
player_points = bot_points = 0
ignore_input = False
ignore_input0 = False


def play_animation(player_choice, bot_choice):
    """Plays the animation of the hands going up and down."""
    global ignore_input, ignore_input0
    ignore_input = ignore_input0 = True
    merged_rocks = merge_strings(rock_ascii, rockm_ascii)
    merged = merge_strings(player_choice, bot_choice)
    skip = False
    for i in range(6):
        if skip and i != 5: continue
        try:
            clear_term()
            if i % 2 == 1: print()
            print(merged if i == 5 else merged_rocks)
            time.sleep(0.4)
        except (KeyboardInterrupt, EOFError):
            skip = True
    time.sleep(0.6)
    ignore_input = False


def merge_strings(s1, s2):
    """Merges two multiline strings together so their lines are on the same line."""
    merged = []
    lines1 = s1.split("\n")
    lines2 = s2.split("\n")
    for i in range(min(len(lines1), len(lines2))):
        merged.append(ensure_length(lines1[i], max_length=os.get_terminal_size()[0] - len(lines2[i]), append=True) + lines2[i])
    return "\n".join(merged)


def on_key_press(key):
    """Called by the main on_key_press function whenever a key is pressed on the OS."""
    global player_selection, selection_made, ignore_input, ignore_input0
    if player_selection != -1 and not selection_made and not ignore_input0:
        if key == Key.left or isinstance(key, KeyCode) and key.char == 'a':
            player_selection -= 1
        elif key == Key.right or isinstance(key, KeyCode) and key.char == 'd':
            player_selection += 1
        elif key == Key.enter or key == Key.space:
            selection_made = True
        if player_selection < 0: player_selection += 3
        elif player_selection > 2: player_selection -= 3
    if not ignore_input: ignore_input0 = False


def player_pick():
    """Lets the player pick either rock, paper or scissors."""
    printw("Pick your poison (use left and right arrow keys, press enter to select)")
    global player_selection, selection_made
    player_selection = 0
    current_selection = -1
    print("\n"*6)
    while True:
        if not player_selection == current_selection:
            current_selection = player_selection
            clear_lines(6)
            choice = rock_ascii if current_selection == 0 else paper_ascii if current_selection == 1 else scissors_ascii
            for line in choice.split("\n"):
                print(" "*(os.get_terminal_size()[0]//2-len(line)//2) + colored(line, color="grey", on_color="on_white"))
        if selection_made:
            clear_lines(6)
            player_choice = itos(player_selection)
            bot_choice = bot_pick(player_choice)
            play_animation(stoascii(player_choice, False), stoascii(bot_choice, True))
            won = has_won(player_choice, bot_choice)
            print()
            print("You " + (colored("won", color="green") if won == 1 else colored("lost", color="red")) + "!" if won != 2 else "It's a tie!")
            global bot_points, player_points
            if won == 0: bot_points += 1
            elif won == 1: player_points += 1
            selection_made = False
            pause()
            break
        time.sleep(0.001)
    player_selection = -1


def itos(i: int) -> str:
    """Turns an integer between 0 and 2 inclusive to its corresponding letter."""
    return "rps"[i]


def stoascii(s: str, mirrored: bool) -> str:
    """Turns a letter to its corresponding ascii art, can optionally also returned the mirrored version."""
    return (rock_ascii if not mirrored else rockm_ascii) if s == "r" else (paper_ascii if not mirrored else paperm_ascii) if s == "p" else (scissors_ascii if not mirrored else scissorsm_ascii)


def bot_pick(player_choice: str) -> str:
    """Let the bot pick either rock, paper or scissors.
    Returns whatever option wins if the difficulty is set to impossible."""
    return random.choice("rps") if not impossible else "r" if player_choice == "s" else "p" if player_choice == "r" else "s"


def has_won(player_choice, bot_choice) -> int:
    """Checks if either the bot or the player won or if a tie occurred."""
    return 2 if player_choice == bot_choice else 1 if (player_choice == "r" and not bot_choice == "p" or player_choice == "p" and not bot_choice == "s" or player_choice == "s" and not bot_choice == "r") else 0


def play():
    """Play Rock Paper Scissors"""
    set_dims(50, 15)
    global impossible, player_points, bot_points, ignore_input
    ignore_input = False
    player_points = bot_points = 0
    impossible = menu("Choose a difficulty.", "Normal", "Impossible", cast=lambda ans: ans.lower() == "impossible", color="green")
    clear_term()
    while True:
        printw("CURRENT SCORE: " + colored(str(player_points), color="green") + " - " + colored(str(bot_points), color="red"), end="\n\n")
        player_pick()
        clear_term()
