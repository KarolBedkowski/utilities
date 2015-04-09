#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
 pomidoro.py - Super-simple pomodoro timer
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

import time
import functools

import Tkinter as tk
import tkMessageBox
import tkFont


class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self._dst = 0
        self._afterid_updateloop = None
        self.grid()

        font = tkFont.Font(size=16, weight='bold')
        self._timer_label = tk.Label(self, text='00:00', font=font)
        self._timer_label.grid(columnspan=4, row=0, padx=5, pady=5)

        for idx, minutes in enumerate((5, 15, 25)):
            btn = tk.Button(
                self, text="%d min" % minutes,
                command=functools.partial(self._start, minutes))
            btn.grid(row=1, column=idx)

        btn = tk.Button(self, text="Stop", command=self._stop)
        btn.grid(row=1, column=3)

        self.master.protocol("WM_DELETE_WINDOW", self._on_quit)
        self._stop()

    def _start(self, minutes):
        self._dst = time.time() + minutes * 60
        if not self._afterid_updateloop:
            self._timer()

    def _on_quit(self):
        self._stop()
        self.master.quit()

    def _stop(self):
        self._dst = 0
        self.master.title('pomidoro.py')
        self._timer_label.config(text='00:00')
        self._afterid_updateloop = None

    def _timer(self):
        now = time.time()
        self.master.update()
        if not self._dst:
            return
        if self._dst <= now:
            self._stop()
            tkMessageBox.showinfo("pomidoro.py", "Done")
            return
        left = self._dst - now
        text = "%0d:%02d" % (left / 60, left % 60)
        self.master.title(text + ' pomidoro.py')
        self._timer_label.config(text=text)
        diff = int(max(1000 - (time.time() - now) * 1000, 500))
        self._afterid_updateloop = self.master.after(diff, self._timer)


def main():
    app = Application()
    app.master.title('pomidoro.py')
    app.mainloop()

if __name__ == "__main__":
    main()
