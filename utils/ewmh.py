from array import array
from Xlib import display, X, protocol


class EWMH:

	def __init__(self, _display=None, root=None):
		self.display = _display or display.Display()
		self.root = root or self.display.screen().root

	def get_active_window(self):
		active_window = self.get_property('_NET_ACTIVE_WINDOW')

		if not active_window:
			return None

		return self.create_window(active_window[0])

	def get_property(self, _type, win=None):
		win = win or self.root
		atom = win.get_full_property(self.display.get_atom(_type), X.AnyPropertyType)

		if not atom:
			return None

		return atom.value

	def set_property(self, _type, data, win=None, mask=None):
		win = win or self.root

		if type(data) is str:
			dataSize = 8
		else:
			data = (data+[0]*(5-len(data)))[:5]
			dataSize = 32

		event = protocol.event.ClientMessage(
			window=win,
			client_type=self.display.get_atom(_type),
			data=(dataSize, data)
		)

		if not mask:
			mask = (X.SubstructureRedirectMask | X.SubstructureNotifyMask)

		self.root.send_event(event, event_mask=mask)

	def create_window(self, _id):
		if not _id:
			return None

		return self.display.create_resource_object('window', _id)


class ActiveWindow:

	def __init__(self):
		self.ewmh = EWMH()
		self.window = self.ewmh.get_active_window()
		self.pid = self.get_window_pid()
		self.name = self.get_window_name()
		self.bus_name = self.get_window_bus_name()
		self.app_path = self.get_application_object_path()
		self.win_path = self.get_window_object_path()
		self.menubar_path = self.get_menubar_object_path()
		self.appmenu_path = self.get_appmenu_object_path()

	def get_window_pid(self):
		window_pid = self.ewmh.get_property('_NET_WM_PID', self.window)

		if not window_pid:
			return None

		return window_pid[0]

	def get_window_name(self):
		name = self.window.get_wm_class()
		name = list(name)[-1]

		return name

	def get_window_bus_name(self):
		bus_name = self.ewmh.get_property('_GTK_UNIQUE_BUS_NAME', self.window)

		if not bus_name:
			return None

		return bus_name.decode('utf-8')

	def get_application_object_path(self):
		object_path = self.ewmh.get_property('_GTK_APPLICATION_OBJECT_PATH', self.window)

		if not object_path:
			return None

		return object_path.decode('utf-8')

	def get_window_object_path(self):
		object_path = self.ewmh.get_property('_GTK_WINDOW_OBJECT_PATH', self.window)

		if not object_path:
			return None

		return object_path.decode('utf-8')

	def get_menubar_object_path(self):
		object_path = self.ewmh.get_property('_GTK_MENUBAR_OBJECT_PATH', self.window)

		if not object_path:
			return None

		return object_path.decode('utf-8')

	def get_appmenu_object_path(self):
		object_path = self.ewmh.get_property('_GTK_APP_MENU_OBJECT_PATH', self.window)

		if not object_path:
			return None

		return object_path.decode('utf-8')

	def close(self):
		self.ewmh.set_property('_NET_CLOSE_WINDOW', [X.CurrentTime, 1], self.window)
		self.ewmh.display.flush()

	def destroy(self):
		self.window.destroy()
		self.ewmh.display.flush()
