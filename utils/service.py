#! /usr/bin/python3

import dbus
import dbus.service

from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop

service_name = 'com.canonical.AppMenu.Registrar'
service_path = '/com/canonical/AppMenu/Registrar'


class AppMenuService(dbus.service.Object):
  def __init__(self):
    self.window_dict = dict()

    bus_name = dbus.service.BusName(service_name, bus=dbus.SessionBus())
    dbus.service.Object.__init__(self, bus_name, service_path)

  @dbus.service.method(service_name, in_signature='uo', sender_keyword='sender')

  def RegisterWindow(self, windowId, menuObjectPath, sender):
    self.window_dict[windowId] = (sender, menuObjectPath)

  @dbus.service.method(service_name, in_signature='u', out_signature='so')

  def GetMenuForWindow(self, windowId):
    if windowId in self.window_dict:
      sender, menuObjectPath = self.window_dict[windowId]
      return [dbus.String(sender), dbus.ObjectPath(menuObjectPath)]

  @dbus.service.method(service_name)

  def Q(self):
    GLib.MainLoop().quit()


if __name__ == "__main__":
  DBusGMainLoop(set_as_default=True)
  AppMenuService()

  try:
    GLib.MainLoop().run()
  except KeyboardInterrupt:
    GLib.MainLoop().quit()
