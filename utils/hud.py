#! /usr/bin/python3

import gi

gi.require_version('Keybinder', '3.0')

from gi.repository import Keybinder, GLib
from dbus.mainloop.glib import DBusGMainLoop

from rofi import RofiMenu
from menu import DbusMenu

def hud(_keystr):
  try:
    dbus_menu = DbusMenu()
    rofi_menu = RofiMenu(dbus_menu.actions, dbus_menu.prompt)

    dbus_menu.activate(rofi_menu.selection)
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
