#!/usr/bin/python3

import gi
import dbus
import dbus.service
import setproctitle

from gi.repository import GLib
from dbus.mainloop.glib import DBusGMainLoop


class HudMenuService(dbus.service.Object):

	def __init__(self):
		bus_name = dbus.service.BusName('org.gnome.HudMenu', bus = dbus.SessionBus())
		dbus.service.Object.__init__(self, bus_name, '/org/gnome/HudMenu')
		self.window_dict = dict()

	@dbus.service.method('org.gnome.HudMenu', in_signature='uo', sender_keyword='sender')

	def RegisterWindow(self, windowId, menuObjectPath, sender):
		self.window_dict[windowId] = (sender, menuObjectPath)

	@dbus.service.method('org.gnome.HudMenu', in_signature='u', out_signature='so')

	def GetMenuForWindow(self, windowId):
		if windowId in self.window_dict:
			sender, menuObjectPath = self.window_dict[windowId]
		return [dbus.String(sender), dbus.ObjectPath(menuObjectPath)]

	@dbus.service.method('org.gnome.HudMenu')

	def Q(self):
		GLib.MainLoop().quit()

if __name__ == "__main__":
	setproctitle.setproctitle('gnome-hud-service')
	DBusGMainLoop(set_as_default=True)
	gnome_hud_service = HudMenuService()
	GLib.MainLoop().run()
