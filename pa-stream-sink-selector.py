#!/usr/bin/python
# -*- coding: utf-8 -*-

import gtk
import appindicator
import os
import sys
import dbus
from subprocess import call, check_call


class AppIndicatorExample:

    def connect(self):
        if call('pactl list modules short | grep module-dbus-protocol',
                shell=True) == 1:
            print '[WARNING] loading module-dbus-protocol into PA'
            check_call(['pactl', 'load-module', 'module-dbus-protocol'])
        else:
            print '[INFO] dbus-module was already loaded'
        if 'PULSE_DBUS_SERVER' in os.environ:
            address = os.environ['PULSE_DBUS_SERVER']
        else:
            bus = dbus.SessionBus()
            server_lookup = bus.get_object('org.PulseAudio1',
                    '/org/pulseaudio/server_lookup1')
            address = server_lookup.Get('org.PulseAudio.ServerLookup1',
                    'Address',
                    dbus_interface='org.freedesktop.DBus.Properties')
        return dbus.connection.Connection(address)

    def __init__(self):
        self.ind = appindicator.Indicator('example-simple-client',
                'indicator-messages',
                appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_attention_icon('indicator-messages-new')
        self.ind.set_icon('distributor-logo')
        try:
            self.conn = self.connect()
            self.core = \
                self.conn.get_object(object_path='/org/pulseaudio/core1'
                    )
            print 'Successfully connected to ' \
                + self.core.Get('org.PulseAudio.Core1', 'Name',
                                dbus_interface='org.freedesktop.DBus.Properties'
                                ) + '!'
        except dbus.exceptions.DBusException, err:
            print err
            raise

        self.menu = gtk.Menu()  # create a menu

        # create items for the menu - labels, checkboxes, radio buttons and images are supported:

        item = gtk.MenuItem('Regular Menu Item')
        item.connect('activate', self.action1)
        item.show()
        self.menu.append(item)

        filem = gtk.MenuItem('Open submenu')

        filemenu = gtk.Menu()

        check = gtk.MenuItem('Action on submenu')
        check.connect('activate', self.action2)
        check.show()
        filemenu.append(check)

        filemenu.show()

        filem.set_submenu(filemenu)
        filem.show()
        self.menu.append(filem)

        image = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
        image.connect('activate', self.action3)
        image.show()
        self.menu.append(image)

        image2 = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        image2.connect('activate', self.quit)
        image2.show()
        self.menu.append(image2)

        self.menu.show()
        self.action()
        self.ind.set_menu(self.menu)

    def quit(self, widget, data=None):
        gtk.main_quit()

    def action(self):
        print 'SINKS:'
        for sink in self.core.Get('org.PulseAudio.Core1', 'Sinks',
                                  dbus_interface='org.freedesktop.DBus.Properties'
                                  ):
            print sink
            s = self.conn.get_object(object_path=sink)
            print s.Get('org.PulseAudio.Core1.Device', 'Name',
                        dbus_interface='org.freedesktop.DBus.Properties'
                        )

        print
        print 'SOURCES:'
        for source in self.core.Get('org.PulseAudio.Core1', 'Sources',
                                    dbus_interface='org.freedesktop.DBus.Properties'
                                    ):
            print source
            s = self.conn.get_object(object_path=source)
            print s.Get('org.PulseAudio.Core1.Device', 'Name',
                        dbus_interface='org.freedesktop.DBus.Properties'
                        )

            # print

        print 'PLAYBACKSTREAMS:'
        for pstream in self.core.Get('org.PulseAudio.Core1',
                'PlaybackStreams',
                dbus_interface='org.freedesktop.DBus.Properties'):
            print pstream
            s = self.conn.get_object(object_path=pstream)
            propertyList = s.Get('org.PulseAudio.Core1.Stream',
                                 'PropertyList',
                                 dbus_interface='org.freedesktop.DBus.Properties'
                                 )

            # print propertyList
            # [:-1] because the strings contained zero-bytes at the end

            appName = ''.join([chr(character) for character in
                              propertyList['application.name']])[:-1]
            mediaName = ''.join([chr(character) for character in
                                propertyList['media.name']])[:-1]
            print '%s: %s\n' % (appName, mediaName)
            if 'Chromium' in appName:
                print 'Found Chromium'

                # Move source
                # interface = dbus.Interface(s, 'org.PulseAudio.Core1.Stream')
                # interface.Move("/org/pulseaudio/core1/sink1")

                propertyList = s.Get('org.PulseAudio.Core1.Stream',
                        'PropertyList',
                        dbus_interface='org.freedesktop.DBus.Properties'
                        )

    def action1(self, widget, data=None):
        self.action()

    def action2(self, widget, data=None):
        print 'action2: %s', widget

    def action3(self, widget, data=None):
        print 'action3: %s', widget


def main():
    gtk.main()
    return 0


if __name__ == '__main__':
    indicator = AppIndicatorExample()
    main()
