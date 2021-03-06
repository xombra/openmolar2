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

from PyQt4 import QtCore, QtGui, QtSql

from lib_openmolar.common.datatypes import OMTypes

from lib_openmolar.common.qt4.dialogs import BaseDialog
from lib_openmolar.common.qt4.widgets.upper_case_lineedit import UpperCaseLineEdit

from lib_openmolar.client.qt4.dialogs.address_dialogs.select_address \
    import AddressSelectionDialog

from lib_openmolar.client.db_orm import AddressRecord

class NewAddressDialog(BaseDialog):
    '''
    *TODO* - fix this dialog, it is broken
    '''
    def __init__(self, parent=None):
        '''
        2 arguments
            1. the database into which the new address will go.
            2. parent widget(optional)
        '''
        BaseDialog.__init__(self, parent)
        self.setWindowTitle(_("New address"))

        label = QtGui.QLabel(_('Enter a New Address'))
        label.setWordWrap(True)
        label.setAlignment(QtCore.Qt.AlignCenter)

        widget = QtGui.QWidget()
        self.form = QtGui.QFormLayout(widget)

        self.insertWidget(label)
        self.insertWidget(widget)

        self.enableApply()
        self.set_accept_button_text(_("Create New Record"))

        self.address_record = AddressRecord() # A blank record
        '''
        A pointer to the dialog's :doc:`AddressRecord`
        '''
        self.address_record.setValue("modified_by", SETTINGS.user)
        self.address_record.setValue("status", "active")

        self.value_store = {}

        # keep a list of required values the user hasn't completed
        self.ommissions = []

        palette = QtGui.QPalette(self.palette())
        brush = QtGui.QBrush(SETTINGS.COLOURS.REQUIRED_FIELD)
        palette.setBrush(QtGui.QPalette.Base, brush)

        standard_fields, advanced_fields = self.address_record.editable_fields

        for editable_field in standard_fields:
            field_name = editable_field.fieldname
            display_text = editable_field.readable_fieldname
            field = self.address_record.field(field_name)

            if editable_field.type is None:
                field_type = field.type()
            else:
                field_type = editable_field.type

            if field_type == QtCore.QVariant.Date:
                widg = QtGui.QDateEdit(self)
                widg.setDate(field.value().toDate())

            elif field_type == QtCore.QVariant.String:
                widg = UpperCaseLineEdit(self)
                widg.setText(field.value().toString())

            elif type(field_type) == OMType:
                widg = QtGui.QComboBox(self)
                for val in field_type.allowed_values:
                    widg.addItem(field_type.readable_dict[val], val)
                index = widg.findData(field.value())
                widg.setCurrentIndex(index)
            else:
                widg = QtGui.QLabel("????")

            if editable_field.required:
                widg.setPalette(palette)

            self.form.addRow(display_text, widg)
            self.value_store[field_name] = (widg, field_type)

        self.form.itemAt(1).widget().setFocus()
        self.result = None

    def sizeHint(self):
        return QtCore.QSize(400,300)

    def exec_(self):
        '''
        overwrite the dialog's exec call
        '''
        while True:
            self.show()
            if BaseDialog.exec_(self):
                if not self.apply():
                    list_of_ommisions = ""
                    for ommision in self.ommisions:
                        list_of_ommisions += u"<li>%s</li>"% ommision

                    QtGui.QMessageBox.warning(self, _("error"),
                    u"%s<ul>%s</ul>" %(
                    _("incomplete form - the following are required"),
                    list_of_ommisions))
                    continue
                id, result = self.check_is_duplicate()
                if result:
                    self.emit(QtCore.SIGNAL("Load Serial Number"), id)
                    return False
                query, values = self.address_record.insert_query
                query += '''\n returning ix, addr1, addr2, addr3, city,
                county, country, postal_cd '''
                print query
                q_query = QtSql.QSqlQuery(SETTINGS.psql_conn)
                q_query.prepare(query)
                for value in values:
                    q_query.addBindValue(value)
                result =  q_query.exec_()
                if result:
                    if q_query.isActive():
                        q_query.next()
                        self.result = q_query.record()
                        return True
                    else:
                        self.Advise("unknown error") #shouldn't happen
                else:
                    self.Advise(u"Error Executing query<hr />%s<hr />%s"% (
                    query, q_query.lastError().text()), 1)
            else:
                return False

    def apply(self):
        '''
        applies the entered data to the new object
        '''
        # step 1.. get the values the user has entered.
        for field_name in self.value_store:
            widg, field_type = self.value_store[field_name]
            if field_type == QtCore.QVariant.Date:
                self.address_record.setValue(field_name, widg.date())
            elif field_type == QtCore.QVariant.String:
                self.address_record.setValue(field_name, widg.text())
            elif type(field_type) == OMType:
                val = widg.itemData(widg.currentIndex())
                self.address_record.setValue(field_name, val)
            else:
                ## shouldn't happen
                LOGGER.error("Whoops! misunderstood field name")

        # step 2.. see if all required fields are completed
        self.ommisions = []
        all_completed = True

        standard_fields, advanced_fields = self.address_record.editable_fields

        for editable_field in standard_fields+advanced_fields:
            if editable_field.required:
                field_name = editable_field.fieldname

                if self.address_record.value(field_name).toString()== "":
                    all_completed = False
                    self.ommisions.append(editable_field.readable_fieldname)

        return all_completed

    def check_is_duplicate(self):
        '''
        is the new address already on the books?
        '''
        chk_dict = {}
        chk_dict["addr1"] = self.address_record.value("addr1").toString()
        chk_dict["addr2"] = self.address_record.value("addr2").toString()
        chk_dict["addr3"] = self.address_record.value("addr3").toString()
        #chk_dict["city"] = self.address_record.value("city").toString()
        #chk_dict["country"] = self.address_record.value("country").toString()
        chk_dict["postal_cd"] = self.address_record.value("postal_cd").toString()
        match_model = SETTINGS.psql_conn.get_address_matchmodel(chk_dict)
        if match_model.rowCount() >0:
            dl = ShowAddyMatchDialog(match_model, self.parent())
            id = dl.chosen_record
            return (id, bool(id))

        return (None, False)

    def Advise(self, *args):
        if __name__ == "__main__":
            print args
        self.emit(QtCore.SIGNAL("Advise"), *args)

class ShowAddyMatchDialog(AddressSelectionDialog):
    def __init__(self, matches, parent=None):
        AddressSelectionDialog.__init__(self, matches, parent)
        self.setWindowTitle(_("Possible Duplicate"))
        self.top_label.setText(
        _("Is the new address one of the following known addresss?"))

        self.set_accept_button_text(_("Yes, load the selected Record"))
        self.set_reject_button_text(_("No, Create a new Record now."))


def _test():

    from lib_openmolar.client.connect import DemoClientConnection

    app = QtGui.QApplication([])

    cc = DemoClientConnection()
    cc.connect()

    dl = NewAddressDialog()
    dl.exec_()

if __name__ == "__main__":
    _test()