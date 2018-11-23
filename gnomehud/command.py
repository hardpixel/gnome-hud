#! /usr/bin/python3

import os
import sys
import threading

from gnomehud.handlers.default import HudMenu
from gnomehud.handlers.rofi import RofiMenu


def run_command(module, function):
  args = 'python3 -c "from gnomehud.%s import %s as run; run()"'
  args = args % (module, function)

  proc = threading.Thread(target=os.system, args=[args])
  proc.start()


def run_hud_menu(menu):
  run_command('appmenu', 'main')
  run_command('keybinder', menu)


def default_hud_menu(*args):
  menu = HudMenu()
  menu.run()


def rofi_hud_menu(*args):
  menu = RofiMenu()
  menu.run()


def main():
  if sys.stdin.isatty():
    run_hud_menu('main')
  else:
    default_hud_menu()


def rofi():
  if sys.stdin.isatty():
    run_hud_menu('rofi')
  else:
    rofi_hud_menu()


if __name__ == "__main__":
  main()
