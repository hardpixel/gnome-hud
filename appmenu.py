#! /usr/bin/python3

from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
from utils.service import AppMenuService


if __name__ == "__main__":
  DBusGMainLoop(set_as_default=True)
  AppMenuService()

  try:
    GLib.MainLoop().run()
  except KeyboardInterrupt:
    GLib.MainLoop().quit()
