"""
This script exports individual or a multi selection of objects in a scene.  Each selected object is exported as an
individual file.  The name of the file is derived from it's name in the scene.  On selection, selected objects are
positioned at 0,0 cords.  User has the option to export as OBJ or FBX.  More export options will be available in the
future as well as the option to for go zeroing out the object.  By default an exportLib folder is created in the users
main maya directory.  The user also has the option to select a specific folder to export to.
"""

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import sys
from PySide import QtGui, QtCore
from shiboken import wrapInstance
import os

USER_APP_DIR = cmds.internalVar(userAppDir=True)
DEFAULT_DIRECTORY = os.path.join(USER_APP_DIR, 'exportLib')
UNIQUE_HANDLE = 'ExportMasterWindow'


def get_maya_main_window():
    main_win_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_win_ptr), QtGui.QWidget)


class ExportMasterUI(QtGui.QDialog):
    def __init__(self, parent=get_maya_main_window(), unique_handle=UNIQUE_HANDLE):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle('Export Master')
        self.setObjectName(unique_handle)
        self.setMinimumSize(450, 200)
        self.setMaximumSize(450, 200)
        self.export_options_list = ['FBX export', 'OBJexport']

        self.create_controls()
        self.create_layout()
        self.create_connections()
        self.export_master = ExportMaster()

    def create_controls(self):
        # path layout
        self.path_lbl = QtGui.QLabel('Path:')
        self.path_lbl.setMinimumSize(50, 0)
        self.path_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.directory_line_edit = QtGui.QLineEdit(DEFAULT_DIRECTORY)
        self.directory_line_edit.setEnabled(False)
        self.path_tool_btn = QtGui.QToolButton()
        self.path_tool_btn.setText('...')

        # file type layout
        self.file_type_lbl = QtGui.QLabel('File type:')
        self.file_type_lbl.setMinimumSize(50, 0)
        self.file_type_lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.combo_box = QtGui.QComboBox()
        self.combo_box.addItems(self.export_options_list)
        self.combo_box.setMinimumSize(125, 0)

        # check_box_layout
        self.check_box_base = QtGui.QCheckBox('Set pivot to base')
        self.check_box_base.setChecked(True)
        self.check_box_delete = QtGui.QCheckBox('Delete on export')

        # export selection layout
        self.export_btn = QtGui.QPushButton('Export')
        self.apply_btn = QtGui.QPushButton('Apply')
        self.close_btn = QtGui.QPushButton('Close')

    def create_layout(self):
        self.default_margin = 2, 2, 2, 2

        # path layout
        path_layout = QtGui.QHBoxLayout()
        path_layout.setContentsMargins(*self.default_margin)
        path_layout.addWidget(self.path_lbl)
        path_layout.addWidget(self.directory_line_edit)
        path_layout.addWidget(self.path_tool_btn)

        # file layout
        file_layout = QtGui.QHBoxLayout()
        file_layout.setContentsMargins(*self.default_margin)
        file_layout.addWidget(self.file_type_lbl)
        file_layout.addWidget(self.combo_box)
        file_layout.addSpacerItem(QtGui.QSpacerItem(290, 0))

        # checkbox layout
        check_box_layout = QtGui.QHBoxLayout()
        check_box_layout.setContentsMargins(*self.default_margin)
        check_box_layout.addSpacerItem(QtGui.QSpacerItem(60, 0))
        check_box_layout.addWidget(self.check_box_base)
        check_box_layout.addWidget(self.check_box_delete)
        check_box_layout.addSpacerItem(QtGui.QSpacerItem(100, 0))

        # button layout
        button_layout = QtGui.QHBoxLayout()
        button_layout.setContentsMargins(*self.default_margin)
        button_layout.setSpacing(5)
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.close_btn)

        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.addLayout(path_layout)
        main_layout.addLayout(file_layout)
        main_layout.addLayout(check_box_layout)
        main_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def create_connections(self):
        self.export_btn.clicked.connect(self.export_btn_cmd)
        self.apply_btn.clicked.connect(self.apply_btn_cmd)
        self.close_btn.clicked.connect(self.close_btn_cmd)
        self.path_tool_btn.clicked.connect(self.path_tool_cmd)

    def export_btn_cmd(self):
        self.apply_btn_cmd()
        self.close_btn_cmd()

    def apply_btn_cmd(self):
        # get directory from self.directory_line_edit
        directory = self.directory_line_edit.text()

        # check export type
        export_type = self.combo_box.currentText()

        # check which options are checked
        set_pivot_base = self.check_box_base.isChecked()
        delete_on_export = self.check_box_delete.isChecked()

        # export according to settings
        self.export_master.export(directory, export_type, set_pivot_base, delete_on_export)

    def close_btn_cmd(self):
        cmds.deleteUI(self.objectName(), window=True)

    def path_tool_cmd(self):
        directory = cmds.fileDialog2(dir=USER_APP_DIR, dialogStyle=2, fileMode=3)
        self.directory_line_edit.setText(directory[0])


class ExportMaster(object):
    def base_pivot(self, sel=None):
        bounding_box = cmds.xform(sel, q=True, bb=True, ws=True)
        y_min = bounding_box[1]
        cmds.move(y_min, ['%s.scalePivot' % sel, '%s.rotatePivot' % sel], moveY=True, absolute=True)
        cmds.move(0, 0, 0, sel, rpr=True, a=True)

    def create_directory(self, directory=DEFAULT_DIRECTORY):
        # if directory does not exist make it...
        if not os.path.exists(directory):
            os.mkdir(directory)
            print 'Export Master default directory does not exist, making exportLib directory.'

    def is_attr_locked(self, selection=None):
        for sel in selection:
            attributes = cmds.listAttr(sel, k=True)

            for attr in attributes:
                full_attribute_name = sel + '.' + attr
                # print 'FULL ATTR NAME: ', full_attribute_name
                if cmds.getAttr(full_attribute_name, lock=True):
                    return True
        return False

    def export(self, directory=None, export_type=None, set_pivot_base=False, delete_on_export=False):
        self.create_directory()

        # get selected objects
        selection = cmds.ls(sl=True, tr=True)

        # check if any attributes in selection are locked
        is_locked = self.is_attr_locked(selection)
        if is_locked:
            sys.stdout.write('Error: Operation canceled.  Please unlock all attributes before exporting.\n')
            return

        if not selection:
            cmds.warning('Please select one or more objects to export.')
        else:
            # iterate through selected objects
            for sel in selection:
                cmds.xform(sel, cp=True)
                cmds.move(0, 0, 0, sel, rpr=True)
                cmds.xform(sel, a=True, ro=(0, 0, 0))

                # move pivot to base
                if set_pivot_base:
                    self.base_pivot(sel)

                cmds.makeIdentity(sel, apply=True, t=1, r=1, s=1, n=0)
                cmds.delete(sel, ch=True)

                # get name of object
                path = os.path.join(directory, sel)
                cmds.select(sel)
                # get export type
                export_options = ExportMasterUI().export_options_list
                if export_type == export_options[0]:
                    cmds.file(path, f=True, pr=1, typ="FBX export", es=1, op="fbx")
                elif export_type == export_options[1]:
                    cmds.file(path, f=True, pr=1, typ="OBJexport", es=1, op="groups=1; ptgroups=1; materials=1; smoothing=1; normals=1")
                # clean up and delete object
                if delete_on_export:
                    cmds.delete(sel)

            sys.stdout.write('Export complete.\n')


def showUI():
    if cmds.window(UNIQUE_HANDLE, exists=True):
        cmds.deleteUI(UNIQUE_HANDLE, wnd=True)
    ui = ExportMasterUI()
    ui.show()
    return ui


