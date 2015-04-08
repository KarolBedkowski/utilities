#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
 pomidoro.py - Super-simple pomidoro timer
 Copyright (c) Karol Będkowski, 2015

 This is free software; you can redistribute it and/or modify it under the
 terms of the GNU General Public License as published by the Free Software
 Foundation; either version 2 of the License, or (at your option) any later
 version.

 This application is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
 for more details.

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""

__version__ = '0.1'
__date__ = '2015-04-08'
__author__ = 'Karol Będkowski'

import threading
import time
import functools

import Tkinter as tk
import tkMessageBox
import tkFont


class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self._dst = 0
        self._done = True
        self._quit = False
        self.grid()

        font = tkFont.Font(size=16, weight='bold')
        self._timer_label = tk.Label(self, text='00:00', font=font)
        self._timer_label.grid(columnspan=3, row=0, padx=5, pady=5)

        for idx, minutes in enumerate((5, 15, 25)):
            btn = tk.Button(
                self, text="%d min" % minutes,
                command=functools.partial(self._pomidoro, minutes))
            btn.grid(row=1, column=idx)

        self.master.protocol("WM_DELETE_WINDOW", self._on_quit)
        self._timer()

    def _pomidoro(self, minutes):
        self._done = False
        self._dst = time.time() + minutes * 60

    def _on_quit(self):
        self._quit = True
        self.master.quit()

    def _timer(self):
        if self._quit:
            return
        now = time.time()
        if self._dst <= now:
            if not self._done:
                self._done = True
                self.master.title('pomidoro.py')
                tkMessageBox.showinfo("pomidoro.py", "Done")
                self._timer_label.config(text='00:00')
        else:
            left = self._dst - now
            text = "%02d:%02d" % (left / 60, left % 60)
            self.master.title(text + ' pomidoro.py')
            self._timer_label.config(text=text)
        timer = threading.Timer(1, self._timer)
        timer.start()


def main():
    app = Application()
    app.master.title('pomidoro.py')
    app.mainloop()

if __name__ == "__main__":
    main()
