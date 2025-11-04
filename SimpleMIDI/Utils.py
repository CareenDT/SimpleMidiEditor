class Vector2:
    def __init__(self, x: int = 0 , y: int = 0):
        self.x = x
        self.y = y

    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)

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

    def Write(self, Pos):
        self.last = self.position

        self.position = Pos
        self.delta = self.position - self.last

        if ~self.drag:
            self.last = self.position

    def SetDrag(self, drag: bool):
        self.drag = drag
