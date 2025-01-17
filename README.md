# Gorelkin_Zhivotovsky_Karakeschishyan
Репозиторий для публикации решений домашних задач по дисциплине "Разработка приложений на Python", выполненных студентами группы 5130203/20102 Животовским Дмитрием (lagnebarte), Горелкиным Алексеем (sadmonke52), Каракещишян Андроником (evilmeandr)

## Telegram Event Management Bot

Этот проект представляет собой Telegram-бота для управления событиями и встречами. Бот позволяет пользователям создавать события, приглашать участников, проверять доступность и управлять своими событиями.

### Функциональность

- **Создание событий**: Пользователи могут создавать события с указанием названия, описания, даты и времени.
- **Приглашение участников**: Пользователи могут приглашать других пользователей на свои события.
- **Проверка доступности**: Пользователи могут устанавливать свой статус доступности (свободен или занят) и проверять доступность на определенную дату и время.
- **Управление событиями**: Пользователи могут просматривать свои события, удалять события и участников.
- **Уведомления**: Бот отправляет уведомления пользователям о новых приглашениях и изменениях статуса событий.

### Установка


1. **Настройка базы данных**:

   Создайте базу данных PostgreSQL и выполните необходимые SQL-запросы для создания таблиц `users`, `events`, `event_participants`, `availability`. 

   Пример SQL-запросов для создания таблиц:

   ```sql
   CREATE TABLE users (
       id SERIAL PRIMARY KEY,
       telegram_id BIGINT UNIQUE,
       username VARCHAR(255),
       full_name VARCHAR(255)
   );

   CREATE TABLE events (
       id SERIAL PRIMARY KEY,
       name VARCHAR(255),
       description TEXT,
       date_time TIMESTAMP,
       creator_id INT REFERENCES users(id)
   );

   CREATE TABLE event_participants (
       id SERIAL PRIMARY KEY,
       event_id INT REFERENCES events(id),
       user_id INT REFERENCES users(id),
       status VARCHAR(50)
   );

   CREATE TABLE availability (
       id SERIAL PRIMARY KEY,
       user_id INT REFERENCES users(id),
       date_time TIMESTAMP,
       status VARCHAR(50)
   );
   ```

2. **Настройка бота**:

   В файле с кодом замените `BOT_TOKEN` на ваш токен бота, полученный от [BotFather](https://t.me/botfather).

   ```python
   BOT_TOKEN = "YOUR_BOT_TOKEN"
   ```

   Настройте параметры подключения к базе данных в `DB_CONFIG`.
