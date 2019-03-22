from Xlib import display, X

class EWMH:

  def __init__(self):
    self.display = display.Display()
    self.root    = self.display.screen().root

  def get_active_window(self):
    win = self.get_property('_NET_ACTIVE_WINDOW')
    return self.create_window(win[0]) if win else None

  def get_property(self, _type, win=None):
    win  = win or self.root
    atom = win.get_full_property(self.display.get_atom(_type), X.AnyPropertyType)

    return atom.value if atom else None

  def create_window(self, _id):
    return self.display.create_resource_object('window', _id)


class EWMHWindow:

  def __init__(self):
    self.ewmh   = EWMH()
    self.window = self.ewmh.get_active_window()

  def get_utf8_prop(self, property):
    result = self.ewmh.get_property(property, self.window)
    return result.decode('utf-8') if result else None

  def get_xid(self):
    result = self.ewmh.get_property('_NET_WM_PID', self.window)
    return result[0] if result else None

  def get_appname(self):
    name = self.window.get_wm_class()
    return list(name)[-1]
