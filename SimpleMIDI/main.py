import io
import sys
import threading
import time

from Utils import *

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QMouseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QSpinBox, QColorDialog

from PyQt6 import uic


class TheApp(QMainWindow):
    def __init__(self):
        super().__init__()
        with open("App.ui", "r", encoding="UTF-8") as file:
            f = io.StringIO(file.read())
            uic.loadUi(f, self)

        self.centralWidget().setMouseTracking(True)
        #         ------Declarations------
        self.ViewPosition = Vector2()
        self.PrimaryDragInfo = MouseMoveInfo()
        self.SecondaryDragInfo = MouseMoveInfo()
        self.notes = []
        self.noteDisplaySize = Vector2(90, 30)
        self.PitchRange = (0, 70)
        self.PitchPerY = 2

        self.BPM = 120

        self.can_place_note = True
        self.PlaceTimer = QTimer()
        self.PlaceTimer.setSingleShot(True)
        self.PlaceTimer.timeout.connect(lambda: setattr(self, 'can_place_note', True))

        self.PlaybackCursor = PlaybackCursor()

        self.dt = DeltaTime()

        #         ------Threads------

        self.PlayThread = threading.Thread(target=self.Play)

        #         ------Preferences------
        self.COLOR_grid_color = QColor("#3d4750")
        self.COLOR_grid_fill_color = QColor("#333c45")
        self.COLOR_note_fill = QColor(255, 100, 100, 200) #-- можно изменить палитру по желанию
        self.COLOR_note_color = QColor(160, 200, 160)
        self.COLOR_Note_Mark = QColor(0, 0, 0)

        self.notePlacementSnap = 8

        self.centralWidget().setStyleSheet(f"background-color: {self.COLOR_grid_fill_color.name()};")

        #         ------Settings Event Links------

        self.GridWidthSetSpinbox.setValue(self.noteDisplaySize[0])
        self.GridHeightSetSpinbox.setValue(self.noteDisplaySize[1])

        self.GridWidthSetSpinbox.valueChanged.connect(self.UpdateSize)
        self.GridHeightSetSpinbox.valueChanged.connect(self.UpdateSize)

        self.centralWidget().paintEvent = self.CentralPaintEvent
        self.centralWidget().mouseMoveEvent = self.Central_MouseMoveEvent
        self.centralWidget().mousePressEvent = self.Central_MousePressEvent
        self.centralWidget().mouseReleaseEvent = self.Central_MouseReleaseEvent
        self.centralWidget().wheelEvent = self.wheelScrollEvent
        self.pushButton.clicked.connect(self.ColorPick)

        self.actionQuit.triggered.connect(lambda: print("Well... this works"))

        #         ------Logger------
        self.Logger = Logger(self.Log)

        # //StaticMessages//
        self._warn_InvalidPitchSettingsRatio = LogMessage(
            "WARN: InvalidPitchSettingsRatio --- PitchRange / PitchPerY should output an integer, outputs float instead( This makes amount of notes on the piano roll miss out )",
            "warn")
        self._msg_Playback = LogMessage("Playback", "msg")

        self.centralWidget().update()

    def ColorPick(self):
        Color = QColorDialog(self).getColor()
        self.COLOR_grid_fill_color = Color
        print(Color)

    def Play(self):
        self.notes.sort(key=lambda x: x.position.x)
        # ///PLAYBACK GOES HERE///

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
                self._CurrentNoteEditing = Note(
                    self.GetGridCoordinates(Vector2(
                        e.pos().x(),
                        e.pos().y()
                    )),
                    AbsPosition=Vector2(
                        e.pos().x(),
                        e.pos().y()
                    ) + self.ViewPosition
                )

                self._CurrentNoteEditing.position.x = int(
                    self._CurrentNoteEditing.position.x * self.notePlacementSnap) / self.notePlacementSnap

                self.notes.append(self._CurrentNoteEditing)
        self.update()

    def Central_MouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.PrimaryDragInfo.drag = False

        elif e.button() == Qt.MouseButton.RightButton:
            self.SecondaryDragInfo.drag = False

            self.can_place_note = False
            self.PlaceTimer.start(50)

            if hasattr(self, "_CurrentNoteEditing"):
                delattr(self, "_CurrentNoteEditing")
        self.update()

    def ChangePitchParams(self, PitchRange=None, PitchPerY=None):
        if PitchRange is not None:
            self.PitchRange = PitchRange
        if PitchPerY is not None:
            self.PitchPerY = PitchPerY

        if self.PitchRange[1] // self.PitchPerY != self.PitchRange[1] / self.PitchPerY:
            self.Logger.Log(self._warn_InvalidPitchSettingsRatio)
        else:
            self.Logger.RemoveSingleton(self._warn_InvalidPitchSettingsRatio)

        self.centralWidget().update()

    def Central_MouseMoveEvent(self, e: QMouseEvent):
        cw_pos = self.centralWidget().mapFrom(self, e.pos())
        position = Vector2(cw_pos.x(), cw_pos.y())

        self.PrimaryDragInfo.Write(position)
        self.SecondaryDragInfo.Write(position)

        if self.PrimaryDragInfo.drag:
            self.ViewPosition -= self.PrimaryDragInfo.delta

        if self.SecondaryDragInfo.drag and hasattr(self, "_CurrentNoteEditing"):
            current_grid_pos = self.GetGridCoordinates(position)
            current_grid_pos.x = int(current_grid_pos.x * self.notePlacementSnap) / self.notePlacementSnap

            length = current_grid_pos.x - self._CurrentNoteEditing.position.x

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

        painter = QPainter(cw)

        font = painter.font()
        font.setPixelSize(int(self.noteDisplaySize.y / 1.4))

        grid_pen = QPen(self.COLOR_grid_color, 2)
        startPoint = Vector2()
        endPoint = Vector2(startPoint.x + cw.width(), startPoint.y + cw.height())

        # Render Grid

        painter.setPen(QPen(QColor(200, 70, 70), 8))
        painter.drawLine(-self.ViewPosition.x, startPoint.y, -self.ViewPosition.x, endPoint.y)

        # Render Notes

        for note in self.notes:
            note: Note
            painter.setPen(QPen(self.COLOR_note_color))
            painter.setBrush(QBrush(self.COLOR_note_color))
            painter.drawRect(int(note.position.x * self.noteDisplaySize.x - self.ViewPosition.x),
                             (note.position.y) * self.noteDisplaySize.y - self.ViewPosition.y,
                             int(self.noteDisplaySize.x * note.length), self.noteDisplaySize.y)

        for idx, x in enumerate(range(startPoint.x, endPoint.x, self.noteDisplaySize.x)):
            painter.setPen(grid_pen)
            offset = self.ViewPosition.x % self.noteDisplaySize.x
            painter.drawLine(x - offset, startPoint.y, x - offset, endPoint.y)

            painter.setPen(QPen(self.COLOR_Note_Mark))
            beat_number = idx + (self.ViewPosition.x // self.noteDisplaySize.x)
            total_seconds = (beat_number * 60) / self.BPM
            time_text = f"{total_seconds:.1f}s"

            painter.drawText(x - offset, int(self.noteDisplaySize.y / 1.4), time_text)

        for idx, pitch in enumerate(range(self.PitchRange[1], self.PitchRange[0] + 1, -self.PitchPerY)):
            screen_y = (idx * self.noteDisplaySize.y) - self.ViewPosition.y

            painter.setPen(grid_pen)
            painter.drawLine(startPoint.x, screen_y, endPoint.x, screen_y)

            painter.setPen(QPen(self.COLOR_Note_Mark))
            painter.drawText(0, int(screen_y), str(pitch))

    def closeEvent(self, a0):
        del (self.PlayThread)
        return super().closeEvent(a0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = TheApp()
    ex.show()
    sys.exit(app.exec())
