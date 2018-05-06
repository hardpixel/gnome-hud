import dbus

class DbusMenu:

  def __init__(self, window):
    self.window = window
    self.session = dbus.SessionBus()
    self.menu_items = dict()
    self.menu_actions = dict()

    self.explore_paths()
    self.explore_items()

  @property

  def actions(self):
    return self.menu_actions.keys()

  def activate(self, selection):
    if selection:
      self.activate_item(selection)

  def activate_item(self, selection):
    action = self.menu_actions.get(selection, 'sys.quit')

    if 'sys.' in action:
      self.window.close()

    elif 'app.' in action:
      app_object = self.session.get_object(self.window.bus_name, self.window.app_path)
      app_iface = dbus.Interface(app_object, dbus_interface='org.gtk.Actions')

      app_iface.Activate(action.replace('app.', ''), [], dict())

    elif 'win.' in action:
      win_object = self.session.get_object(self.window.bus_name, self.window.win_path)
      win_iface = dbus.Interface(win_object, dbus_interface='org.gtk.Actions')

      win_iface.Activate(action.replace('win.', ''), [], dict())

    elif 'unity.' in action:
      mnb_object = self.session.get_object(self.window.bus_name, self.window.menubar_path)
      mnb_iface = dbus.Interface(mnb_object, dbus_interface='org.gtk.Actions')

      mnb_iface.Activate(action.replace('unity.', ''), [], dict())

  def explore_paths(self):
    paths = [self.window.appmenu_path, self.window.menubar_path]

    for path in filter(None, paths):
      pobject = self.session.get_object(self.window.bus_name, path)
      interface = dbus.Interface(pobject, dbus_interface='org.gtk.Menus')
      results = interface.Start([x for x in range(1024)])

      for result in results:
        self.menu_items[(result[0], result[1])] = result[2]

  def explore_items(self, menu_id=None, labels=None):
    menu_id = menu_id or (0, 0)
    labels = labels or list()

    for menu in self.menu_items.get(menu_id, list()):
      if 'label' in menu:
        label = menu['label']
        new_labels = labels + [label]
        form_label = self.format_labels(new_labels)

        if 'action' in menu:
          menu_action = menu['action']

          if ':section' not in menu and ':submenu' not in menu:
            self.menu_actions[form_label] = menu_action

      if ':section' in menu:
        section = menu[':section']
        section_id = (section[0], section[1])
        self.explore_items(section_id, labels)

      if ':submenu' in menu:
        submenu = menu[':submenu']
        submenu_id = (submenu[0], submenu[1])
        self.explore_items(submenu_id, new_labels)

  def format_labels(self, labels):
    separator = u'\u0020\u0020\u00BB\u0020\u0020'
    head, *tail = labels
    result = head

    for label in tail:
      result = result + separator + label

    result = result.replace('Root >', '')
    result = result.replace('_', '')

    return result.strip()
