import json
from PyQt6.QtWidgets import QDialog, QColorDialog, QDialogButtonBox

from QTFiles.HelpPage_ui import Ui_HelpPageDialog
from QTFiles.Preferences_Dialog import Ui_PreferencesDialog
from Utility.Utils import get_resource_path


config_path = get_resource_path("SMDIconfig.json")

class PreferencesDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        
        Ui_PreferencesDialog.setupUi(self)

        self.InterfacePageButton.clicked.connect(lambda: self.switch(0))
        self.ProjectPageButton.clicked.connect(lambda: self.switch(1))

        self.InnerColorChangeButton.clicked.connect(lambda: self.ChangeColor("COLOR_grid_fill_color"))
        self.OuterColorChangeButton.clicked.connect(lambda: self.ChangeColor("COLOR_grid_color"))
        self.NoteColorChangeButton.clicked.connect(lambda: self.ChangeColor("COLOR_note_color"))
        self.NoteMarkColorChangeButton.clicked.connect(lambda: self.ChangeColor("COLOR_Note_Mark"))

        self.buttonBox: QDialogButtonBox
        self.buttonBox.clicked.connect(self.Save)

        self.BPMspinBox.valueChanged.connect(self.ChangeBPM)

        self.BPMspinBox.setValue(self.parent().BPM)

        self.RecordedBPM = self.parent().BPM

        self.RecordedPitchRange = (self.parent().PitchRange)
        self.RecordedPitchPerY = (self.parent().PitchPerY)

        self.PitchRangeMinSpinBox.valueChanged.connect(lambda x: self.ChangePitchRange(0,x))
        self.PitchRangeMaxSpinBox.valueChanged.connect(lambda x: self.ChangePitchRange(1,x))

        self.PitchPerYSpinBox.valueChanged.connect(self.ChangePitchPerY)

        self.PitchRangeMinSpinBox.setValue(self.RecordedPitchRange[0])
        self.PitchRangeMaxSpinBox.setValue(self.RecordedPitchRange[1])

        self.PitchPerYSpinBox.setValue(self.RecordedPitchPerY)

    def ChangeBPM(self,x):
        self.RecordedBPM = x

    def ChangePitchPerY(self,x):
        self.RecordedPitchPerY = x

    def ChangePitchRange(self, idx, val):
        self.RecordedPitchRange[idx] = val

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

            with open("SMDIconfig.json", "w") as f:
                json.dump(dic, f)

        p.ChangePitchParams(self.RecordedPitchRange, self.RecordedPitchPerY)

    def switch(self, index):
        self.MainTab.setCurrentIndex(index)

class HelpPage(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        
        Ui_HelpPageDialog.setupUi(self)

        self.GeneralPageButton.clicked.connect(lambda: self.switch(0))
        self.CanvasPageButton.clicked.connect(lambda: self.switch(1))
    
    def switch(self, index):
        self.MainTab.setCurrentIndex(index)

    
