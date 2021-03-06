#! /usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
##                                                                           ##
##  Copyright 2010-2012, Neil Wallace <neil@openmolar.com>                   ##
##                                                                           ##
##  This program is free software: you can redistribute it and/or modify     ##
##  it under the terms of the GNU General Public License as published by     ##
##  the Free Software Foundation, either version 3 of the License, or        ##
##  (at your option) any later version.                                      ##
##                                                                           ##
##  This program is distributed in the hope that it will be useful,          ##
##  but WITHOUT ANY WARRANTY; without even the implied warranty of           ##
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            ##
##  GNU General Public License for more details.                             ##
##                                                                           ##
##  You should have received a copy of the GNU General Public License        ##
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.    ##
##                                                                           ##
###############################################################################

import re
from PyQt4 import QtGui, QtCore

class ChartLineEdit(QtGui.QLineEdit):
    '''
    A custom line edit that accepts only BLOCK LETTERS
    and is self aware when verification is needed
    override the keypress event for up and down arrow keys.
    '''

    edit_finished = QtCore.pyqtSignal(object)
    '''
    this is a signal emitted when user has finished entering an item.
    argument will be ("next", "prev" or "stay")
    '''

    def __init__(self, parent=None):
        QtGui.QLineEdit.__init__(self, parent)

    def clear(self):
        '''
        clears the text
        '''
        self.setText("")

    @property
    def trimmed_text(self):
        return self.text().trimmed()

    def keyPressEvent(self, event):
        '''
        overrides QWidget's keypressEvent
        '''
        if event.key() == QtCore.Qt.Key_Space:
            self.edit_finished.emit("stay")
        elif self.text() == "" and event.key() in (
        QtCore.Qt.Key_Left, QtCore.Qt.Key_Right,
        QtCore.Qt.Key_Down, QtCore.Qt.Key_Up):
            self.emit(QtCore.SIGNAL("Nav_key"), event)
        elif event.key() in (
            QtCore.Qt.Key_Down,
            QtCore.Qt.Key_Return):
                self.edit_finished.emit("next")
        elif event.key() == QtCore.Qt.Key_Up:
            self.edit_finished.emit("prev")
        else:
            inputT = event.text().toAscii()
            if re.match("[a-z]", inputT):
                #-- catch and overwrite any lower case
                event = QtGui.QKeyEvent(event.type(), event.key(),
                event.modifiers(), event.text().toUpper())
            QtGui.QLineEdit.keyPressEvent(self,event)

if __name__ == "__main__":

    def sig_catcher(*args):
        print "signal caught", args

    app = QtGui.QApplication([])
    obj = ChartLineEdit()
    obj.edit_finished.connect(sig_catcher)

    obj.show()
    app.exec_()