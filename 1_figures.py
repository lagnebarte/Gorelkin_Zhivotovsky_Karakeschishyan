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
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    def area(self):
        return self.width * self.height

    def perimeter(self):
        return 2 * (self.width + self.height)

    def __repr__(self):
        return (f"{Shape.__repr__(self)}, со сторонами {self.width} и {self.height},"
                f" с площадью {self.area()} и периметром {self.perimeter()}")


class Square(Rectangle):
    """Квадраты"""
    name = 'квадрат'

    def __init__(self, side, x=0, y=0):
        super().__init__(side, side, x, y)


    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._height = self._width = value    # обновление высоты при изменении ширины

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._width = self._height = value    # обновление ширины при изменении высоты

    @property
    def side(self):
        return self._side

    @side.setter
    def side(self, value):
        self._width = self._height = self._side = value


    def __repr__(self):
        return (f"{Shape.__repr__(self)}, со стороной {self.width},"
                f" с площадью {self.area()} и периметром {self.perimeter()}")


def test():
    print("--------------Тесты--------------")        
  
    print("шаг 1") 
    square = Square(5)
    print(square)
    square.height = square.height *2
    print(square)
    
    print("шаг 2") 
    square.side = 4
    print(square)
    print(square.height, square.width)
    
    print("шаг 3") 
    square.height = 3
    print(square)
    print(square.height, square.width)
    
    print("шаг 4") 
    square.width = 2
    print(square)
    print(square.height, square.width)




if __name__ == '__main__':
    test()
