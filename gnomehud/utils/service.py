import dbus
import dbus.service

from gi.repository import GLib

BUS_NAME = 'com.canonical.AppMenu.Registrar'
BUS_PATH = '/com/canonical/AppMenu/Registrar'


class AppMenuService(dbus.service.Object):
  def __init__(self):
    self.window_dict = dict()

    bus_name = dbus.service.BusName(BUS_NAME, bus=dbus.SessionBus())
    dbus.service.Object.__init__(self, bus_name, BUS_PATH)

  @dbus.service.method(BUS_NAME, in_signature='uo', sender_keyword='sender')

  def RegisterWindow(self, windowId, menuObjectPath, sender):
    self.window_dict[windowId] = (sender, menuObjectPath)

  @dbus.service.method(BUS_NAME, in_signature='u', out_signature='so')

  def GetMenuForWindow(self, windowId):
    if windowId in self.window_dict:
      sender, menuObjectPath = self.window_dict[windowId]
      return [dbus.String(sender), dbus.ObjectPath(menuObjectPath)]

  @dbus.service.method(BUS_NAME)

  def Q(self):
    GLib.MainLoop().quit()
