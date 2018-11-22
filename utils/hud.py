#! /usr/bin/python3

import gi

gi.require_version('Keybinder', '3.0')

from gi.repository import Keybinder, GLib
from dbus.mainloop.glib import DBusGMainLoop

from rofi import RofiMenu


def hud(_keystr):
  try:
    rofi_menu = RofiMenu()
    rofi_menu.open()

  except AttributeError:
    return False


if __name__ == "__main__":
  DBusGMainLoop(set_as_default=True)

  Keybinder.init()
  Keybinder.bind('<Ctrl><Alt>space', hud)

  try:
    GLib.MainLoop().run()
  except KeyboardInterrupt:
    GLib.MainLoop().quit()
