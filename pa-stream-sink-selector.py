#!/usr/bin/python
# -*- coding: utf-8 -*-

import gtk
import gobject
import appindicator
import os
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from subprocess import call, check_call


class SinkRadioMenuItem(gtk.RadioMenuItem):

    def __init__(
        self,
        radioGroup,
        label,
        parse_underlines,
        streamPath,
        sinkPath,
        ):
        super(SinkRadioMenuItem, self).__init__(radioGroup, label,
                parse_underlines)
        self.streampath = streamPath
        self.sinkpath = sinkPath

    def getstream(self):
        return self.streampath

    def getsink(self):
        return self.sinkpath


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
        icon_path = os.path.abspath(os.path.dirname(__file__) + '/icon.svg');
        if not os.path.isfile(icon_path):
          icon_path = gtk.STOCK_INFO
        self.ind.set_icon(icon_path)
        try:
            self.conn = self.connect()
            self.core = \
                self.conn.get_object(object_path='/org/pulseaudio/core1'
                    )
        except dbus.exceptions.DBusException, err:
            print err
            raise

        for (sig_name, sig_handler) in (('NewSink', self.dbushandler),
                ('SinkRemoved', self.dbushandler), ('NewPlaybackStream',
                self.dbushandler), ('PlaybackStreamRemoved', self.dbushandler)):
            print self.core.ListenForSignal('org.PulseAudio.Core1.{}'.format(sig_name),
                    dbus.Array(signature='o'))
            print self.conn.add_signal_receiver(sig_handler,
                    signal_name=sig_name, member_keyword='member')

        self.menu = gtk.Menu()  # create a menu

        quitItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quitItem.connect('activate', self.quit)
        quitItem.show()
        self.menu.append(quitItem)

        self.makeMenuFromPulseAudio()

        self.menu.show()
        self.action()
        self.ind.set_menu(self.menu)

    def quit(self, widget, data=None):
        self.loop.quit()

    def makeMenuFromPulseAudio(self):
        for pstream in self.core.Get('org.PulseAudio.Core1',
                'PlaybackStreams',
                dbus_interface='org.freedesktop.DBus.Properties'):
            s = self.conn.get_object(object_path=pstream)
            streampropertyList = s.Get('org.PulseAudio.Core1.Stream',
                    'PropertyList',
                    dbus_interface='org.freedesktop.DBus.Properties')
            streamsplaybacksink = s.Get('org.PulseAudio.Core1.Stream',
                    'Device',
                    dbus_interface='org.freedesktop.DBus.Properties')

            appName = ''.join([chr(character) for character in
                              streampropertyList['application.name'
                              ]])[:-1]
            mediaName = ''.join([chr(character) for character in
                                streampropertyList['media.name']])[:-1]
            streamName = '%s: %s' % (appName, mediaName)

            subMenuItem = gtk.MenuItem(streamName)
            subMenu = gtk.Menu()

            radioGroup = None
            for sink in self.core.Get('org.PulseAudio.Core1', 'Sinks',
                    dbus_interface='org.freedesktop.DBus.Properties'):

                s = self.conn.get_object(object_path=sink)
                sinkpropertyList = s.Get('org.PulseAudio.Core1.Device',
                        'PropertyList',
                        dbus_interface='org.freedesktop.DBus.Properties'
                        )

                sinkDesc = ''.join([chr(character) for character in
                                   sinkpropertyList['device.description'
                                   ]])[:-1]
                radioItem = SinkRadioMenuItem(radioGroup, sinkDesc,
                        False, pstream, sink)
                if radioGroup == None:
                    radioGroup = radioItem
                radioItem.connect('activate', self.sinkPress)
                radioItem.show()
                if sink == streamsplaybacksink:
                    radioItem.set_active(True)
                subMenu.append(radioItem)
            subMenuItem.set_submenu(subMenu)
            subMenuItem.show()
            self.menu.prepend(subMenuItem)
            #self.menu.append(subMenuItem)

    def action(self):
        for pstream in self.core.Get('org.PulseAudio.Core1',
                'PlaybackStreams',
                dbus_interface='org.freedesktop.DBus.Properties'):

            # print pstream

            s = self.conn.get_object(object_path=pstream)
            streampropertyList = s.Get('org.PulseAudio.Core1.Stream',
                    'PropertyList',
                    dbus_interface='org.freedesktop.DBus.Properties')
            streamsplaybacksink = s.Get('org.PulseAudio.Core1.Stream',
                    'Device',
                    dbus_interface='org.freedesktop.DBus.Properties')

            # print propertyList

            #  [:-1] because the strings contained zero-bytes at the end

            appName = ''.join([chr(character) for character in
                              streampropertyList['application.name'
                              ]])[:-1]
            mediaName = ''.join([chr(character) for character in
                                streampropertyList['media.name']])[:-1]
            streamName = '%s: %s' % (appName, mediaName)
            print '%s: %s' % (streamName, pstream)
            prePend = ' ' * len(streamName)
            for sink in self.core.Get('org.PulseAudio.Core1', 'Sinks',
                    dbus_interface='org.freedesktop.DBus.Properties'):
                prePend = ' ' * len(streamName)
                if sink == streamsplaybacksink:
                    prePend = prePend + ' -> '
                else:
                    prePend = prePend + '    '

                s = self.conn.get_object(object_path=sink)
                sinkName = s.Get('org.PulseAudio.Core1.Device', 'Name',
                                 dbus_interface='org.freedesktop.DBus.Properties'
                                 )
                sinkpropertyList = s.Get('org.PulseAudio.Core1.Device',
                        'PropertyList',
                        dbus_interface='org.freedesktop.DBus.Properties'
                        )

                # print sinkpropertyList

                for key in sinkpropertyList:
                    print '%s: %s' % (key, ''.join([chr(character)
                            for character in
                            sinkpropertyList[key]])[:-1])

                print '%s%s (%s)' % (prePend, sinkName, sink)

    def sinkPress(self, widget, data=None):
        if isinstance(widget, SinkRadioMenuItem) \
            and widget.get_active():
            print 'Move %s to %s' % (widget.getstream(),
                    widget.getsink())
            s = self.conn.get_object(object_path=widget.getstream())
            interface = dbus.Interface(s, 'org.PulseAudio.Core1.Stream')
            interface.Move(widget.getsink())

    def dbushandler(self, sender=None, member=None):
        print 'got signal from %s, message %s' % (sender, member)
        for i in self.menu.get_children(): # This is ugly
            if isinstance(i, gtk.MenuItem) and i.get_submenu() != None:
                self.menu.remove(i) # So ugly
        self.makeMenuFromPulseAudio() # I feel bad


def main():
    DBusGMainLoop(set_as_default=True)
    loop = gobject.MainLoop()
    AppIndicatorExample(loop)
    loop.run()
    return 0


if __name__ == '__main__':
    main()
