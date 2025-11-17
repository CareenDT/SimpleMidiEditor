import time
from PyQt6.QtWidgets import QTextBrowser

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
    
    def to_dict(self):
        return {'x': self.x, 'y': self.y}
    
    @classmethod
    def from_dict(cls, data):
        return cls(data['x'], data['y'])

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

    def to_dict(self):
        return {
            'position': self.position.to_dict(),
            'lastPosition': self.lastPosition.to_dict(),
            'delta': self.delta.to_dict(),
            'drag': self.drag
        }
    
    @classmethod
    def from_dict(cls, data):
        obj = cls()
        obj.position = Vector2.from_dict(data['position'])
        obj.lastPosition = Vector2.from_dict(data['lastPosition'])
        obj.delta = Vector2.from_dict(data['delta'])
        obj.drag = data['drag']
        return obj

class LogMessage:
    def __init__(self, Text, Type):
        self.text = Text
        self.type = Type

class Note:
    def __init__(self, Position = Vector2(), Length = 1, AbsPosition = Vector2(), instrumentIdx = 0):
        self.position = Position
        self.AbsPosition = AbsPosition
        self.length = Length
        self.instrumentIdx = instrumentIdx

    def __len__(self):
        return self.length

    def __repr__(self):
        return f"Note{(self.position, self.length)}"
    
    def to_dict(self):
        return {
            'position': self.position.to_dict(),
            'length': self.length,
            'instrumentIdx': self.instrumentIdx
        }
    
    @classmethod
    def from_dict(cls, data):
        position = Vector2.from_dict(data['position'])
        note = cls(position)
        note.length = data['length']
        note.instrumentIdx = data.get('instrumentIdx', 0)
        return note
    
    def __repr__(self):
        return f"Note(pos={self.position}, len={self.length}, inst={self.instrumentIdx})"

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
            rs = f'{(time.strftime("%H:%M:%S", time.localtime()))} /// {rs}<span style = "color:{colors[i.type]}; line-height: 30px">{i.text}</span> <br>'

        self.LogWidget.setHtml(rs)

class PlaybackCursor:
    def __init__(self):
        self.Position = 0
        self.isPlaying = False