#! /usr/bin/python3

import gi

gi.require_version('Keybinder', '3.0')

from gi.repository import Keybinder, GLib

from rofi import RofiMenu


def hud(_keystr):
  rofi_menu = RofiMenu()
  rofi_menu.open()


if __name__ == "__main__":
  Keybinder.init()
  Keybinder.bind('<Ctrl><Alt>space', hud)

  try:
    GLib.MainLoop().run()
  except KeyboardInterrupt:
    GLib.MainLoop().quit()
