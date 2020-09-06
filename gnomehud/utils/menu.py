import time
import dbus

from gnomehud.utils.shell import ShellWindow
from gnomehud.utils.bamf import BamfWindow
from gnomehud.utils.shell import is_wayland
from gnomehud.utils.fuzzy import match_replace


def active_window():
  if is_wayland():
    return ShellWindow()
  else:
    return BamfWindow()


def format_label(parts):
  separator = u'\u0020\u0020\u00BB\u0020\u0020'
  return separator.join(parts)


def normalize_label(text):
  text = match_replace('_|\.\.\.|…', '', text)
  text = match_replace('\s+', ' ', text)

  return text.strip()


class DbusGtkMenuItem(object):

  def __init__(self, item, path=[]):
    self.path   = path
    self.action = str(item.get('action', ''))
    self.accel  = str(item.get('accel', ''))
    self.label  = normalize_label(item.get('label', ''))
    self.text   = format_label(self.path + [self.label])


class DbusGtkMenu(object):

  def __init__(self, session, window):
    self.results      = {}
    self.actions      = {}
    self.session      = session
    self.bus_name     = window.get_utf8_prop('_GTK_UNIQUE_BUS_NAME')
    self.app_path     = window.get_utf8_prop('_GTK_APPLICATION_OBJECT_PATH')
    self.win_path     = window.get_utf8_prop('_GTK_WINDOW_OBJECT_PATH')
    self.menubar_path = window.get_utf8_prop('_GTK_MENUBAR_OBJECT_PATH')
    self.appmenu_path = window.get_utf8_prop('_GTK_APP_MENU_OBJECT_PATH')

  def activate(self, selection):
    action = self.actions.get(selection, '')

    if 'app.' in action:
      self.send_action(action, 'app.', self.app_path)
    elif 'win.' in action:
      self.send_action(action, 'win.', self.win_path)
    elif 'unity.' in action:
      self.send_action(action, 'unity.', self.menubar_path)

  def send_action(self, name, prefix, path):
    object    = self.session.get_object(self.bus_name, path)
    interface = dbus.Interface(object, dbus_interface='org.gtk.Actions')

    interface.Activate(name.replace(prefix, ''), [], dict())

  def get_results(self):
    self.results = {}
    self.actions = {}

    for path in filter(None, [self.appmenu_path, self.menubar_path]):
      object    = self.session.get_object(self.bus_name, path)
      interface = dbus.Interface(object, dbus_interface='org.gtk.Menus')
      results   = interface.Start([x for x in range(1024)])

      for menu in results:
        self.results[(menu[0], menu[1])] = menu[2]

    self.collect_entries([0, 0])

  def collect_entries(self, menu, labels=[]):
    for menu in self.results.get((menu[0], menu[1]), []):
      if 'label' in menu:
        menu_item = DbusGtkMenuItem(menu, labels)
        menu_path = labels + [menu_item.label]

        if ':submenu' in menu:
          self.collect_entries(menu[':submenu'], menu_path)
        elif 'action' in menu:
          self.actions[menu_item.text] = menu_item.action

      elif ':section' in menu:
        self.collect_entries(menu[':section'], labels)


class DbusAppMenuItem(object):

  def __init__(self, item, path=[]):
    self.path   = path
    self.action = int(item[0])
    self.accel  = item[1].get('shortcut', '')
    self.label  = normalize_label(item[1].get('label', ''))
    self.text   = format_label(self.path + [self.label])


class DbusAppMenu(object):

  def __init__(self, session, window):
    self.actions   = {}
    self.session   = session
    self.xid       = window.get_xid()
    self.interface = self.get_interface()

  def activate(self, selection):
    action = self.actions[selection]

    self.interface.Event(action, 'clicked', 0, 0)
    self.close_level1_items()

  def close_level1_items(self):
    items = self.interface.GetLayout(0, 1, ['label'])[1]

    for item in items[2]:
      self.interface.Event(item[0], 'closed', 'not used', dbus.UInt32(time.time()))

  def get_interface(self):
    bus_name = 'com.canonical.AppMenu.Registrar'
    bus_path = '/com/canonical/AppMenu/Registrar'

    try:
      object     = self.session.get_object(bus_name, bus_path)
      interface  = dbus.Interface(object, bus_name)
      name, path = interface.GetMenuForWindow(self.xid)
      object     = self.session.get_object(name, path)
      interface  = dbus.Interface(object, 'com.canonical.dbusmenu')

      return interface
    except dbus.exceptions.DBusException:
      return None

  def get_results(self):
    self.actions = {}

    if self.interface:
      results = self.interface.GetLayout(0, -1, ['children-display'])
      self.expand_menus(results[1])

      results = self.interface.GetLayout(0, -1, ['label'])
      self.collect_entries(results[1], [])

  def expand_menus(self, item=None):
    item_id    = item[0]
    item_props = item[1]

    if 'children-display' in item_props:
      try:
        self.interface.AboutToShow(item_id)
        self.interface.Event(item_id, 'opened', 'not used', dbus.UInt32(time.time()))
      except dbus.exceptions.DBusException:
        alert = 'Failed to expand submenu children!'
        print('Gnome HUD: WARNING: (AppMenu) %s' % alert)

    if len(item[2]):
      for child in item[2]:
        self.expand_menus(child)

  def collect_entries(self, item=None, labels=[]):
    menu_item = DbusAppMenuItem(item, labels)
    menu_path = labels

    if bool(menu_item.label) and menu_item.label != 'Root':
      menu_path = labels + [menu_item.label]

    if len(item[2]):
      for child in item[2]:
        self.collect_entries(child, menu_path)

    elif bool(menu_item.label):
      self.actions[menu_item.text] = menu_item.action


class DbusPlotinusMenuItem(object):

  def __init__(self, item):
    self.path   = list(item['Path'])[1:]
    self.action = int(item['Id'])
    self.accel  = list(item['Accelerators'])
    self.label  = normalize_label(item['Label'])
    self.text   = format_label(self.path + [self.label])


class DbusPlotinusMenu(object):

  def __init__(self, session, window):
    self.actions   = {}
    self.session   = session
    self.win_path  = window.get_utf8_prop('_GTK_WINDOW_OBJECT_PATH')
    self.interface = self.get_interface()

  def activate(self, selection):
    self.actions[selection].Execute()

  def get_interface(self):
    bus_name = 'com.worldwidemann.plotinus'
    bus_path = '/com/worldwidemann/plotinus'

    try:
      object    = self.session.get_object(bus_name, bus_path)
      interface = dbus.Interface(object, dbus_interface=bus_name)

      return interface
    except dbus.exceptions.DBusException:
      return None

  def get_results(self):
    self.actions = {}

    if self.interface and self.win_path:
      name, paths = self.interface.GetCommands(self.win_path)
      commands    = [self.session.get_object(name, path) for path in paths]

      for command in commands:
        self.collect_entries(command)

  def collect_entries(self, command):
    interface  = dbus.Interface(command, dbus_interface='org.freedesktop.DBus.Properties')
    command    = dbus.Interface(command, dbus_interface='com.worldwidemann.plotinus.Command')
    properties = interface.GetAll('com.worldwidemann.plotinus.Command')
    menu_item  = DbusPlotinusMenuItem(properties)

    self.actions[menu_item.text] = command


class DbusMenu:

  def __init__(self):
    self.session  = dbus.SessionBus()
    self.window   = active_window()
    self.gtkmenu  = DbusGtkMenu(self.session, self.window)
    self.appmenu  = DbusAppMenu(self.session, self.window)
    self.plotinus = DbusPlotinusMenu(self.session, self.window)

  @property

  def prompt(self):
    return self.window.get_appname()

  @property

  def actions(self):
    self.appmenu.get_results()
    actions = self.appmenu.actions

    if not bool(actions):
      self.plotinus.get_results()
      actions = self.plotinus.actions

    if not bool(actions):
      self.gtkmenu.get_results()
      actions = self.gtkmenu.actions

    if not bool(actions):
      alert = 'No menu items available!'
      print('Gnome HUD: WARNING: (%s) %s' % (self.prompt, alert))

    return actions.keys()

  def activate(self, selection):
    if selection in self.gtkmenu.actions:
      self.gtkmenu.activate(selection)

    elif selection in self.appmenu.actions:
      self.appmenu.activate(selection)

    elif selection in self.plotinus.actions:
      self.plotinus.activate(selection)
