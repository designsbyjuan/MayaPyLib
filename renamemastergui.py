"""
This is a simple renaming tool.  It has find and replace functionality as well as ability to add prefix and suffixes
User must select nodes in the scene to apply functionality.
"""

import maya.OpenMayaUI as omui
import maya.cmds as cmds
from PySide import QtGui, QtCore
from shiboken import wrapInstance

UNIQUE_HANDLE = 'RenameMasterWindow'


def get_maya_main_window():
    main_win_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_win_ptr), QtGui.QWidget)


class RenameMasterUI(QtGui.QDialog):
    def __init__(self, parent=get_maya_main_window(), unique_handle=UNIQUE_HANDLE):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle('Rename Master')
        self.setObjectName(unique_handle)
        self.setMinimumSize(540, 100)
        self.setMaximumSize(540, 100)
        self.add_opt_list = ['before name', 'after name']
        self.create_controls()
        self.create_layout()
        self.create_connections()
        self.rename_master = RenameMaster()

    def create_controls(self):
        # replace text widgets
        self.replace_btn = QtGui.QPushButton('Replace Text')
        self.find_lbl = QtGui.QLabel('Find:')
        self.find_line = QtGui.QLineEdit()
        self.replace_lbl = QtGui.QLabel('Replace:')
        self.replace_line = QtGui.QLineEdit()

        #add text widgets
        self.add_btn = QtGui.QPushButton('Add Text')
        self.add_combo_box = QtGui.QComboBox()
        self.add_combo_box.addItems(self.add_opt_list)
        self.add_line = QtGui.QLineEdit()

    def create_layout(self):
        self.default_margins = 2, 2, 2, 2

        # replace layout
        replace_layout = QtGui.QHBoxLayout()
        replace_layout.setContentsMargins(*self.default_margins)
        replace_layout.addWidget(self.find_lbl)
        replace_layout.addWidget(self.find_line)
        replace_layout.addWidget(self.replace_lbl)
        replace_layout.addWidget(self.replace_line)
        replace_layout.addWidget(self.replace_btn)

        # add layout
        add_layout = QtGui.QHBoxLayout()
        add_layout.setContentsMargins(*self.default_margins)
        add_layout.addWidget(self.add_combo_box)
        add_layout.addWidget(self.add_line)
        add_layout.addWidget(self.add_btn)

        # main layout
        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.addLayout(replace_layout)
        main_layout.addLayout(add_layout)

        self.setLayout(main_layout)

    def create_connections(self):
        self.replace_btn.clicked.connect(self.replace_btn_cmd)
        self.add_btn.clicked.connect(self.add_btn_cmd)

    def replace_btn_cmd(self):
        selection = cmds.ls(sl=True)
        find_str = self.find_line.text()
        replace_str = self.replace_line.text()

        self.rename_master.replace_text(selection, find_str, replace_str)

        # clear the text box
        self.find_line.setText('')
        self.replace_line.setText('')

    def add_btn_cmd(self):
        selection = cmds.ls(sl=True)
        # check option type (before name or after name)
        add_text_opt = self.add_combo_box.currentText()
        add_str = self.add_line.text()
        if add_text_opt == self.add_opt_list[0]:
            # add prefix
            self.rename_master.add_prefix(selection, add_str)
        elif add_text_opt == self.add_opt_list[1]:
            # add suffix
            self.rename_master.add_suffix(selection, add_str)

        # clear the text box
        self.add_line.setText('')


class RenameMaster(object):
    def __init__(self):
        self.no_selection_warning = 'Select one or more nodes to rename.'
        self.no_params_warning = 'Enter find parameters.'

    def replace_text(self, selection=None, find_str=None, replace_str=None):
        if not find_str:
            cmds.warning(self.no_params_warning)
            return

        if selection:
            for sel in selection:
                new_name = sel.replace(find_str, replace_str)
                cmds.rename(sel, new_name)
        else:
            cmds.warning(self.no_selection_warning)

    def add_prefix(self, selection=None, prefix_str=None):
        if selection:
            for sel in selection:
                cmds.rename(sel, prefix_str + sel)
        else:
            cmds.warning(self.no_selection_warning)

    def add_suffix(self, selection=None, suffix_str=None):
        if selection:
            for sel in selection:
                cmds.rename(sel, sel + suffix_str)
        else:
            cmds.warning(self.no_selection_warning)


def showUI():
    if cmds.window(UNIQUE_HANDLE, exists=True):
        cmds.deleteUI(UNIQUE_HANDLE, wnd=True)
    ui = RenameMasterUI()
    ui.show()
    return ui

