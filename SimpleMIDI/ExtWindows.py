from PyQt6 import uic
from PyQt6.QtWidgets import QDialog


class PreferencesDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        with open('QTFiles/PreferencesDialog.ui') as f:
            uic.loadUi(f, self)

        self.InterfacePageButton.clicked.connect(lambda: self.switch(0))
        self.TestPageButton.clicked.connect(lambda: self.switch(1))

    def switch(self, index):
        self.MainTab.setCurrentIndex(index)