#! /usr/bin/python3

import gi
import dbus
import psutil
import subprocess
import inflection

gi.require_version('Gtk', '3.0')
gi.require_version('Keybinder', '3.0')

from gi.repository import Keybinder, GLib, Gtk
from dbus.mainloop.glib import DBusGMainLoop
from Xlib import display, X


class EWMH:

	def __init__(self, _display=None, root=None):
		self.display = _display or display.Display()
		self.root = root or self.display.screen().root

	def get_active_window(self):
		active_window = self.get_property('_NET_ACTIVE_WINDOW')

		if active_window is None:
			return None

		return self.create_window(active_window[0])

	def get_property(self, _type, win=None):
		if not win:
			win = self.root

		atom = win.get_full_property(self.display.get_atom(_type), X.AnyPropertyType)

		if atom:
			return atom.value

	def create_window(self, window_id):
		if not window_id:
			return None

		return self.display.create_resource_object('window', window_id)


class HudMenu:

	def __init__(self, menu_keys, prompt):
		self.menu_items = self.parse_items(menu_keys)
		self.prompt = self.parse_prompt(prompt)
		self.menu = self.open_menu()

	def rgba_to_hex(self, color):
		red = int(color.red * 255)
		green = int(color.green * 255)
		blue = int(color.blue * 255)

		return "#{0:02x}{1:02x}{2:02x}".format(red, green, blue)

	def parse_items(self, menu_keys):
		string, *menu_items = menu_keys

		for menu_item in menu_items:
			string += '\n' + menu_item

		return string.encode('utf-8')

	def parse_prompt(self, prompt):
		prompt = prompt.split('.')[0]

		if len(prompt) < 2:
			prompt = ''
		else:
			prompt = prompt + ':'

		return inflection.titleize(prompt)

	def gtk_theme_colors(self):
		window = Gtk.Window()
		style_context = window.get_style_context()
		gtk_theme_colors = {
			'bg': style_context.lookup_color('theme_bg_color')[1],
			'fg': style_context.lookup_color('theme_fg_color')[1],
			'selected_bg': style_context.lookup_color('theme_selected_bg_color')[1],
			'selected_fg': style_context.lookup_color('theme_selected_fg_color')[1],
			'error_bg': style_context.lookup_color('error_bg_color')[1],
			'error_fg': style_context.lookup_color('error_fg_color')[1],
			'info_bg': style_context.lookup_color('info_bg_color')[1],
			'unfocused_fg': style_context.lookup_color('theme_unfocused_fg_color')[1],
			'unfocused_bg': style_context.lookup_color('theme_unfocused_bg_color')[1]
		}

		for name, color in gtk_theme_colors.items():
			gtk_theme_colors[name] = self.rgba_to_hex(color)

		return gtk_theme_colors

	def theme_colors(self):
		gtk_colors = self.gtk_theme_colors()
		theme_colors = {
			'window': [
				gtk_colors['bg'],
				gtk_colors['unfocused_fg'],
				gtk_colors['unfocused_fg']
			],
			'normal': [
				gtk_colors['bg'],
				gtk_colors['fg'],
				gtk_colors['bg'],
				gtk_colors['selected_bg'],
				gtk_colors['selected_fg']
			],
			'urgent': [
				gtk_colors['bg'],
				gtk_colors['fg'],
				gtk_colors['bg'],
				gtk_colors['error_bg'],
				gtk_colors['error_fg']
			]
		}

		for name, colors in theme_colors.items():
			theme_colors[name] = ', '.join(colors)

		return theme_colors

	def open_menu(self):
		settings = Gtk.Settings.get_default()
		font_name = settings.get_property('gtk-font-name')
		theme_colors = self.theme_colors()

		settings = [
			'rofi', '-dmenu', '-i', '-location', '2', '-width', '100',
			'-hide-scrollbar', '-lines', '12', '-color-enabled',
			'-p', self.prompt, '-font', font_name,
			'-color-window', theme_colors['window'],
			'-color-normal', theme_colors['normal'],
			'-color-urgent', theme_colors['urgent']
		]

		menu = subprocess.Popen(settings, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		menu.stdin.write(self.menu_items)

		return menu

	def get_selection(self):
		selection = self.menu.communicate()[0].decode('utf8').rstrip()
		self.menu.stdin.close()

		return selection


def format_label_list(label_list):
	separator = u'\u0020\u0020\u00BB\u0020\u0020'
	head, *tail = label_list
	result = head

	for label in tail:
		result = result + separator + label

	return result.replace('Root > ', '').replace('_', '')


def try_gtk_interface(bus_name, app_path, win_path, appmenu_path, menubar_path, prompt):
	if bus_name is None or app_path is None or win_path is None:
		return

	if appmenu_path is None and menubar_path is None:
		return

	session_bus = dbus.SessionBus()
	bus_name = bus_name.decode('utf-8')
	app_path = app_path.decode('utf-8')
	win_path = win_path.decode('utf-8')
	app_object = session_bus.get_object(bus_name, app_path)
	app_iface = dbus.Interface(app_object, dbus_interface='org.gtk.Actions')
	win_object = session_bus.get_object(bus_name, win_path)
	win_iface = dbus.Interface(win_object, dbus_interface='org.gtk.Actions')

	app_menus = dict()
	app_menus_actions = dict()

	if appmenu_path:
		appmenu_path = appmenu_path.decode('utf-8')
		appmenu_object = session_bus.get_object(bus_name, appmenu_path)
		appmenu_iface = dbus.Interface(appmenu_object, dbus_interface='org.gtk.Menus')
		appmenu_results = appmenu_iface.Start([x for x in range(1024)])

		for appmenu_result in appmenu_results:
			app_menus[(appmenu_result[0], appmenu_result[1])] = appmenu_result[2]

	if menubar_path:
		menubar_path = menubar_path.decode('utf-8')
		menubar_object = session_bus.get_object(bus_name, menubar_path)
		menubar_iface = dbus.Interface(menubar_object, dbus_interface='org.gtk.Menus')
		menubar_results = menubar_iface.Start([x for x in range(1024)])

		for menubar_result in menubar_results:
			app_menus[(menubar_result[0], menubar_result[1])] = menubar_result[2]

	def explore_menu(menu_id, label_list):
		if menu_id in app_menus:
			for menu in app_menus[menu_id]:
				if 'label' in menu:
					menu_label = menu['label']
					new_label_list = label_list + [menu_label]
					formatted_label = format_label_list(new_label_list)

					if 'action' in menu:
						menu_action = menu['action']

						if ':section' not in menu and ':submenu' not in menu:
							app_menus_actions[formatted_label] = menu_action

				if ':section' in menu:
					menu_section = menu[':section']
					section_menu_id = (menu_section[0], menu_section[1])
					explore_menu(section_menu_id, label_list)

				if ':submenu' in menu:
					menu_submenu = menu[':submenu']
					submenu_menu_id = (menu_submenu[0], menu_submenu[1])
					explore_menu(submenu_menu_id, new_label_list)

	explore_menu((0,0), [])

	menu_keys = sorted(app_menus_actions.keys())
	hudmenu = HudMenu(menu_keys, prompt)
	selection = hudmenu.get_selection()
	action = app_menus_actions.get(selection, False)

	if action and 'app.' in action:
		app_iface.Activate(action.replace('app.', ''), [], dict())

	if action and 'win.' in action:
		win_iface.Activate(action.replace('win.', ''), [], dict())


def hud(_keystr):
	ewmh = EWMH()
	win = ewmh.get_active_window()
	window_pid = ewmh.get_property('_NET_WM_PID', win)[0]
	prompt = psutil.Process(window_pid).name()
	bus_name = ewmh.get_property('_GTK_UNIQUE_BUS_NAME', win)
	app_path = ewmh.get_property('_GTK_APPLICATION_OBJECT_PATH', win)
	win_path = ewmh.get_property('_GTK_WINDOW_OBJECT_PATH', win)
	menubar_path = ewmh.get_property('_GTK_MENUBAR_OBJECT_PATH', win)
	appmenu_path = ewmh.get_property('_GTK_APP_MENU_OBJECT_PATH', win)

	try_gtk_interface(bus_name, app_path, win_path, appmenu_path, menubar_path, prompt)


if __name__ == "__main__":
	DBusGMainLoop(set_as_default=True)
	Keybinder.init()
	Keybinder.bind('<Ctrl><Alt>space', hud)

	try:
		GLib.MainLoop().run()
	except KeyboardInterrupt:
		GLib.MainLoop().quit()
