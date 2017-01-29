"""
The script allows users to create a library of their favorite models.  Select a model in your scene to save it to the
library or make no selection to save the whole scene.  Name model appropriately.  To overwrite a model, save new model
with same name.  Output is a .ma file located in a default directory.  If a model file is deleted from the default
directory it's library membership will be revoked next time the app is executed.  The model file will still be present
in the directory, but no longer loaded into the library.  To load or delete a model from the library, select the model's
icon in the gui and click the appropriate action.  Hover over an icon to see more information on the model.
"""

import pymel.core as pmc
import os
import json
import pprint
import maya.OpenMayaUI as omui
from PySide import QtGui, QtCore
from shiboken import wrapInstance

USER_APP_DIR = pmc.internalVar(userAppDir=True)
DEFAULT_DIRECTORY = os.path.join(USER_APP_DIR, 'modelLibrary')
JSON_PATH = os.path.join(DEFAULT_DIRECTORY, 'modelLibrary.json')
UNIQUE_HANDLE = 'ModelLibWindow'


def get_maya_main_window():
    main_win_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_win_ptr), QtGui.QWidget)


class ModelLibUI(QtGui.QDialog):

    SIZE = 64
    BUFFER = 20

    def __init__(self, parent=get_maya_main_window(), unique_handle=UNIQUE_HANDLE):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle('Model Library')
        self.setObjectName(unique_handle)
        self.setMinimumSize(300, 300)
        self.setMaximumSize(300, 300)
        self.create_controls()
        self.create_layout()
        self.create_connections()

        self.model_lib = ModelLib()
        self.load_model_lib()

    def create_controls(self):
        # save layout
        self.save_lbl = QtGui.QLabel('Model:')
        self.save_line = QtGui.QLineEdit()
        self.save_btn = QtGui.QPushButton('Save')

        # model list layout
        # TODO: center icons within QListWidget
        self.model_list_box = QtGui.QListWidget()
        self.model_list_box.setViewMode(QtGui.QListWidget.IconMode)
        self.model_list_box.setIconSize(QtCore.QSize(ModelLibUI.SIZE, ModelLibUI.SIZE))
        self.model_list_box.setGridSize(
            QtCore.QSize(ModelLibUI.SIZE + ModelLibUI.BUFFER, ModelLibUI.SIZE + ModelLibUI.BUFFER)
        )
        self.model_list_box.setMovement(QtGui.QListView.Static)

        # button layout
        self.load_btn = QtGui.QPushButton('Load')
        self.remove_btn = QtGui.QPushButton('Delete')
        self.close_btn = QtGui.QPushButton('Close')

    def create_layout(self):
        # save layout
        save_layout = QtGui.QHBoxLayout()
        save_layout.addWidget(self.save_lbl)
        save_layout.addWidget(self.save_line)
        save_layout.addWidget(self.save_btn)

        # model list layout
        model_list_layout = QtGui.QHBoxLayout()
        model_list_layout.addWidget(self.model_list_box)

        # button layout
        button_layout = QtGui.QHBoxLayout()
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.close_btn)

        # main layout
        main_layout = QtGui.QVBoxLayout()
        main_layout.addLayout(save_layout)
        main_layout.addLayout(model_list_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def create_connections(self):
        self.load_btn.clicked.connect(self.load_btn_cmd)
        self.remove_btn.clicked.connect(self.delete_btn_cmd)
        self.close_btn.clicked.connect(self.close_btn_cmd)
        self.save_btn.clicked.connect(self.save_btn_cmd)

    def load_btn_cmd(self):
        curr_item = self.model_list_box.currentItem()
        if curr_item:
            # get the item name of the curr selected
            item_name = curr_item.text()
            print 'Loading:', item_name
            model = Model(name=item_name)
            self.model_lib.load_model(model)
        else:
            # nothing is selected, display a warning
            pmc.displayWarning('Please select a model to load.')

    def refresh_btn_cmd(self):
        self.model_list_box.clear()
        self.load_model_lib()

    def delete_btn_cmd(self):
        curr_item = self.model_list_box.currentItem()
        if curr_item:
            item_name = curr_item.text()
            print 'Deleting:', item_name
            model = Model(name=item_name)
            # TODO: should we also delete the model from the directory?
            # delete model from library
            self.model_lib.delete_model(model)
            self.refresh_btn_cmd()
        else:
            pmc.displayWarning('Please select a model to remove.')

    def close_btn_cmd(self):
        pmc.deleteUI(self.objectName(), window=True)

    def save_btn_cmd(self):
        model_name = self.save_line.text()
        if model_name:
            print 'Saving', model_name
            model = Model(name=model_name)
            self.model_lib.save_model(model=model)
            self.save_line.setText('')
            # refresh the model list since it has been updated...
            self.refresh_btn_cmd()
        else:
            pmc.displayWarning('Please enter model name to save.')

    def load_model_lib(self):
        # clear list before loading...
        self.model_lib.model_list = []
        # generate the model list
        self.model_lib.generate_model_list()

        # try and load each model
        for model in self.model_lib.model_list:
            # if the model path exists let's load it up...
            if os.path.exists(model.path):
                item = QtGui.QListWidgetItem(model.name)
                self.model_list_box.addItem(item)
                icon = QtGui.QIcon(model.icon)
                item.setIcon(icon)
                # tool tip
                item.setToolTip(pprint.pformat(str(model.path)))
            else:
                # the model path does not exist, delete it from the model library and json
                self.model_lib.delete_model(model)


class Model(object):
    """
    Defines the attributes and behavior of the model class
    """
    def __init__(self, **kwargs):
        # if not path or icon arg is given, use the default directory
        self.name = kwargs.get('name', 'model')
        self.path = kwargs.get('path', os.path.join(DEFAULT_DIRECTORY, '%s.ma' % self.name))
        self.icon = kwargs.get('icon', os.path.join(DEFAULT_DIRECTORY, '%s.jpg' % self.name))

    def __eq__(self, other):
        # models are equal if they have the same name and path
        return self.name == other.name and self.path == other.path


class ModelLib(object):
    """
    Holds members of model library as well as methods to manipulate it.
    """
    def __init__(self):
        self.model_list = []

    def create_directory(self, directory=DEFAULT_DIRECTORY):
        if not os.path.exists(directory):
            os.mkdir(directory)

    def create_icon(self, model=Model()):
        pmc.viewFit()
        # set img format as jpg
        pmc.setAttr('defaultRenderGlobals.imageFormat', 8)

        pmc.playblast(
            completeFilename=model.icon, forceOverwrite=True, format='image', width=200, height=200,
            showOrnaments=False, startTime=1, endTime=1, viewer=False
        )

    def save_model(self, model=Model(), icon=True, directory=DEFAULT_DIRECTORY):
        # create model library directory if it doesn't exist...
        self.create_directory(directory)

        # if something is selected, export by selection...
        if pmc.ls(sl=True):
            pmc.exportSelected(model.path, force=1)
        # otherwise export the whole scene...
        else:
            pmc.exportAll(model.path, force=1)

        # generate model icon
        if icon:
            self.create_icon(model)

        # append model to json
        # check if the model already exists in the model_list
        for item in self.model_list:
            if item == model:
                # model is already a member of model_list, do not append...
                return

        # model is not member of model_list, append...
        self.model_list.append(model)

        # update json with new members information...
        with open(JSON_PATH, 'w') as f:
            # TODO: create default method
            json.dump([o.__dict__ for o in self.model_list], f, indent=4)

    def delete_model(self, model=Model()):
        # delete the instance from list
        self.model_list.remove(model)

        # print new list
        for i in self.model_list:
            print 'Updated model list:', i.name

        # update the json
        with open(JSON_PATH, 'w') as f:
            json.dump([o.__dict__ for o in self.model_list], f, indent=4)

    def load_model(self, model=Model()):
        """
        imports the model into maya using the model's path attribute
        """
        # check if model is member of list, check if present in path
        if model in self.model_list and os.path.exists(model.path):
            pmc.importFile(model.path)
        else:
            pmc.displayWarning('Model is not a member of model list...')

    def generate_model_list(self):
        # check if the json even exists...
        if not os.path.exists(JSON_PATH):
            return

        # read json and populate self.model_list
        with open(JSON_PATH, 'r') as f:
            data = json.load(f)

        for item in data:
            model_name, path, icon = map(item.get, ('name', 'path', 'icon'))
            self.model_list.append(Model(name=model_name, path=path, icon=icon))


def showUI():
    if pmc.window(UNIQUE_HANDLE, exists=True):
        pmc.deleteUI(UNIQUE_HANDLE, wnd=True)
    ui = ModelLibUI()
    ui.show()
    return ui





