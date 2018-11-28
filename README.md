# Gnome HUD
Unity like HUD menu for the GNOME Desktop Environment.

### Screenshots
HUD menu running with the default menu handler (GTK3).

![Screenshot](/screenshot.png)

HUD menu running with the [Rofi](https://github.com/DaveDavenport/rofi) menu handler.

![Settings](/screenshot-rofi.png)

## Dependencies
```
gtk3 bamf linkeybinder3 python python-gobject python-dbus
```

## Installation
Install the package with the Python Package Index using `pip` command.
```
pip install gnome-hud
```

### Post installation
After the package installation, follow the instructions below:

- Install bamf daemon (It is strongly recommend to add bamf daemon to autostart)
- Install GTK module using instructions below
- To get QT menus to work, install your distribution's qt4 and qt5 appmenu packages

**UBUNTU**

* Install [unity-gtk-module](https://launchpad.net/unity-gtk-module) with `sudo apt-get install unity-gtk2-module unity-gtk3-module`
* Follow instructions in [appmenu-gtk-module](https://github.com/rilian-la-te/vala-panel-appmenu/blob/master/subprojects/appmenu-gtk-module/README.md), but replace any occurence of `appmenu-gtk-module` to `unity-gtk-module`

**ARCH LINUX**

* Install [appmenu-gtk-module](https://www.archlinux.org/packages/community/x86_64/appmenu-gtk-module) for GTK appmenu support
* Install [appmenu-qt4](https://www.archlinux.org/packages/community/x86_64/appmenu-qt4) for Qt4 appmenu support
* Install [libdbusmenu-gtk2](https://www.archlinux.org/packages/community/x86_64/libdbusmenu-gtk2) and [libdbusmenu-gtk3](https://www.archlinux.org/packages/community/x86_64/libdbusmenu-gtk3) for GTK2 and GTK3 dbusmenu support
* Install [libdbusmenu-qt4](https://www.archlinux.org/packages/extra/x86_64/libdbusmenu-qt4) and [libdbusmenu-qt5](https://www.archlinux.org/packages/extra/x86_64/libdbusmenu-qt5) for Qt4 and Qt5 dbusmenu support

*The post installation instructions above are adapted from [Vala Panel Application Menu](https://github.com/rilian-la-te/vala-panel-appmenu).*

### Packages
Arch Linux: [AUR package](https://aur.archlinux.org/packages/gnome-hud)

## Usage
After the installation is completed, you will have 3 executables and a gnomehud.desktop file available.

* Open the GTK3 menu dialog with `gnomehud`
* Open the Rofi menu dialog with `gnomehud-rofi`
* Start the AppMenu service with `gnomehud-service`

The desktop file launches `gnomehud-service` and can be used to add it to the startup applications in gnome-tweaks. The dialog commands can be used for custom keyboard shortcuts in keyboard settings.

When running the dialog commands from a terminal the keybinding is <kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>Space</kbd>.

## Contributing
Bug reports and pull requests are welcome on GitHub at https://github.com/hardpixel/gnome-hud.

## License
Gnome HUD is available as open source under the terms of the [GPLv3](http://www.gnu.org/licenses/gpl-3.0.en.html)
