import math

class Quaternions:
    def __init__(self, w, x, y, z):
        """Инициализация кватериона с компонентами w, x, y, z."""
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        """Сложение двух кватерионов."""
        return Quaternions(self.w + other.w, self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        """Вычитание другого кватериона из текущего."""
        return Quaternions(self.w - other.w, self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):
        """Умножение кватериона на другой кватерион или скаляр."""
        if isinstance(other, Quaternions):
            w = self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z
            x = self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y
            y = self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x
            z = self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w
            return Quaternions(w, x, y, z)
        elif isinstance(other, (int, float)):
            return Quaternions(self.w * other, self.x * other, self.y * other, self.z * other)

    def __rmul__(self, other):
        """Перегрузка оператора умножения для скалярного умножения кватериона."""
        return self.__mul__(other)

    def conjugate(self):
        """Возвращает сопряженный кватерион."""
        return Quaternions(self.w, -self.x, -self.y, -self.z)

    def modulus(self):
        """Вычисляет модуль (длину) кватериона."""
        return math.sqrt(self.w ** 2 + self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalize(self):
        """Нормализует кватерион (приводит к единичной длине)."""
        mod = self.modulus()
        if mod == 0:
            raise ValueError("Невозможно нормализовать нулевой кватерион.")
        return Quaternions(self.w / mod, self.x / mod, self.y / mod, self.z / mod)

    def __truediv__(self, other):
        """Деление кватериона на другой кватерион."""
        if not isinstance(other, Quaternions):
            raise ValueError("Делитель должен быть кватерионом.")
        if other.modulus() == 0:
            raise ValueError("Деление на нулевой кватерион невозможно.")
        return self * other.conjugate() * (1 / other.modulus() ** 2)

    def rotate(self, vector):
        """Поворачивает вектор (кватерион с нулевой скалярной частью) с помощью данного кватериона."""
        if not isinstance(vector, Quaternions) or vector.w != 0:
            raise ValueError("Вектор должен быть кватернионом с нулевой скалярной частью.")
        return self * vector * self.conjugate()

    def __eq__(self, other):
        """Сравнивает два кватериона на равенство."""
        if not isinstance(other, Quaternions):
            return NotImplemented
        return (self.w == other.w and
                self.x == other.x and
                self.y == other.y and
                self.z == other.z)

    def __str__(self):
        """Возвращает строковое представление кватериона."""
        return f'({self.w}, {self.x}i, {self.y}j, {self.z}k)'
# Тесты
def run_tests():
    q1 = Quaternions(1, 2, 3, 4)
    q2 = Quaternions(5, 6, 7, 8)

    # Тест сложения
    assert (q1 + q2) == Quaternions(6, 8, 10, 12), "Ошибка в сложении"

    # Тест вычитания
    assert (q1 - q2) == Quaternions(-4, -4, -4, -4), "Ошибка в вычитании"

    # Тест умножения
    assert (q1 * q2) == Quaternions(-60, 12, 30, 24), "Ошибка в умножении"

    # Тест поворота
    vector = Quaternions(0, 1, 0, 0)  # Вектор (1, 0, 0) в виде кватерниона
    rotation = Quaternions(math.cos(math.pi/4), 0, 0, math.sin(math.pi/4))  # Поворот на 90

    print("Все тесты пройдены успешно!")

if __name__ == "__main__":
    run_tests()
