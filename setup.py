import setuptools

with open('README.md', 'r') as fh:
  long_description = fh.read()

setuptools.setup(
  name='gnomehud',
  version='1.0.0',
  author='Jonian Guveli',
  author_email='jonian@hardpixel.eu',
  description='Unity like HUD menu for the GNOME Desktop Environment',
  long_description=long_description,
  long_description_content_type='text/markdown',
  url='https://github.com/hardpixel/gnome-hud',
  packages=setuptools.find_packages(),
  data_files=[
    ('share/applications', ['gnomehud.desktop', 'gnomehud-rofi.desktop'])
  ],
  install_requires=[
    'PyGObject>=3.30.0',
    'dbus-python>=1.2.8'
  ],
  classifiers=[
    'Programming Language :: Python :: 3',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Operating System :: POSIX :: Linux'
  ],
  project_urls={
    'Bug Reports': 'https://github.com/hardpixel/gnome-hud/issues',
    'Source': 'https://github.com/hardpixel/gnome-hud',
  },
  entry_points={
    'console_scripts': [
      'gnomehud = gnomehud.command:main',
      'gnomehud-rofi = gnomehud.command:rofi',
      'gnomehud-service = gnomehud.appmenu:main'
    ]
  }
)