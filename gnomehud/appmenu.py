#! /usr/bin/python3

from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop
from gnomehud.utils.service import AppMenuService


def main():
  DBusGMainLoop(set_as_default=True)
  AppMenuService()

  try:
    GLib.MainLoop().run()
  except KeyboardInterrupt:
    GLib.MainLoop().quit()


if __name__ == "__main__":
  main()
