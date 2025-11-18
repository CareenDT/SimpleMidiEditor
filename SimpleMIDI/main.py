import json
import sys
import threading
import time

from Utility.Utils import *
from ExtWindows import *

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QMouseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QSpinBox, QColorDialog, QCheckBox, QPushButton, QComboBox

import FileHandler

from QTFiles.App_ui import Ui_MainWindow

from Utility.Midi import player, instruments

ForceReload = False


class TheApp(QMainWindow):
    def __init__(self):
        super().__init__()

        Ui_MainWindow.setupUi(self)

        self.centralWidget().setMouseTracking(True)

        FileHandler.instance = self

        for i,k in instruments.items():
            self.InstrumentChoiceBox.addItem(f"{i}: {k}")

        #         ------Declarations------
        self.ViewPosition = Vector2()

        self.ViewFixedOffset = self.CamFixPosOffsetSpinBox.value()

        self.PrimaryDragInfo = MouseMoveInfo()
        self.SecondaryDragInfo = MouseMoveInfo()
        self.notes = []
        self.noteDisplaySize = Vector2(90, 30)
        self.PitchRange = [1, 121]
        self.PitchPerY = 2
        self.InstrumentIndex = 0

        self.BPM = 120
        
        self.OnionSkinMaxDistance = 5
        self.OnionSkinBaseOpacity = 200

        self.can_place_note = True
        self.PlaceTimer = QTimer()
        self.PlaceTimer.setSingleShot(True)
        self.PlaceTimer.timeout.connect(lambda: setattr(self, 'can_place_note', True))

        self.EditMode = True

        self.PlaybackCursor = PlaybackCursor()

        self.last_note_end = 0
        

        #         ------Preferences------
        #config_path = get_resource_path(__file__)
        
        defaultConfig = {"COLOR_grid_fill_color": "#2e2f36", "COLOR_grid_color": "#40414b", "COLOR_note_color": "#a1ff90", "COLOR_Note_Mark": "#7aff52"}

        if not os.path.exists("SMDIconfig.json"):
            with open("SMDIconfig.json", "w") as f:
                json.dump(defaultConfig, f)

        with open("SMDIconfig.json", "r") as file:

            try:
                c: dict = json.load(file)
                for i, k in c.items():
                    setattr(self, i, QColor(k))

                print(c)

            except json.JSONDecodeError as e:
                #Fallback
                
                for i, k in defaultConfig.items():
                    setattr(self, i, QColor(k))

                print(e)

        self.notePlacementSnap = 8

        self.centralWidget().setStyleSheet(f"background-color: {self.COLOR_grid_fill_color.name()};")

        #         ------Event Links------

        self.GridWidthSetSpinbox.setValue(self.noteDisplaySize[0])
        self.GridHeightSetSpinbox.setValue(self.noteDisplaySize[1])

        self.GridWidthSetSpinbox.valueChanged.connect(self.UpdateSize)
        self.GridHeightSetSpinbox.valueChanged.connect(self.UpdateSize)
        
        self.PlaceModeButton.clicked.connect(lambda: self.ChangeMode(True))
        self.RemoveModeButton.clicked.connect(lambda: self.ChangeMode(False))

        self.InstrumentIndexSpinBox.valueChanged.connect(self.SetInstrumentByIndex)
        self.InstrumentChoiceBox.activated.connect(self.SetInstrumentByCbox)

        self.OnionSkinSpinBox.setValue(self.OnionSkinMaxDistance)
        self.OnionSkinSpinBox.valueChanged.connect(self.SetOnionSkinDistance)

        self.centralWidget().paintEvent = self.CentralPaintEvent
        self.centralWidget().mouseMoveEvent = self.Central_MouseMoveEvent
        self.centralWidget().mousePressEvent = self.Central_MousePressEvent
        self.centralWidget().mouseReleaseEvent = self.Central_MouseReleaseEvent
        self.centralWidget().wheelEvent = self.wheelScrollEvent

        self.PlayButton.clicked.connect(self.playback_PlayThread)
        self.PauseButton.clicked.connect(self.PauseResume)
        self.StopButton.clicked.connect(self.Stop)

        self.CamFixPosOffsetSpinBox.valueChanged.connect(self.ChangeViewFixedOffset)

        self.actionPreferences.triggered.connect(lambda: PreferencesDialog(parent=self).exec())
        self.actionAbout.triggered.connect(lambda: HelpPage(parent=self).exec())

        self.actionNew.triggered.connect(self.LoadDefultProjectSettings)
        self.actionOpen.triggered.connect(self.LoadProject)
        self.actionSave.triggered.connect(self.WrapUpForSaving)
        self.actionExportToMIDI.triggered.connect(lambda: FileHandler.ExportToMidi(self))

        #         ------Logger------
        self.Logger = Logger(self.Log)

        # //StaticMessages//
        self._warn_InvalidPitchSettingsRatio = LogMessage(
            "WARN: InvalidPitchSettingsRatio --- PitchRange / PitchPerY should output an integer, outputs float instead ( This makes amount of notes on the piano roll miss out ) ",
            "warn")
        self._error_LogicalErrorPitchMinMoreThanMax = LogMessage(
            "Logic error: Pitch range minimal value can't be greater that maximum",
            "error")
        self._msg_Playback = LogMessage("Playback", "info")

        self._error_FileLoadError = LogMessage("File import error: incorrect or corrupted .SMDI file", "error")

        self.centralWidget().update()
    
    def LoadDefultProjectSettings(self):

        # Reset view and position
        self.ViewPosition = Vector2()
        self.ViewFixedOffset = 0
        self.PlaybackCursor.Position = 0
        self.PlaybackCursor.isPlaying = False

        # Reset notes
        self.notes.clear()

        # Reset display settings
        self.noteDisplaySize = Vector2(90, 30)
        self.PitchRange = [1, 121]
        self.PitchPerY = 2
        self.BPM = 120

        # Reset instrument settings
        self.InstrumentIndex = 0
        self.OnionSkinMaxDistance = 5
        self.OnionSkinBaseOpacity = 200

        # Reset mode
        self.EditMode = True
        self.can_place_note = True

        self.UpdateUIFromDefaults()

        self.update()

    def UpdateUIFromDefaults(self):
        # Grid settings
        self.GridWidthSetSpinbox.setValue(self.noteDisplaySize.x)
        self.GridHeightSetSpinbox.setValue(self.noteDisplaySize.y)

        # Instrument settings
        self.InstrumentIndexSpinBox.setValue(self.InstrumentIndex)
        self.InstrumentChoiceBox.setCurrentIndex(self.InstrumentIndex)
        self.OnionSkinSpinBox.setValue(self.OnionSkinMaxDistance)

        # View settings
        self.CamFixPosOffsetSpinBox.setValue(self.ViewFixedOffset)

        # Mode display
        self.CurrentModeLabel.setText("Current: Place")

        # Playback display
        self.Time.setText("0.0/0.0")

    def LoadProject(self):
        loaded_data = FileHandler.LoadFromJson()
        if loaded_data:
            FileHandler.ApplyToApp(self, loaded_data)

    def WrapUpForSaving(self):
        Data = {
            "ViewPosition": self.ViewPosition.to_dict(),
            "notes": [i.to_dict() for i in self.notes],
            "noteDisplaySize": self.noteDisplaySize.to_dict(),
            "PitchRange": self.PitchRange,
            "PitchPerY": self.PitchPerY,
            "BPM": self.BPM,
            "OnionSkinMaxDistance": self.OnionSkinMaxDistance,
            "InstrumentIndex": self.InstrumentIndex
        }
        FileHandler.SaveToJson(Data)
    
    def ChangeViewFixedOffset(self, x):
        self.ViewFixedOffset = x

    def SetOnionSkinDistance(self, x):
        self.OnionSkinMaxDistance = x

    def SetInstrumentByIndex(self, x):
        self.InstrumentIndex = x

        self.InstrumentChoiceBox.setCurrentIndex(x)

    def SetInstrumentByCbox(self, x):
        self.InstrumentIndex = x

        self.InstrumentIndexSpinBox.setValue(x)

    def ChangeMode(self, to: bool):
        self.EditMode = to

        self.CurrentModeLabel.setText("Current: " + ("Place" if self.EditMode else "Remove"))


    def ColorPick(self):
        Color = QColorDialog(self).getColor()
        self.COLOR_grid_fill_color = Color
        print(Color)
        
    def playback_PlayThread(self):
        PlayThread = threading.Thread(target=self.Play)
        self.PlaybackCursor.Position = 0

        if self.PlaybackCursor.isPlaying == False:
            PlayThread.daemon = True
            PlayThread.start()

    def PauseResume(self):
        self.PlaybackCursor.isPlaying = not self.PlaybackCursor.isPlaying

        if self.PlaybackCursor.isPlaying:
            PlayThread = threading.Thread(target=self.Play)
            PlayThread.daemon = True
            PlayThread.start()

    def Stop(self):
        self.PlaybackCursor.isPlaying = False
        self.PlaybackCursor.Position = 0

    def Play(self):
        try:
            self.notes.sort(key=lambda x: x.position.x)
            
            if not self.notes:
                return
            
            self.last_note_end = max(note.position.x + note.length for note in self.notes)

            self.PlaybackCursor.isPlaying = True

            seconds_per_beat = 60.0 / self.BPM

            while self.PlaybackCursor.isPlaying and self.PlaybackCursor.Position <= self.last_note_end:
                current_time = self.PlaybackCursor.Position

                notes_to_play = [
                    note for note in self.notes 
                    if abs(note.position.x - current_time) < 0.001
                ]

                self.Time.setText(f"{current_time}/{self.last_note_end}")

                if self.FixCamPosCheckBox.isChecked():
                    self.ViewPosition.x = int((self.PlaybackCursor.Position - (self.ViewFixedOffset/10)) * self.noteDisplaySize.x)

                for note in notes_to_play:
                    pitch = int((((self.PitchRange[1]+self.PitchRange[0]+1)) - note.position.y) // self.PitchPerY)
                    duration = note.length * seconds_per_beat
                    
                    pitch = max(0, min(127, pitch))
                    player.play_note(pitch, 100, duration, note.instrumentIdx)

                self.update()

                time_increment = 0.125

                time.sleep(time_increment * seconds_per_beat)

                self.PlaybackCursor.Position += time_increment

            self.PlaybackCursor.isPlaying = False
            self.update()

        except Exception as e:
            print(f"Playback error: {e}")
            self.PlaybackCursor.isPlaying = False

    def GetGridCoordinates(self, mouse_pos):

        grid_x = (mouse_pos.x + self.ViewPosition.x) / self.noteDisplaySize.x
        grid_y = (mouse_pos.y + self.ViewPosition.y) // self.noteDisplaySize.y

        return Vector2(grid_x, grid_y)

    def Central_MousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.PrimaryDragInfo.drag = True
        elif e.button() == Qt.MouseButton.RightButton:
            self.SecondaryDragInfo.drag = True

            if self.can_place_note and not hasattr(self, "_CurrentNoteEditing"):
                if self.EditMode:
                    self._CurrentNoteEditing = Note(
                        self.GetGridCoordinates(Vector2(
                            e.pos().x(),
                            e.pos().y()
                        )),
                        AbsPosition=Vector2(
                            e.pos().x(),
                            e.pos().y()
                        ) + self.ViewPosition,
                        instrumentIdx=self.InstrumentIndex
                    )

                    self._CurrentNoteEditing.position.x = int(
                        self._CurrentNoteEditing.position.x * self.notePlacementSnap) / self.notePlacementSnap

                    self.notes.append(self._CurrentNoteEditing)
                else:
                    mouse_pos = Vector2(e.pos().x(), e.pos().y())

                    grid_pos = self.GetGridCoordinates(mouse_pos)
                    note_to_remove = self.find_note_at_position(grid_pos)
                    if (note_to_remove is not None) and (note_to_remove.instrumentIdx == self.InstrumentIndex):
                        self.notes.remove(note_to_remove)
                        self.update()
        self.update()

    def Central_MouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.PrimaryDragInfo.drag = False

        elif e.button() == Qt.MouseButton.RightButton:
            self.SecondaryDragInfo.drag = False

            self.can_place_note = False
            if len(tuple(note.position.x + note.length for note in self.notes)) > 0:
                self.last_note_end = max(note.position.x + note.length for note in self.notes)
            self.PlaceTimer.start(50)

            if hasattr(self, "_CurrentNoteEditing"):
                delattr(self, "_CurrentNoteEditing")
        self.update()
    
    def find_note_at_position(self, grid_pos):
        for note in self.notes:
            note_rect = (
                note.position.x,
                note.position.y,
                note.position.x + note.length,
                note.position.y + 1
            )

            if (note_rect[0] <= grid_pos.x <= note_rect[2] and 
                note_rect[1] <= grid_pos.y <= note_rect[3]):
                return note
        return None

    def ChangePitchParams(self, PitchRange=None, PitchPerY=None):
        if PitchRange is not None:
            self.PitchRange = PitchRange
        if PitchPerY is not None:
            self.PitchPerY = PitchPerY

        if (self.PitchRange[1] - self.PitchRange[0]) // self.PitchPerY != self.PitchRange[1] / self.PitchPerY:
            self.Logger.Log(self._warn_InvalidPitchSettingsRatio)
        else:
            self.Logger.RemoveSingleton(self._warn_InvalidPitchSettingsRatio)

        if self.PitchRange[0] > self.PitchRange[1]:
            self.Logger.Log(self._error_LogicalErrorPitchMinMoreThanMax)
        else:
            self.Logger.RemoveSingleton(self._error_LogicalErrorPitchMinMoreThanMax)

        self.centralWidget().update()

    def Central_MouseMoveEvent(self, e: QMouseEvent):
        cw_pos = self.centralWidget().mapFrom(self, e.pos())
        position = Vector2(cw_pos.x(), cw_pos.y())

        self.PrimaryDragInfo.Write(position)
        self.SecondaryDragInfo.Write(position)

        if self.PrimaryDragInfo.drag:

            if self.FixCamPosCheckBox.isChecked() and self.PlaybackCursor.isPlaying:
                self.ViewPosition.y -= self.PrimaryDragInfo.delta.y
            else:
                self.ViewPosition -= self.PrimaryDragInfo.delta
            
            self.ViewPosition = Vector2(max(0,self.ViewPosition.x),max(self.ViewPosition.y,0))

        if self.SecondaryDragInfo.drag and hasattr(self, "_CurrentNoteEditing"):
            current_grid_pos = self.GetGridCoordinates(position)
            current_grid_pos.x = int(current_grid_pos.x * self.notePlacementSnap) / self.notePlacementSnap

            length = current_grid_pos.x - self._CurrentNoteEditing.position.x

            self.last_note_end = max(note.position.x + note.length for note in self.notes)

            self._CurrentNoteEditing.length = max(0.125, length)

            self._CurrentNoteEditing.length = int(
                self._CurrentNoteEditing.length * self.notePlacementSnap) / self.notePlacementSnap

        self.centralWidget().update()

    def wheelScrollEvent(self, event):
        scroll_amount = event.angleDelta().y() // 16

        self.noteDisplaySize.x = min(max(8, self.noteDisplaySize.x + scroll_amount), 99)

        self.GridWidthSetSpinbox.setValue(self.noteDisplaySize.x)

        self.centralWidget().update()

    def UpdateSize(self):
        self.noteDisplaySize = Vector2(self.GridWidthSetSpinbox.value(), self.GridHeightSetSpinbox.value())
        self.centralWidget().update()

    def CentralPaintEvent(self, event):
        cw = self.centralWidget()

        cw.setStyleSheet(f"background-color: {self.COLOR_grid_fill_color.name()};")

        painter = QPainter(cw)

        font = painter.font()
        font.setPixelSize(int(self.noteDisplaySize.y))

        grid_pen = QPen(self.COLOR_grid_color, 2)
        startPoint = Vector2()
        endPoint = Vector2(startPoint.x + cw.width(), startPoint.y + cw.height())

        # Render Grid

        painter.setPen(QPen(QColor(200, 70, 70), 16))
        painter.drawLine(-self.ViewPosition.x, startPoint.y, -self.ViewPosition.x, endPoint.y)

        # Render Notes

        for note in self.notes:
            note: Note
            if note.instrumentIdx == self.InstrumentIndex:
                borders: QColor = self.COLOR_note_color
                borders.darker(10)
                painter.setPen(QPen(borders,2))
                painter.setBrush(QBrush(self.COLOR_note_color))
                painter.drawRect(
                    int(note.position.x * self.noteDisplaySize.x - self.ViewPosition.x),

                    (note.position.y) * self.noteDisplaySize.y - self.ViewPosition.y,

                    int(self.noteDisplaySize.x * note.length), self.noteDisplaySize.y
                )
            else:
                forward = note.instrumentIdx - self.InstrumentIndex > 0

                distance = abs(note.instrumentIdx - self.InstrumentIndex)

                if distance > self.OnionSkinMaxDistance:
                    continue

                opacity = self.OnionSkinBaseOpacity * (1 - (distance / self.OnionSkinMaxDistance))
                opacity = max(30, opacity)

                clr: QColor = QColor(255 if not forward else 0, 50, 255 if forward else 0, int(opacity))

                borders: QColor = clr
                borders.darker(10)

                painter.setPen(QPen(borders,2))
                painter.setBrush(QBrush(clr))
                painter.drawRect(
                    int(note.position.x * self.noteDisplaySize.x - self.ViewPosition.x),

                    (note.position.y) * self.noteDisplaySize.y - self.ViewPosition.y,

                    int(self.noteDisplaySize.x * note.length), self.noteDisplaySize.y
                )

        for idx, x in enumerate(range(startPoint.x, endPoint.x, self.noteDisplaySize.x)):
            painter.setPen(grid_pen)
            offset = self.ViewPosition.x % self.noteDisplaySize.x
            painter.drawLine(x - offset, startPoint.y, x - offset, endPoint.y)

            painter.setPen(QPen(self.COLOR_Note_Mark))
            beat_number = idx + (self.ViewPosition.x // self.noteDisplaySize.x)
            total_seconds = (beat_number * 60) / self.BPM
            time_text = f"{total_seconds:.1f}s"

            painter.drawText(x - offset, int(self.noteDisplaySize.y), time_text)

        for idx, pitch in enumerate(range(self.PitchRange[1], self.PitchRange[0], -self.PitchPerY)):
            screen_y = (idx * self.noteDisplaySize.y) - self.ViewPosition.y

            painter.setPen(grid_pen)
            painter.drawLine(startPoint.x, screen_y, endPoint.x, screen_y)

            painter.setPen(QPen(self.COLOR_Note_Mark))
            painter.drawText(0, int(screen_y), str(pitch))

        
        cursor_x = int(self.PlaybackCursor.Position * self.noteDisplaySize.x) - self.ViewPosition.x
        painter.setPen(QPen(QColor(0, 255, 0), 4))
        painter.drawLine(cursor_x, startPoint.y, cursor_x, endPoint.y)


    def closeEvent(self, a0):
        return super().closeEvent(a0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TheApp()
    ex.show()
    sys.exit(app.exec())