import io
import sys

from Utils import *

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QMouseEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QSpinBox

from PyQt6 import uic


class MyApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        with open("App.ui", "r", encoding="UTF-8") as file:
            f = io.StringIO(file.read())
            uic.loadUi(f, self)

        self.centralWidget().setMouseTracking(True)

        self.notes = []
        self.noteDisplaySize = Vector2(38, 6)

        #Pref
        self.grid_color = QColor("#4d68b2")
        self.grid_fill_color = QColor("#644db2")
        self.note_fill = QColor(255, 100, 100, 200)
        self.note_border = QColor(0, 0, 0)

        self.centralWidget().setStyleSheet(f"background-color: {self.grid_fill_color.name()};")

        self.GridWidthSetSpinbox.setValue(self.noteDisplaySize[0])
        self.GridHeightSetSpinbox.setValue(self.noteDisplaySize[1])

        self.GridWidthSetSpinbox.valueChanged.connect(self.UpdateSize)
        self.GridHeightSetSpinbox.valueChanged.connect(self.UpdateSize)

        self.ViewPosition = Vector2()

        self.DragInfo = MouseMoveInfo()

        self.centralWidget().paintEvent = self.CentralPaintEvent
        self.centralWidget().mouseMoveEvent = self.Central_MouseMoveEvent
        self.centralWidget().mousePressEvent = self.Central_MousePressEvent
        self.centralWidget().mouseReleaseEvent = self.Central_MouseReleaseEvent
        self.centralWidget().wheelEvent = self.wheelScrollEvent

        self.PitchBound = (-50,50)
        self.PitchPerNote = 5

        self.centralWidget().update()

    def GetGridCoordinates(self, mouse_pos):

        #midi_pitch = self.PitchBound[0] + (grid_y * self.PitchPerNote)
        return# Vector2(grid_x)#, grid_y), midi_pitch

    def Central_MousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.DragInfo.drag = True
        elif e.button() == Qt.MouseButton.RightButton:
            print(self.GetGridCoordinates(Vector2(e.pos().x(), e.pos().y())))

    def Central_MouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.DragInfo.drag = False

    def Central_MouseMoveEvent(self, e: QMouseEvent):
        cw_pos = self.centralWidget().mapFrom(self, e.pos())
        position = Vector2(cw_pos.x(), cw_pos.y())

        self.DragInfo.Write(position)

        if self.DragInfo.drag:
            self.ViewPosition -= self.DragInfo.delta

        self.centralWidget().update()

    def wheelScrollEvent(self,event):
        scroll_amount = event.angleDelta().y() // 16

        self.noteDisplaySize.x = min(max(8, self.noteDisplaySize.x + scroll_amount),99)

        self.GridWidthSetSpinbox.setValue(self.noteDisplaySize.x)

        self.centralWidget().update()

    def UpdateSize(self):
        self.noteDisplaySize = Vector2(self.GridWidthSetSpinbox.value(), self.GridHeightSetSpinbox.value())
        self.centralWidget().update()

    def CentralPaintEvent(self, event):
        cw = self.centralWidget()

        painter = QPainter(cw)
        painter.begin(self)
        grid_pen = QPen(self.grid_color,2)
        startPoint = Vector2()
        endPoint = Vector2(startPoint.x + cw.width(), startPoint.y + cw.height())

        #Render Grid

        for x in range(startPoint.x, endPoint.x, self.noteDisplaySize.x):
            painter.setPen(grid_pen)
            offset = self.ViewPosition.x % self.noteDisplaySize.x
            painter.drawLine(x - offset, startPoint.y, x - offset, endPoint.y)

        for pitch in range(self.PitchBound[0], self.PitchBound[1] + 1, self.PitchPerNote):

            pitch_index = pitch - self.PitchBound[0]
            screen_y = pitch_index * self.noteDisplaySize.y - self.ViewPosition.y

            painter.setPen(grid_pen)
            painter.drawLine(startPoint.x, screen_y, endPoint.x, screen_y)

        painter.setPen(QPen(QColor(200,70,70),8))
        painter.drawLine(-self.ViewPosition.x, startPoint.y, -self.ViewPosition.x, endPoint.y)

        painter.end()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MyApplication()
    ex.show()
    sys.exit(app.exec())
