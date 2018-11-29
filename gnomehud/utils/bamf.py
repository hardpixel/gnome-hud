import gi

gi.require_version('Bamf', '3')

from gi.repository import Bamf
from gi.repository import Gio


class BamfWindow(object):

  def __init__(self):
    self.matcher = Bamf.Matcher.get_default()
    self.app     = self.matcher.get_active_application()
    self.window  = self.matcher.get_active_window()

  def get_utf8_prop(self, property):
    return self.window.get_utf8_prop(property)

  def get_xid(self):
    return self.window.get_xid()

  def get_appname(self):
    app  = self.matcher.get_active_application()
    file = app.get_desktop_file()
    info = Gio.DesktopAppInfo.new_from_filename(file)

    return info.get_string('Name')
