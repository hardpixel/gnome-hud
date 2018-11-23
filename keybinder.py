#! /usr/bin/python3

import gi

gi.require_version('Keybinder', '3.0')

from gi.repository import Keybinder, GLib
from utils.rofi import RofiMenu


def hud_menu(_keystr):
  rofi_menu = RofiMenu()
  rofi_menu.run()


if __name__ == "__main__":
  Keybinder.init()
  Keybinder.bind('<Ctrl><Alt>space', hud_menu)

  try:
    GLib.MainLoop().run()
  except KeyboardInterrupt:
    GLib.MainLoop().quit()
