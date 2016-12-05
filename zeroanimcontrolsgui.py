"""
This script will zero out all the animation controls in a rig.  Includes FK/IK, user defined controls with unique names.
Values of 0 and 1 are considered default.  Scale attributes are set back to 1.  Reset controls by finding prefixes or
reset by the manual selection of specific anim controls within rig.
"""

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import sys
from PySide import QtGui, QtCore
from shiboken import wrapInstance

UNIQUE_HANDLE = 'ZeroAnimControlsWindow'


def get_maya_main_window():
    main_win_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_win_ptr), QtGui.QWidget)


class ZeroAnimControlsUI(QtGui.QDialog):
    def __init__(self, parent=get_maya_main_window(), unique_handle=UNIQUE_HANDLE):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle('Reset Animation Controls')
        self.setObjectName(unique_handle)
        self.setMinimumSize(450, 200)
        self.setMaximumSize(450, 200)

        self.create_controls()
        self.create_layout()
        self.create_connections()
        self.zero_anim = ZeroAnimControls()

    def create_controls(self):
        # option widgets
        self.by_prefix_radio_btn = QtGui.QRadioButton('Reset by prefix')
        self.by_selection_radio_btn = QtGui.QRadioButton('Reset by selection')
        self.by_selection_radio_btn.setChecked(True)

        # prefix widgets
        self.prefix_lbl = QtGui.QLabel('Find Prefix(es):')
        self.prefix_lbl.setMinimumWidth(75)
        self.prefix_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.prefix_line_edit = QtGui.QLineEdit()
        self.prefix_line_edit.setPlaceholderText('ctrl*, ctrlIK*, ctrlFK* , ctrlGim*, *anim')
        self.prefix_line_edit.setEnabled(False)
        self.select_prefix_btn = QtGui.QPushButton('Select')

        # reset widgets
        self.reset_btn = QtGui.QPushButton('Reset Anim Controls')
        self.apply_btn = QtGui.QPushButton('Apply')
        self.close_btn = QtGui.QPushButton('Close')

    def create_layout(self):
        self.default_margins = 2, 2, 2, 2

        # option layout
        option_layout = QtGui.QHBoxLayout()
        option_layout.setContentsMargins(*self.default_margins)
        option_layout.addWidget(self.by_prefix_radio_btn)
        option_layout.addWidget(self.by_selection_radio_btn)
        option_layout.addSpacerItem(QtGui.QSpacerItem(100, 0))

        # prefix layout
        prefix_layout = QtGui.QHBoxLayout()
        prefix_layout.setContentsMargins(*self.default_margins)
        prefix_layout.addWidget(self.prefix_lbl)
        prefix_layout.addWidget(self.prefix_line_edit)
        prefix_layout.addWidget(self.select_prefix_btn)

        # button layout
        button_layout = QtGui.QHBoxLayout()
        button_layout.setContentsMargins(*self.default_margins)
        button_layout.setSpacing(5)
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.close_btn)

        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.addLayout(option_layout)
        main_layout.addLayout(prefix_layout)
        main_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def create_connections(self):
        self.by_prefix_radio_btn.toggled.connect(self.on_toggle_cmd)
        self.by_selection_radio_btn.toggled.connect(self.on_toggle_cmd)
        self.reset_btn.clicked.connect(self.reset_btn_cmd)
        self.apply_btn.clicked.connect(self.apply_btn_cmd)
        self.close_btn.clicked.connect(self.close_btn_cmd)

    def on_toggle_cmd(self):
        if self.by_prefix_radio_btn.isChecked():
            self.prefix_line_edit.setEnabled(True)
        elif self.by_selection_radio_btn.isChecked():
            self.prefix_line_edit.setEnabled(False)

    def reset_btn_cmd(self):
        self.apply_btn_cmd()
        self.close_btn_cmd()

    def apply_btn_cmd(self):
        anim_controls = []
        # check which option is active
        if self.by_prefix_radio_btn.isChecked():
            prefix_list = self.prefix_line_edit.text().split(',')
            anim_controls = self.zero_anim.get_controls_prefix(prefix_list)
            # check if prefix_list returned any matches
            if not anim_controls:
                cmds.warning('No matching controls found.')
                return

        elif self.by_selection_radio_btn.isChecked():
            anim_controls = self.zero_anim.get_controls_selection()
            # check if any controls we selected
            if not anim_controls:
                cmds.warning('Select controls to reset.')
                return

        # anim controls with matching prefix or selected controls, reset them...
        self.zero_anim.reset_controls(anim_controls)
        sys.stdout.write('Operation completed.\n')

    def close_btn_cmd(self):
        cmds.deleteUI(self.objectName(), window=True)


class ZeroAnimControls(object):

    def get_controls_prefix(self, prefix_list=None):
        transforms = cmds.ls(prefix_list, et='transform')
        joints = cmds.ls(prefix_list, et='joint')
        anim_controls = transforms + joints
        return anim_controls

    def get_controls_selection(self):
        anim_controls = cmds.ls(sl=True, tr=True)
        return anim_controls

    def reset_controls(self, anim_controls=None):
        for control in anim_controls:
            attributes = cmds.listAttr(control, k=True)

            for attr in attributes:
                full_attribute_name = control + '.' + attr

                # check if attribute is locked..
                if not cmds.getAttr(full_attribute_name, lock=True):
                    # attribute set to 1 considered to be default state, skip...
                    if cmds.getAttr(full_attribute_name) != 1:
                        # non scale attributes are set back to 0
                        if attr.find('scale') == -1:
                            cmds.setAttr(full_attribute_name, 0)
                        else:
                            # scale attributes are set back to 1
                            cmds.setAttr(full_attribute_name, 1)


def showUI():
    if cmds.window(UNIQUE_HANDLE, exists=True):
        cmds.deleteUI(UNIQUE_HANDLE, wnd=True)
    ui = ZeroAnimControlsUI()
    ui.show()
    return ui