# -*- coding: utf-8 -*-

# Copyright(C) 2008-2010  Romain Bignon
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import re
from datetime import datetime
from dateutil import tz
from logging import error, warning
from mechanize import FormNotFoundError

from weboob.backends.aum.pages.base import PageBase
from weboob.backends.aum.exceptions import AdopteCantPostMail
from weboob.capabilities.messages import Message

class MailParser(Message):

    """
    <td>
        <table width="100%">
            <tr valign="top">
                <td width="1" bgcolor="black">
                <td width="88" align="center">
                    <table class=a onclick="window.location='romainn'" style="background:url(http://img.adopteunmec.com/img/bg_mini.png);width:74px;height:85px">
                        <tr height=4>
                            <td></td>
                        </tr>
                        <tr valign=top height=66>
                            <td width=74 align=center style="-moz-opacity:0.5;opacity:0.5">
                                <table class=a onclick="window.location='romainn'" style="width:66px;background-image:url(http://p7.adopteunmec.com/7/7/0/8/7/4/thumb0_3.jpg);background-repeat:no-repeat">
                                    <tr height=2><td></td></tr>
                                    <tr height=31 valign=top>
                                        <td width=2></td>
                                        <td align=left><img width=7 heght=7 src='http://img.adopteunmec.com/img/i/null.png'id=status_ /></td>
                                    </tr>
                                    <tr height=31 valign=bottom>
                                        <td width=2></td>
                                        <td width=63 align=right id=online_>
                                            <blnk><blink><img src="http://img.adopteunmec.com/img/online0.png" width=7 height=7  /></blink></blnk>
                                            <img src="http://img.adopteunmec.com/img/online1.png" width=25 height=10  />
                                        </td>
                                        <td width=3></td>
                                    </tr>
                                    <tr height=2><td></td></tr>
                                    <tr><td colspan=10 align=center style="font-size:10px;font-weight:bold;letter-spacing:-1px">Romain</td></tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
                <td>
                    <p style="color:#444444;font-size:10px">27 octobre 2008, 01:11:32, nouveau
                    <br />
                    </p>
                    <br>Moi en g�n�ral j'aime sortir tout simplement dans des bars, pour discuter avec mes amis et/ou coll�gues, et rencontrer des gens. Sinon je fais de la guitare, et je d�veloppe des projets perso.</p>
                </td>
                <td width="1" bgcolor="black">
            </tr>
            <tr height="6"><td width="1" bgcolor="black"><td colspan="2"></td><td width="1" bgcolor="black"></tr>

        </table>
    </td>
    """

    DATETIME_REGEXP = re.compile(u'([0-9]{1,2}) ([a-zéû]*) ([0-9]{4}), ([0-9]{2}):([0-9]{2}):([0-9]{2})(.*)')
    months = [u'', u'janvier', u'février', u'mars', u'avril', u'mai', u'juin', u'juillet', u'août', u'septembre', u'octobre', u'novembre', u'décembre']
    SMILEY_REGEXP = re.compile('http://s.adopteunmec.com/img/smile/([0-9]+).gif')
    smileys = {0: ':)',
               1: ':D',
               2: ':o',
               3: ':p',
               4: ';)',
               5: ':(',
               6: ':$',
               7: ':\'(',
               11: ':#',
               14: ':\\',
               15: ':|',
               10: '(L)',
              }

    def __init__(self, id, name, tr):
        #             <td>             <table>  implicit<tbody>  <tr>
        Message.__init__(self, id, 0, 'Discussion with %s' % name, name)
        self.tr = tr.childNodes[0].childNodes[1].childNodes[0].childNodes[0]

        tds = self.tr.childNodes

        counter = 0
        for td in tds:
            if not hasattr(td, 'tagName') or td.tagName != u'td':
                continue

            counter += 1

            if counter == 3:
                date = u''
                for child in td.childNodes[1].childNodes:
                    if hasattr(child, 'data'):
                        date += child.data
                self.parse_date(date)
                content = ''
                for c in td.childNodes[3].childNodes:
                    if hasattr(c, 'data'):
                        content += ''.join(c.data.split('\n')) # to strip \n
                    elif hasattr(c, 'tagName'):
                        if c.tagName == 'br':
                            content += '\n'
                        elif c.tagName == 'img' and c.hasAttribute('src'):
                            m = self.SMILEY_REGEXP.match(c.getAttribute('src'))
                            if m and self.smileys.has_key(int(m.group(1))):
                                try:
                                    content += self.smileys[int(m.group(1))]
                                except KeyError:
                                    error('Mail: unable to find this smiley: %s' % c.getAttribute('src'))
                self.content = content
                break

        self.parse_profile_link()
        self.parse_from()

    def set_reply_id(self, date):
        self.reply_id = date

    def parse_date(self, date_str):
        # To match regexp, we have to remove any return chars in string
        # before the status ('nouveau', 'lu', etc)
        date_str = u''.join(date_str.split(u'\n'))

        m = self.DATETIME_REGEXP.match(date_str)
        if m:
            day = int(m.group(1))
            month = self.months.index(m.group(2))
            year = int(m.group(3))
            hour = int(m.group(4))
            minute = int(m.group(5))
            sec = int(m.group(6))
            # build datetime object with local timezone
            d = datetime(year, month, day, hour, minute, sec, tzinfo=tz.tzlocal())
            # then, convert it to UTC timezone
            d = d.astimezone(tz.tzutc())
            # and get timestamp
            self.date = d
            self.id = self.get_date_int()

            if m.group(7).find('nouveau') >= 0:
                self.is_new = True
        else:
            error('Error: unable to parse the datetime string "%s"' % date_str)

    def parse_profile_link(self):
        tables = self.tr.getElementsByTagName('div')

        for table in tables:
            if table.hasAttribute('class') and table.getAttribute('class') == 'mini' and table.hasAttribute('onclick'):

                text = table.getAttribute('onclick')

                regexp = re.compile("window.location='(.*)'")
                m = regexp.match(text)

                if m:
                    self.profile_link = m.group(1)
                    self.signature = u'Profile: http://www.adopteunmec.com%s' % self.profile_link
                    return

        warning('Unable to find the profile URL in the message %s@%s' % (self.get_from(), self.get_id()))

    def parse_from(self):
        tds = self.tr.getElementsByTagName('div')

        for td in tds:
            if not td.hasAttribute('class') or td.getAttribute('class') != 'mini_pseudo':
                continue

            if td.childNodes:
                self.sender = td.childNodes[0].data

            return

        warning('Warning: unable to find from in the mail %s' % self.get_id())

class ContactThreadPage(PageBase):

    """
<form name=sendMsg method="post" action="/thread.php?id=1567992">
<table align=center width=700>
<tr valign="top"><td width=370 align="left">
        <table width=370>
        <tr height=25 style="background:url(http://img.adopteunmec.com/img/bg_list1.gif)"><td colspan=4>&nbsp;&nbsp;<font color=#ff0198>Ecrire � <big><b>zoe</b></big></font></td></tr>
        <tr height=193 valign=top><td width=1 bgcolor=black></td><td colspan=2 bgcolor=white><textarea id=message name=message style="width:366px;height:190px;border:none"></textarea></td><td width=1 bgcolor=black></td></tr>
        <tr height=1><td width=1 bgcolor=black></td><td bgcolor="#d15c91" colspan=2></td><td width=1 bgcolor=black></td></tr>
        <tr height=1><td width=1 bgcolor=black></td><td bgcolor="#ffffff" colspan=2></td><td width=1 bgcolor=black></td></tr>
        <tr><td width=1 bgcolor=black></td><td bgcolor="#ffe8f3">
                <table><tr>
                        <td width=8></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/0.gif" style="cursor:pointer" onclick="emote(':)')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/1.gif" style="cursor:pointer" onclick="emote(':D')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/2.gif" style="cursor:pointer" onclick="emote(':o')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/3.gif" style="cursor:pointer" onclick="emote(':p')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/4.gif" style="cursor:pointer" onclick="emote(';)')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/5.gif" style="cursor:pointer" onclick="emote(':(')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/6.gif" style="cursor:pointer" onclick="emote(':$')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/7.gif" style="cursor:pointer" onclick="emote(':\'(')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/11.gif" style="cursor:pointer" onclick="emote(':#')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/14.gif" style="cursor:pointer" onclick="emote(':\\')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/15.gif" style="cursor:pointer" onclick="emote(':|')"></td>
                        <td width=23><img src="http://img.adopteunmec.com/img/smile/10.gif" style="cursor:pointer" onclick="emote('(L)')"></td>
                </tr></table>
        </td><td bgcolor="#ffe8f3" align=right><input type="image" src="http://img.adopteunmec.com/img/buttonSendMail.jpg" style="border:none"></td><td width=1 bgcolor=black></td></tr>
        <tr height=1><td width=1 bgcolor=black colspan=4></tr>
        </table>
</td><td width=304 align="right">
        <iframe frameborder=0 scrolling=NO style='width:300px;height:250px;boder:0' src='http://graphs.adopteunmec.com/ads/index.php?i=5'></iframe>
</td></tr>
</table>
<input type=hidden id=link name=link>
</form>
    """

    def post(self, content):
        try:
            self.browser.select_form(name="sendMsg")
            if isinstance(content, unicode):
                content = content.encode('iso-8859-15', 'replace')
            self.browser['message'] = content

            self.browser.submit()  # submit current form
        except FormNotFoundError, e:
            error = 'Unknown error (%s)' % e
            p_list = self.document.getElementsByTagName('p')
            for p in p_list:
                if p.hasAttribute('align') and p.getAttribute('align') == 'center':
                    error = p.firstChild.data
                    break

            raise AdopteCantPostMail(error)


    """
<table align=center style="width:700px;background:black">
    <tr style="height:1px">
        <td>
        </td>
    </tr>
    <tr bgcolor="#ffe9f6" valign="top">
        content
    </tr>
    ...
    <tr height="25" style="background:url(http://img.adopteunmec.com/img/bg_list1.gif)"><td>&nbsp;&nbsp;<a href="/thread.php?id=1567992&see=all">voir tous les messages</a></td></tr>
</table>

    """

    id_regexp = re.compile("/thread.php\?id=([0-9]+)")

    def on_loaded(self):
        self.items = []

        a_list = self.document.getElementsByTagName('a')
        self.id = 0
        for a in a_list:
            if a.hasAttribute('href'):
                m = self.id_regexp.match(a.getAttribute('href'))
                if m:
                    self.id = int(m.group(1))
                    break

        self.name = ''
        big_list = self.document.getElementsByTagName('big')
        for big in big_list:
            child = big.firstChild
            if hasattr(child, 'tagName') and child.tagName == u'b':
                self.name = child.firstChild.data
                break

        tables = self.document.getElementsByTagName('table')
        table = None
        for t in tables:
            if t.hasAttribute('style') and t.getAttribute('style') == 'width:700px;background:black':
                table = t
                break

        if not table:
            # It is probably the 'sent' page
            return

        for tag in table.childNodes[1].childNodes[1:]:
            if not hasattr(tag, 'tagName') or tag.tagName != u'tr':
                continue

            if not tag.hasAttribute('valign'):
                continue

            mail = MailParser(self.id, self.name, tag)

            if self.items:
                self.items[-1].set_reply_id(mail.get_date_int())
            self.items += [mail]

    def get_id(self):
        return self.id

    def get_mails(self):
        return self.items
