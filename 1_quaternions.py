
import math

class Quaternions:
    def __init__(self, w, x, y, z):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):  # сложение
        return Quaternions(self.w + other.w, self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):  # вычитание
        return Quaternions(self.w - other.w, self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other):  # умножение
        if isinstance(other, Quaternions):
            w = self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z
            x = self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y
            y = self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x
            z = self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w
            return Quaternions(w, x, y, z)
        elif isinstance(other, (int, float)):  # умножение на число
            return Quaternions(self.w * other, self.x * other, self.y * other, self.z * other)

    def __rmul__(self, other):  # умножение числа на кватерион
        return self.__mul__(other)

    def conjugate(self):  # сопряжение
        return Quaternions(self.w, -self.x, -self.y, -self.z)

    def modulus(self):  # модуль
        return math.sqrt(self.w ** 2 + self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalize(self):  # нормализация
        mod = self.modulus()
        if mod == 0:
            raise ValueError("Невозможно нормализовать нулевой кватерион.")
        return Quaternions(self.w / mod, self.x / mod, self.y / mod, self.z / mod)

    def __truediv__(self, other):  # деление
        if not isinstance(other, Quaternions):
            raise ValueError("Делитель должен быть кватерионом.")
        if other.modulus() == 0:
            raise ValueError("Деление на нулевой кватерион невозможно.")
        return self * other.conjugate() * (1 / other.modulus() ** 2)

    def __str__(self):
        return f'({self.w}, {self.x}i, {self.y}j, {self.z}k)'

# Пример использования
q1 = Quaternions(1, 2, 3, 4)
q2 = Quaternions(5, 6, 7, 8)
q3 = Quaternions(100, 100, 100, 100)

# Деление и вычитание
Q = q1 - (q2 / q3)
print(Q)
