#!/usr/bin/python
# -*- coding: utf-8 -*-

import gtk
import gobject
import appindicator
import os
import sys
import dbus
from dbus.mainloop.glib import DBusGMainLoop
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
            self.bus = dbus.SessionBus()
            server_lookup = self.bus.get_object('org.PulseAudio1',
                    '/org/pulseaudio/server_lookup1')
            address = server_lookup.Get('org.PulseAudio.ServerLookup1',
                    'Address',
                    dbus_interface='org.freedesktop.DBus.Properties')
        return dbus.connection.Connection(address)

    def __init__(self, loop):
        self.loop = loop
        self.ind = appindicator.Indicator('example-simple-client',
                'indicator-messages',
                appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_attention_icon('indicator-messages-new')
        self.ind.set_icon(gtk.STOCK_INFO)
        try:
            self.conn = self.connect()
            self.conn.call_on_disconnection(self.handler)
            self.core = \
                self.conn.get_object(object_path='/org/pulseaudio/core1'
                    )
        except dbus.exceptions.DBusException, err:
            print err
            raise

        for sig_name, sig_handler in (
                ('NewSink', self.handler),
                ('SinkRemoved', self.handler),
                ('NewPlaybackStream', self.handler),
                ('PlaybackStreamRemoved', self.handler)):
            print self.core.ListenForSignal('org.PulseAudio.Core1.{}'
                .format(sig_name), dbus.Array(signature='o'))
            print self.conn.add_signal_receiver(sig_handler, signal_name=sig_name, member_keyword='member')

        self.menu = gtk.Menu()  # create a menu

        # create items for the menu - labels, checkboxes, radio buttons and images are supported:

        #item = gtk.MenuItem('Regular Menu Item')
        #item.connect('activate', self.action1)
        #item.show()
        #self.menu.append(item)

        #filem = gtk.MenuItem('Open submenu')

        #filemenu = gtk.Menu()

        #check = gtk.MenuItem('Action on submenu')
        #check.connect('activate', self.action2)
        #check.show()
        #filemenu.append(check)

        #filemenu.show()

        #filem.set_submenu(filemenu)
        #filem.show()
        #self.menu.append(filem)

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
        #gtk.main_quit()
        self.loop.quit()

    def action(self):
        for pstream in self.core.Get('org.PulseAudio.Core1',
                'PlaybackStreams',
                dbus_interface='org.freedesktop.DBus.Properties'):
            #print pstream
            s = self.conn.get_object(object_path=pstream)
            streampropertyList = s.Get('org.PulseAudio.Core1.Stream',
                                 'PropertyList',
                                 dbus_interface='org.freedesktop.DBus.Properties'
                                 )
            streamsplaybacksink = s.Get('org.PulseAudio.Core1.Stream',
                                 'Device',
                                 dbus_interface='org.freedesktop.DBus.Properties'
                                 )
            # print propertyList
            # [:-1] because the strings contained zero-bytes at the end

            appName = ''.join([chr(character) for character in
                              streampropertyList['application.name']])[:-1]
            mediaName = ''.join([chr(character) for character in
                                streampropertyList['media.name']])[:-1]
            streamName = '%s: %s' % (appName, mediaName)
            print "%s: %s" % (streamName, pstream)
            prePend = ' ' * len(streamName)
            for sink in self.core.Get('org.PulseAudio.Core1', 'Sinks',
                                  dbus_interface='org.freedesktop.DBus.Properties'
                                  ):
                prePend = ' ' * len(streamName)
                if(sink == streamsplaybacksink):
                    prePend = prePend + ' -> '
                else:
                    prePend = prePend + '    '

                s = self.conn.get_object(object_path=sink)
                sinkName = s.Get('org.PulseAudio.Core1.Device', 'Name',
                            dbus_interface='org.freedesktop.DBus.Properties')
                sinkpropertyList = s.Get('org.PulseAudio.Core1.Device',
                                 'PropertyList',
                                 dbus_interface='org.freedesktop.DBus.Properties'
                                 )
                #print sinkpropertyList
                for key in sinkpropertyList:
                    print "%s: %s" % (key, ''.join([chr(character) for character in
                                sinkpropertyList[key]])[:-1])

                print "%s%s (%s)" %(prePend, sinkName, sink)

            #if 'Chromium' in appName:
            #    print 'Found Chromium'



    def action1(self, widget, data=None):
        self.action()

    def action2(self, widget, data=None):
        print 'action2: %s', widget

    def action3(self, widget, data=None):
        print 'action3: %s', widget

    def handler(self, sender=None, member=None):
        print "got signal from %s, message %s" % (sender, member)

def main():
    DBusGMainLoop(set_as_default=True)
    loop = gobject.MainLoop()
    AppIndicatorExample(loop)
    loop.run()
    return 0


if __name__ == '__main__':
    main()
