#! /usr/bin/python3

import gi

gi.require_version('Keybinder', '3.0')

from gi.repository import Keybinder, GLib
from dbus.mainloop.glib import DBusGMainLoop

from utils.ewmh import ActiveWindow
from utils.rofi import RofiMenu
from utils.menu import DbusMenu

def gnome_hud(_keystr):
  try:
    window = ActiveWindow()
    dbus_menu = DbusMenu(window)
    rofi_menu = RofiMenu(dbus_menu.actions, window.name)

    dbus_menu.activate_menu_item(rofi_menu.selection)
  except AttributeError:
    return False


if __name__ == "__main__":
  DBusGMainLoop(set_as_default=True)

  Keybinder.init()
  Keybinder.bind('<Ctrl><Alt>space', gnome_hud)

  try:
    GLib.MainLoop().run()
  except KeyboardInterrupt:
    GLib.MainLoop().quit()
