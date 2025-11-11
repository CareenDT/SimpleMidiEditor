import time

from PyQt6.QtWidgets import QTextBrowser
#from Midi import MidiPlayer

#GMidi = MidiPlayer()

class Vector2:
    def __init__(self, x: int = 0 , y: int = 0):
        self.x = x
        self.y = y

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __mul__(self, other):
        return Vector2(self.x * other.x, self.y * other.y)

    def __getitem__(self, item):
        return (self.x, self.y)[item]

    def __invert__(self):
        return Vector2(-self.x, -self.y)

    def __repr__(self):
        return f"Vector2{self.x, self.y}"

class MouseMoveInfo:
    def __init__(self):
        self.position = Vector2()
        self.last = Vector2()
        self.delta = Vector2()
        self.drag = False

        self._IsAtStart = True

        self.start = self.position

    def Write(self, Pos):
        self.last = self.position

        self.position = Pos
        self.delta = self.position - self.last

        if self.drag:
            
            if self._IsAtStart:
                self.start = self.position
            self._IsAtStart = False
        else:
            self._IsAtStart = True
            self.last = self.position

    def SetDrag(self, drag: bool):
        self.drag = drag

    def __repr__(self):
        return f"MouseMoveInfo{(self.position, self.last, self.delta, self.drag, self.start)}"

class LogMessage:
    def __init__(self, Text, Type):
        self.text = Text
        self.type = Type

class Note:
    def __init__(self, Position = Vector2(), Length = 1, AbsPosition = Vector2()):
        self.position = Position
        self.AbsPosition = AbsPosition
        self.length = Length

    def __len__(self):
        return self.length

    def Play(self):
        pass

    def __repr__(self):
        return f"Note{(self.position, self.length)}"

class Logger:
    def __init__(self,Widget):
        self.LogWidget: QTextBrowser
        self.LogWidget: QTextBrowser = Widget
        self.messages: list[LogMessage] = []

    def Log(self, Message: LogMessage, Singleton=True):
        if not Singleton or not Message in self.messages:
            self.messages.append(Message)
        self.Updt()

    def Clear(self):
        self.messages.clear()
        self.Updt()

    def RemoveSingleton(self, Message: LogMessage):
        try:
            self.messages.remove(Message)
        except ValueError:
            pass
        finally:
            self.Updt()

    def Updt(self):
        rs = ""

        colors = {
            "info": "white",
            "warn": "orange", 
            "error": "red",
        }

        for i in self.messages:
            rs = f'{rs}<span style = "color:{colors[i.type]}">{i.text}</span> <br>'

        self.LogWidget.setHtml(rs)

class PlaybackCursor:
    def __init__(self):
        self.Position = 0
        self.isPlaying = False
    def Move(self, By:float, Notes: list[Note], pitchPerY: int):
        self.Position += By
        
        NotesOnPosition = [n for n in Notes if n.position == self.Position]

        for i in NotesOnPosition:
            #GMidi.play_note(i.position.y,duration=i.length)
            pass

class DeltaTime:
    def __init__(self):
        self.last_time = time.time()
    
    def get_delta(self):
        current_time = time.time()
        delta = current_time - self.last_time
        self.last_time = current_time
        return delta