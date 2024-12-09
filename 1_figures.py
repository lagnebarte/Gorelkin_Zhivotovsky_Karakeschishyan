from math import pi


class Shape:
    """Геометрические фигуры"""
    name = 'геометрическая фигура'

    def __init__(self, x=0, y=0):
        self.__x = x
        self.__y = y

    def __repr__(self):
        return f"{self.name} по координатам ({self.__x}, {self.__y})"


class Rectangle(Shape):
    """Прямоугольники"""
    name = 'прямоугольник'

    def __init__(self, width, height, x=0, y=0):
        super().__init__(x, y)
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)

    def __repr__(self):
        return (f"{Shape.__repr__(self)}, со сторонами {self.width} и {self.height},"
                f" с площадью {self.area()} и периметром {self.perimeter()}")


class Square(Shape):
    """Квадраты"""
    name = 'квадрат'

    def __init__(self, side, x=0, y=0):
        super().__init__(x, y)
        self._side = side  # Используем одно свойство для стороны квадрата

    @property
    def side(self):
        return self._side

    @property
    def area(self):
        return self.side ** 2

    @property
    def perimeter(self):
        return 4 * self.side

    def __repr__(self):
        return (f"{Shape.__repr__(self)}, со стороной {self.side},"
                f" с площадью {self.area} и периметром {self.perimeter}")


class Circle(Shape):
    """Круги"""
    name = 'круг'

    def __init__(self, radius, x=0, y=0):
        super().__init__(x, y)
        self.r = radius

    def area(self):
        return pi * self.r ** 2

    def perimeter(self):
        return 2 * pi * self.r

    def __repr__(self):
        return (f"{Shape.__repr__(self)}, с радиусом {self.r},"
                f" с площадью {self.area()} и периметром {self.perimeter()}")


if __name__ == '__main__':
    figures = [Rectangle(2, 3), Square(2, 1, 1), Circle(1)]
    for figure in figures:
        print(figure)
