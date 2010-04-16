#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ft=python et softtabstop=4 cinoptions=4 shiftwidth=4 ts=4 ai

"""
Copyright(C) 2010  Romain Bignon, Christophe Benz

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

"""

from weboob.capabilities.bank import ICapBank
from weboob.capabilities.messages import ICapMessages, ICapMessagesReply
from weboob.capabilities.travel import ICapTravel
from weboob.tools.application import BaseApplication

class Dummy(BaseApplication):
    APPNAME = 'dummy'

    def main(self, argv):
        self.weboob.load_backends()

        for backend in self.weboob.iter_backends():
            print 'Backend [%s]' % backend.name
            if backend.has_caps(ICapMessages):
                print '|- ICapMessages        [Print its messages]'
                for message in backend.iter_messages():
                    print '|  |- %s' % message
            if backend.has_caps(ICapMessagesReply):
                print '|- ICapMessagesReply   [TODO]'
            if backend.has_caps(ICapTravel):
                print '|- ICapTravel.stations [Search station \'defense\']'
                s = None
                for station in backend.iter_station_search('defense'):
                    print '|  |- [%s] %s' % (station.id, station.name)
                    if s is None:
                        s = station.id
                print '|- ICapTravel.departures [Departures from \'%s\']' % s
                for departure in backend.iter_station_departures(s):
                    print '|  |- [%s] %s at %s to %s' % (departure.id, departure.type, departure.time.strftime("%H:%M"),
                                                         departure.arrival_station)
            if backend.has_caps(ICapBank):
                for account in backend.iter_accounts():
                    print '|  |- [%s] label=%s balance=%s coming=%s' % (
                        account.id, account.label, account.balance, account.coming)
