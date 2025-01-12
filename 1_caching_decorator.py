def cache_it(max_size=5):
    def decorator(func):
        cache = {}  # словарь для кэша
        queue = []  # очередь для LRU

        def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)  # ключ из аргументов
            if key in cache:  # если есть в кэше - возвращаем
                # обновляем очередь
                queue.remove(key)
                queue.append(key)
                print(f"Из кэша для {args}, {kwargs}")
                return cache[key]

            result = func(*args, **kwargs)   # вычисляем новое значение
            if len(cache) >= max_size:   # если кэш полный - удаляем старый элемент
                old_key = queue.pop(0)
                del cache[old_key]

            cache[key] = result  # добавляем новый результат
            queue.append(key)
            return result
        return wrapper
    return decorator

@cache_it(max_size=2)
def add(x, y):
    print(f"Вычисляем {x} + {y}")
    return x + y

@cache_it(max_size=3)
def multiply(x, y):
    print(f"Вычисляем {x} * {y}")
    return x * y

if __name__ == "__main__":
    print(add(2, 3))  # выведет "Вычисляем 2 + 3" и результат
    print(add(2, 3))  # выведет результат из кэша
    print(add(4, 5))
    print(add(6, 7))  # выведет "Вычисляем 6 + 7" и вытеснит первый результат

    print(multiply(2, 3))  # выведет "Вычисляем 2 * 3" и результат
    print(multiply(2, 3))  # из кэша
    print(multiply(4, 5))
    print(multiply(6, 7))
    print(multiply(8, 9))  # считаем 8 * 9 -> вытесняет (2, 3)



