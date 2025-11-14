import json

from PyQt6 import uic
from PyQt6.QtWidgets import QDialog, QColorDialog, QDialogButtonBox


class PreferencesDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        with open('QTFiles/PreferencesDialog.ui') as f:
            uic.loadUi(f, self)

        self.InterfacePageButton.clicked.connect(lambda: self.switch(0))
        self.TestPageButton.clicked.connect(lambda: self.switch(1))

        self.InnerColorChangeButton.clicked.connect(lambda: self.ChangeColor("COLOR_grid_fill_color"))
        self.OuterColorChangeButton.clicked.connect(lambda: self.ChangeColor("COLOR_grid_color"))
        self.NoteColorChangeButton.clicked.connect(lambda: self.ChangeColor("COLOR_note_color"))
        self.NoteMarkColorChangeButton.clicked.connect(lambda: self.ChangeColor("COLOR_Note_Mark"))

        self.buttonBox: QDialogButtonBox
        self.buttonBox.clicked.connect(self.Save)

        self.BPMspinBox.valueChanged.connect(self.ChangeBPM)

    def ChangeBPM(self,x):
        print(x)
        self.parent().BPM = x

    def ChangeColor(self, Property):
        p = self.parent()
        val = QColorDialog.getColor(parent=self)
        setattr(p, Property, val)

    def Save(self, button):
        p = self.parent()
        if self.buttonBox.buttonRole(button) == QDialogButtonBox.ButtonRole.ApplyRole:
            dic = {
                "COLOR_grid_fill_color": p.COLOR_grid_fill_color.name(),
                "COLOR_grid_color": p.COLOR_grid_color.name(),
                "COLOR_note_color": p.COLOR_note_color.name(),
                "COLOR_Note_Mark": p.COLOR_Note_Mark.name()
            }

            with open('config.json', "w") as f:
                json.dump(dic, f)

    def switch(self, index):
        self.MainTab.setCurrentIndex(index)
