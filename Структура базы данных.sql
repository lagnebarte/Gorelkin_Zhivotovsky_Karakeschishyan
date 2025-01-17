CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(50),
    full_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active'
);

-- Таблица событий
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    date_time TIMESTAMP NOT NULL,
    creator_id INT REFERENCES users(id) ON DELETE CASCADE
);

-- Таблица участников событий
CREATE TABLE event_participants (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'confirmed'
);

-- Таблица доступности
CREATE TABLE availability (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    date_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'free'
);


ALTER TABLE availability 
ADD CONSTRAINT unique_user_datetime 
UNIQUE (user_id, date_time);