import telebot
import psycopg2
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import types

BOT_TOKEN = "7856265146:AAFc5CgMuXvxT27RCNVu7pZKznrKeE-JWhY"
bot = telebot.TeleBot(BOT_TOKEN)

DB_CONFIG = {
    "dbname": "calendar_bot",
    "user": "postgres",
    "password": "Andronik_",
    "host": "localhost"
}

def db_connect():
    return psycopg2.connect(**DB_CONFIG)

def make_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("📅 Создать событие"),
        KeyboardButton("📊 Мои события"),
        KeyboardButton("🕒 Отметить занятость"),
        KeyboardButton("📩 Пригласить участников"),
        KeyboardButton("❌ Удалить участника"),
        KeyboardButton("🗑 Удалить событие"),
        KeyboardButton("🚫 Отказаться от участия"),
        KeyboardButton("📨 Мои приглашения")
    ]
    kb.add(*buttons)
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE telegram_id = %s",
                (message.from_user.id,))
    user = cur.fetchone()
    msg = "👋 Привет! Я бот для управления событиями и встречами.\n\n"

    if not user:
        cur.execute("""
            INSERT INTO users (telegram_id, username, full_name)
            VALUES (%s, %s, %s)
        """, (
            message.from_user.id,
            message.from_user.username,
            f"{message.from_user.first_name} {message.from_user.last_name or ''}"))
        conn.commit()
        msg += "✅ Регистрация прошла успешно!\n\n"

    msg += "Используйте кнопки ниже:"
    bot.reply_to(message, msg, reply_markup=make_keyboard())
    cur.close()
    conn.close()

@bot.message_handler(func=lambda m: m.text == "📅 Создать событие")
def new_event(message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("❌ Отмена"))
    msg = bot.reply_to(message, "📝 Введите название:", reply_markup=kb)
    bot.register_next_step_handler(msg, get_name)

def get_name(message):
    if message.text == "❌ Отмена":
        bot.reply_to(message, "❌ Создание события отменено", reply_markup=make_keyboard())
        return

    event = {'creator': message.from_user.id}
    event['name'] = message.text
    msg = bot.reply_to(message, "📋 Введите описание (или '-' чтобы пропустить):")
    bot.register_next_step_handler(msg, get_desc, event)

def get_desc(message, event):
    if message.text == "❌ Отмена":
        bot.reply_to(message, "❌ Создание события отменено", reply_markup=make_keyboard())
        return

    event['desc'] = None if message.text == '-' else message.text
    msg = bot.reply_to(message, "🕒 Введите дату и время (ГГГГ-ММ-ДД ЧЧ:ММ):")
    bot.register_next_step_handler(msg, get_time, event)

def get_time(message, event):
    if message.text == "❌ Отмена":
        bot.reply_to(message, "❌ Создание события отменено", reply_markup=make_keyboard())
        return

    try:
        dt = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        if dt < datetime.now():
            msg = bot.reply_to(message, "⚠️ Укажите будущую дату:")
            bot.register_next_step_handler(msg, get_time, event)
            return
        event['time'] = dt
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add(KeyboardButton("➖ Без участников"))
        kb.add(KeyboardButton("❌ Отмена"))
        msg = bot.reply_to(message,
            "👥 Укажите участников через запятую (@user1, @user2) или выберите 'Без участников':",
            reply_markup=kb)
        bot.register_next_step_handler(msg, get_users, event)
    except ValueError:
        msg = bot.reply_to(message, "⚠️ Неверный формат. Используйте: ГГГГ-ММ-ДД ЧЧ:ММ")
        bot.register_next_step_handler(msg, get_time, event)

def get_users(message, event):
    if message.text == "❌ Отмена":
        bot.reply_to(message, "❌ Создание события отменено", reply_markup=make_keyboard())
        return

    conn = db_connect()
    cur = conn.cursor()

    # получаем создателя
    cur.execute("""
        SELECT id, username 
        FROM users 
        WHERE telegram_id = %s
    """, (event['creator'],))
    creator_id, creator_name = cur.fetchone()

    # создаем событие
    cur.execute("""
        INSERT INTO events (name, description, date_time, creator_id)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """, (event['name'], event['desc'], event['time'], creator_id))
    event_id = cur.fetchone()[0]

    results = {'ok': [], 'busy': [], 'not_found': []}
    if message.text != "➖ Без участников":
        users = [u.strip().replace('@', '') for u in message.text.split(',')]
        kb = InlineKeyboardMarkup()
        kb.row(
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_{event_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{event_id}"))

        for username in users:
            cur.execute("SELECT id, telegram_id FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

            if not user:
                results['not_found'].append(username)
                continue

            # проверяем занятость
            cur.execute("""
                SELECT status 
                FROM availability 
                WHERE user_id = %s AND date_time = %s
            """, (user[0], event['time']))

            if cur.fetchone():
                results['busy'].append(username)
                continue

            cur.execute("""
                INSERT INTO event_participants (event_id, user_id, status)
                VALUES (%s, %s, 'pending')
            """, (event_id, user[0]))

            results['ok'].append(username)
            invite = f"""
🎫 Новое приглашение!

📅 {event['name']}
🕒 {event['time'].strftime('%Y-%m-%d %H:%M')}
👤 От: @{creator_name}
"""
            if event['desc']:
                invite += f"📝 {event['desc']}\n"
            bot.send_message(user[1], invite, reply_markup=kb)


    conn.commit()
    resp = f"""
🎉 Событие создано!

📅 {event['time'].strftime('%Y-%m-%d')}
🕒 {event['time'].strftime('%H:%M')}
"""
    if event['desc']:
        resp += f"📝 {event['desc']}\n"

    if message.text == "➖ Без участников":
        resp += "\n👤 Событие создано без участников"
    else:
        if results['ok']:
            resp += f"\n📨 Приглашены: @{', @'.join(results['ok'])}"
        if results['busy']:
            resp += f"\n⚠️ Заняты: @{', @'.join(results['busy'])}"
        if results['not_found']:
            resp += f"\n❌ Не найдены: @{', @'.join(results['not_found'])}"

    bot.reply_to(message, resp, reply_markup=make_keyboard())
    cur.close()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith(('accept_', 'reject_')))
def handle_invitation_response(call):
    action, event_id = call.data.split('_')
    event_id = int(event_id)
    conn = db_connect()
    cursor = conn.cursor()

    # Получаем информацию о событии
    cursor.execute("""
        SELECT e.name, u.username
        FROM events e
        JOIN users u ON e.creator_id = u.id
        WHERE e.id = %s
    """, (event_id,))

    event = cursor.fetchone()
    if not event:
        bot.answer_callback_query(call.id, "❌ Событие не найдено")
        cursor.close()
        conn.close()
        return

    event_name, creator_username = event

    # Обновляем статус участника
    status = 'confirmed' if action == 'accept' else 'declined'
    cursor.execute("""
        UPDATE event_participants
        SET status = %s
        WHERE event_id = %s 
        AND user_id = (
            SELECT id FROM users 
            WHERE telegram_id = %s
        )
        RETURNING (
            SELECT username FROM users 
            WHERE telegram_id = %s
        )
    """, (status, event_id, call.message.chat.id, call.message.chat.id))

    result = cursor.fetchone()
    if result:
        participant_username = result[0]

        if action == 'accept':
            response_text = "✅ Вы приняли приглашение!"
        else:
            response_text = "❌ Вы отклонили приглашение!"

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None)

        new_message_text = call.message.text + f"\n\n{response_text}"
        bot.edit_message_text(
            text=new_message_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id)

        # Отправляем уведомление создателю события
        cursor.execute("""
            SELECT telegram_id 
            FROM users 
            WHERE username = %s
        """, (creator_username,))
        creator_chat = cursor.fetchone()

        if creator_chat:
            if action == 'accept':
                creator_notification = f"✅ Пользователь @{participant_username} принял приглашение на событие '{event_name}'"
            else:
                creator_notification = f"❌ Пользователь @{participant_username} отклонил приглашение на событие '{event_name}'"

            bot.send_message(creator_chat[0], creator_notification)

        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, "❌ Приглашение не найдено или уже обработано")

    conn.commit()
    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == "📊 Мои события")
def my_events(message):
    conn = db_connect()
    cursor = conn.cursor()
    # Выбираем события где я создатель или участник
    cursor.execute("""
        SELECT 
            e.name, 
            e.date_time, 
            e.description, 
            u.username,
            e.creator_id = (SELECT id FROM users WHERE telegram_id = %s) as is_creator,
            (
                SELECT COUNT(*) 
                FROM event_participants ep2 
                WHERE ep2.event_id = e.id 
                AND ep2.status = 'confirmed'
            ) as participants
        FROM events e
        JOIN users u ON e.creator_id = u.id
        LEFT JOIN event_participants ep ON e.id = ep.event_id 
            AND ep.user_id = (SELECT id FROM users WHERE telegram_id = %s)
        WHERE 
            e.creator_id = (SELECT id FROM users WHERE telegram_id = %s)
            OR (ep.user_id = (SELECT id FROM users WHERE telegram_id = %s) 
                AND ep.status = 'confirmed')
        ORDER BY e.date_time
    """, (message.from_user.id, message.from_user.id, message.from_user.id, message.from_user.id))
    events = cursor.fetchall()

    if not events:
        response = "У вас нет запланированных событий."
    else:
        response = "📋 Ваши события:\n\n"
        for e in events:
            response += f"📅 {e[0]}\n"  # Название
            response += f"🕒 {e[1].strftime('%Y-%m-%d %H:%M')}\n"  # Дата
            if e[2]:  # Если есть описание
                response += f"📝 {e[2]}\n"
            response += f"👤 Организатор: @{e[3]}\n"
            response += f"👥 Подтвердили участие: {e[5]} участников\n"
            if e[4]:  # Если я создатель
                response += "🎯 Вы организатор\n"
            else:
                response += "✅ Вы участник\n"
            response += "\n"
    bot.reply_to(message, response, reply_markup=make_keyboard())
    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == "📩 Пригласить участников")
def invite_to_event(message):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.name, e.date_time
        FROM events e
        JOIN users u ON e.creator_id = u.id
        WHERE u.telegram_id = %s
        AND e.date_time > NOW()
        ORDER BY e.date_time
    """, (message.from_user.id,))
    events = cursor.fetchall()
    cursor.close()
    conn.close()

    if not events:
        bot.reply_to(
            message,
            "У вас нет предстоящих событий, в которые можно пригласить участников.",
            reply_markup=make_keyboard())
        return

    keyboard = InlineKeyboardMarkup()
    for e in events:
        btn_text = f"{e[1]} ({e[2].strftime('%Y-%m-%d %H:%M')})"
        callback = f"invite_{e[0]}"
        keyboard.add(InlineKeyboardButton(text=btn_text, callback_data=callback))
    keyboard.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_invite"))
    bot.reply_to(message,"Выберите событие для приглашения участников:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_invite")
def handle_invite_cancel(call):
    bot.edit_message_text(
        "❌ Приглашение участников отменено",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('invite_'))
def handle_invite_selection(call):
    event_id = int(call.data.split('_')[1])
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("❌ Отмена"))
    msg = bot.send_message(
        call.message.chat.id,
        "Введите username пользователей через запятую (@user1, @user2):",
        reply_markup=kb)
    bot.register_next_step_handler(msg, process_invites, event_id)
def process_invites(message, event_id):
    if message.text == "❌ Отмена":
        bot.reply_to(message, "❌ Приглашение участников отменено", reply_markup=make_keyboard())
        return

    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.name, e.date_time, u.username as creator
        FROM events e
        JOIN users u ON e.creator_id = u.id
        WHERE e.id = %s
    """, (event_id,))
    event = cursor.fetchone()

    if not event:
        bot.reply_to(message, "Событие не найдено.", reply_markup=make_keyboard())
        cursor.close()
        conn.close()
        return

    usernames = message.text.split(',')
    usernames = [u.strip().replace('@', '') for u in usernames]
    invited = []
    already_invited = []
    not_found = []
    unavailable = []
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("✅ Принять", callback_data=f"accept_{event_id}"),
        InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{event_id}"))

    for username in usernames:
        cursor.execute(
            "SELECT id, telegram_id FROM users WHERE username = %s",
            (username,))
        user = cursor.fetchone()

        if not user:
            not_found.append(username)
            continue

        cursor.execute("""
            SELECT id FROM event_participants
            WHERE event_id = %s AND user_id = %s
        """, (event_id, user[0]))

        if cursor.fetchone():
            already_invited.append(username)
            continue

        cursor.execute("""
            SELECT status FROM availability
            WHERE user_id = %s AND date_time = %s
        """, (user[0], event[1]))

        avail = cursor.fetchone()
        if avail and avail[0] == 'busy':
            unavailable.append(username)
            continue

        cursor.execute("""
            INSERT INTO event_participants (event_id, user_id, status)
            VALUES (%s, %s, 'pending')
        """, (event_id, user[0]))

        invited.append(username)

        invite_text = f"""
🎫 Вас пригласили на событие!

📅 Название: {event[0]}
🕒 Дата и время: {event[1].strftime('%Y-%m-%d %H:%M')}
👤 Организатор: @{event[2]}
"""
        bot.send_message(user[1], invite_text, reply_markup=keyboard)

    conn.commit()
    response = "Результаты приглашения:\n"
    if invited:
        response += f"\n✅ Приглашены: @{', @'.join(invited)}"
    if already_invited:
        response += f"\n📝 Уже приглашены: @{', @'.join(already_invited)}"
    if unavailable:
        response += f"\n⚠️ Недоступны: @{', @'.join(unavailable)}"
    if not_found:
        response += f"\n❌ Не найдены: @{', @'.join(not_found)}"

    bot.reply_to(message, response, reply_markup=make_keyboard())
    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == "🗑 Удалить событие")
def delete_event(message):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.name, e.date_time
        FROM events e
        JOIN users u ON e.creator_id = u.id
        WHERE u.telegram_id = %s
        ORDER BY e.date_time
    """, (message.from_user.id,))
    events = cursor.fetchall()
    cursor.close()
    conn.close()

    if not events:
        bot.reply_to(
            message,
            "У вас нет предстоящих событий, которые можно удалить.",
            reply_markup=make_keyboard())
        return

    keyboard = InlineKeyboardMarkup()
    for e in events:
        btn_text = f"{e[1]} ({e[2].strftime('%Y-%m-%d %H:%M')})"
        callback = f"delete_{e[0]}"
        keyboard.add(InlineKeyboardButton(text=btn_text, callback_data=callback))
    keyboard.add(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete"))

    bot.reply_to(
        message,
        "Выберите событие для удаления:",
        reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "cancel_delete")
def handle_delete_cancel(call):
    bot.edit_message_text(
        "❌ Удаление события отменено",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_delete_selection(call):
    event_id = int(call.data.split('_')[1])
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{event_id}"),
        InlineKeyboardButton("❌ Нет, отмена", callback_data=f"cancel_delete_{event_id}"))
    bot.edit_message_text(
        "Вы уверены, что хотите удалить это событие? Все участники получат уведомление об отмене.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('confirm_delete_', 'cancel_delete_')))
def handle_delete_confirmation(call):
    action = call.data.split('_')[0]
    event_id = int(call.data.split('_')[2])

    if action == 'cancel':
        bot.edit_message_text(
            "❌ Удаление отменено",
            call.message.chat.id,
            call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.name, e.date_time 
        FROM events e
        JOIN users u ON e.creator_id = u.id
        WHERE e.id = %s AND u.telegram_id = %s
    """, (event_id, call.message.chat.id))

    event = cursor.fetchone()
    if not event:
        bot.answer_callback_query(call.id, "❌ У вас нет прав на удаление этого события")
        cursor.close()
        conn.close()
        return

    cursor.execute("""
        SELECT u.telegram_id
        FROM event_participants ep
        JOIN users u ON ep.user_id = u.id
        WHERE ep.event_id = %s
    """, (event_id,))

    participants = cursor.fetchall()

    cursor.execute("DELETE FROM event_participants WHERE event_id = %s", (event_id,))
    cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
    conn.commit()

    bot.edit_message_text(
        f"✅ Событие '{event[0]}' успешно удалено",
        call.message.chat.id,
        call.message.message_id)
    bot.answer_callback_query(call.id)

    notif_text = f"""
❌ Событие отменено!

📅 Название: {event[0]}
🕒 Дата и время: {event[1].strftime('%Y-%m-%d %H:%M')}

Организатор отменил это событие.
"""

    for p in participants:
        bot.send_message(p[0], notif_text)

    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == "🚫 Отказаться от участия")
def leave_event(message):
    conn = db_connect()
    cursor = conn.cursor()
    # Получаем список событий, в которых пользователь участвует
    cursor.execute("""
        SELECT e.id, e.name, e.date_time
        FROM events e
        JOIN event_participants ep ON e.id = ep.event_id
        WHERE ep.user_id = (SELECT id FROM users WHERE telegram_id = %s)
        AND e.creator_id != (SELECT id FROM users WHERE telegram_id = %s)
        AND ep.status = 'confirmed'
    """, (message.from_user.id, message.from_user.id))
    events = cursor.fetchall()

    if not events:
        bot.reply_to(message, "У вас нет событий, от которых можно отказаться.", reply_markup=make_keyboard())
        return
    keyboard = InlineKeyboardMarkup()

    for event in events:
        button_text = f"{event[1]} ({event[2].strftime('%Y-%m-%d %H:%M')})"
        callback_data = f"leave_{event[0]}"
        keyboard.add(InlineKeyboardButton(button_text, callback_data=callback_data))
    bot.reply_to(message, "Выберите событие для отказа:", reply_markup=keyboard)
    cursor.close()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('leave_'))
def handle_leave_selection(call):
    event_id = int(call.data.split('_')[1])
    confirm_keyboard = InlineKeyboardMarkup()
    confirm_keyboard.row(
        InlineKeyboardButton("✅ Да, отказаться", callback_data=f"confirm_leave_{event_id}"),
        InlineKeyboardButton("❌ Нет, остаться", callback_data=f"cancel_leave_{event_id}"))
    bot.edit_message_text(
        "Вы уверены, что хотите отказаться от участия в этом событии? Организатор получит уведомление.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=confirm_keyboard
    )
@bot.callback_query_handler(func=lambda call: call.data.startswith(('confirm_leave_', 'cancel_leave_')))
def handle_leave_confirmation(call):
    action, _, event_id = call.data.split('_')
    event_id = int(event_id)
    if action == 'cancel':
        bot.edit_message_text(
            "Вы остались участником события.",
            call.message.chat.id,
            call.message.message_id)
        bot.answer_callback_query(call.id)
        return
    conn = db_connect()
    cursor = conn.cursor()
    # Проверяем, что событие существует
    cursor.execute("""
        SELECT e.name, e.date_time, u.username, u.telegram_id
        FROM events e
        JOIN users u ON e.creator_id = u.id
        WHERE e.id = %s
    """, (event_id,))

    event = cursor.fetchone()
    if not event:
        bot.answer_callback_query(call.id, "Событие не найдено.")
        return

    event_name, event_date, creator_username, creator_telegram_id = event
    # Удаляем пользователя из участников
    cursor.execute("""
        DELETE FROM event_participants
        WHERE event_id = %s AND user_id = (SELECT id FROM users WHERE telegram_id = %s)
    """, (event_id, call.message.chat.id))

    if cursor.rowcount == 0:
        bot.answer_callback_query(call.id, "Вы не являетесь участником этого события.")
        return

    conn.commit()
    bot.edit_message_text(
        f"Вы отказались от участия в событии '{event_name}'.",
        call.message.chat.id,
        call.message.message_id)
    bot.answer_callback_query(call.id)
    notification = f"""
❌ Отказ от участия

👤 Пользователь: @{call.from_user.username}
📅 Событие: {event_name}
🕒 Дата и время: {event_date.strftime('%Y-%m-%d %H:%M')}
    """
    bot.send_message(creator_telegram_id, notification)
    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == "❌ Удалить участника")
def remove_participant(message):
    conn = db_connect()
    cursor = conn.cursor()
    # Получаем события, где пользователь является организатором
    cursor.execute("""
        SELECT e.id, e.name, e.date_time
        FROM events e
        JOIN users u ON e.creator_id = u.id
        WHERE u.telegram_id = %s
        AND e.date_time > NOW()
        ORDER BY e.date_time
    """, (message.from_user.id,))

    events = cursor.fetchall()
    if not events:
        bot.reply_to(message, "У вас нет предстоящих событий, где вы организатор.", reply_markup=make_keyboard())
        return

    event_keyboard = InlineKeyboardMarkup()
    for event in events:
        button_text = f"{event[1]} ({event[2].strftime('%Y-%m-%d %H:%M')})"
        callback_data = f"select_event_remove_{event[0]}"
        event_keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    bot.reply_to(message, "Выберите событие, из которого хотите удалить участника:", reply_markup=event_keyboard)
    cursor.close()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_event_remove_'))
def handle_event_selection_for_remove(call):
    event_id = int(call.data.split('_')[-1])
    conn = db_connect()
    cursor = conn.cursor()

    # Получаем список участников события
    cursor.execute("""
        SELECT 
            u.id,
            u.username,
            u.telegram_id
        FROM users u
        JOIN event_participants ep ON u.id = ep.user_id
        WHERE ep.event_id = %s
        AND ep.status = 'confirmed'
        AND u.id != (SELECT creator_id FROM events WHERE id = %s)
    """, (event_id, event_id))

    participants = cursor.fetchall()
    if not participants:
        bot.edit_message_text(
            "В этом событии нет подтверждённых участников.",
            call.message.chat.id,
            call.message.message_id)
        return

    participant_keyboard = InlineKeyboardMarkup()
    for participant in participants:
        button_text = f"@{participant[1]}"
        callback_data = f"remove_participant_{event_id}_{participant[0]}"
        participant_keyboard.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    participant_keyboard.add(InlineKeyboardButton("🔙 Отмена", callback_data="cancel_remove_participant"))
    bot.edit_message_text(
        "Выберите участника для удаления:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=participant_keyboard)
    cursor.close()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('remove_participant_'))
def handle_remove_participant(call):
    _, _, event_id, user_id = call.data.split('_')
    event_id = int(event_id)
    user_id = int(user_id)
    conn = db_connect()
    cursor = conn.cursor()

    # Проверяем, что пользователь является организатором события
    cursor.execute("""
        SELECT e.name, e.date_time, u.telegram_id, u.username
        FROM events e
        JOIN users u ON u.id = %s
        WHERE e.id = %s
        AND e.creator_id = (SELECT id FROM users WHERE telegram_id = %s)
    """, (user_id, event_id, call.message.chat.id))

    event_info = cursor.fetchone()
    if not event_info:
        bot.answer_callback_query(call.id, "У вас нет прав на удаление участников из этого события")
        return

    event_name, event_date, participant_telegram_id, participant_username = event_info

    # Удаляем участника
    cursor.execute("""
        DELETE FROM event_participants
        WHERE event_id = %s AND user_id = %s
    """, (event_id, user_id))
    conn.commit()

    # Отправляем подтверждение организатору
    bot.edit_message_text(
        f"✅ Участник @{participant_username} удалён из события '{event_name}'",
        call.message.chat.id,
        call.message.message_id)
    bot.answer_callback_query(call.id)
    notification_text = f"""
❌ Вы были удалены из события

📅 Название: {event_name}
🕒 Дата и время: {event_date.strftime('%Y-%m-%d %H:%M')}

Организатор удалил вас из списка участников.
"""
    bot.send_message(participant_telegram_id, notification_text)
    cursor.close()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data == "cancel_remove_participant")
def handle_cancel_remove(call):
    bot.edit_message_text(
        "❌ Удаление участника отменено",
        call.message.chat.id,
        call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: message.text == "🕒 Отметить занятость")
def set_availability(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_button = types.KeyboardButton("❌ Отмена")
    markup.add(cancel_button)

    msg = bot.reply_to(message, """ 
🕒 Установка доступности

Введите дату, время и статус в формате:
ГГГГ-ММ-ДД ЧЧ:ММ статус

Статус может быть:
✅ free - свободен
❌ busy - занят

Пример: 2025-01-10 15:00 busy
""", reply_markup=markup)
    bot.register_next_step_handler(msg, save_availability)

def save_availability(message):
    if message.text == "❌ Отмена":
        bot.reply_to(message, "Операция отменена", reply_markup=make_keyboard())
        return
    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, """
⚠️ Неверный формат. 

Правильный формат: ГГГГ-ММ-ДД ЧЧ:ММ статус

Пример: 2025-01-10 15:00 busy
""", reply_markup=make_keyboard())
        return

    date_time_str = f"{args[0]} {args[1]}"
    status = args[2].lower()
    if status not in ['busy', 'free']:
        bot.reply_to(message, "⚠️ Статус должен быть 'busy' или 'free'", reply_markup=make_keyboard())
        return

    try:
        date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
    except ValueError:
        bot.reply_to(message, "⚠️ Неверный формат даты и времени", reply_markup=make_keyboard())
        return

    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, full_name 
        FROM users 
        WHERE telegram_id = %s
    """, (message.from_user.id,))
    user_data = cursor.fetchone()

    if not user_data:
        bot.reply_to(message, "⚠️ Пользователь не найден. Используйте /start для регистрации.", reply_markup=make_keyboard())
        return

    user_id, user_fullname = user_data
    cursor.execute("""
        INSERT INTO availability (user_id, date_time, status)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, date_time)
        DO UPDATE SET status = EXCLUDED.status
    """, (user_id, date_time, status))

    if status == 'busy':
        cursor.execute("""
            SELECT e.id, e.name, e.creator_id, e.date_time
            FROM events e
            JOIN event_participants ep ON e.id = ep.event_id
            WHERE ep.user_id = %s 
            AND DATE(e.date_time) = DATE(%s)
            AND ep.status = 'confirmed'
        """, (user_id, date_time))

        events = cursor.fetchall()
        for event in events:
            event_id, event_name, creator_id, event_date = event
            cursor.execute("""
                UPDATE event_participants
                SET status = 'cancelled'
                WHERE event_id = %s AND user_id = %s
            """, (event_id, user_id))
            notify_event_creator(bot, creator_id, user_fullname, event_name, event_date.strftime('%Y-%m-%d %H:%M'))

    conn.commit()
    status_emoji = "✅" if status == "free" else "❌"
    response = f"{status_emoji} Статус на {date_time_str} установлен как '{status}'"

    if status == 'busy' and events:
        response += f"\n\nОтменено участие в {len(events)} событиях на эту дату."

    bot.reply_to(message, response, reply_markup=make_keyboard())
    cursor.close()
    conn.close()

def notify_event_creator(bot, creator_id, user_fullname, event_name, date):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users WHERE id = %s", (creator_id,))
    creator_data = cursor.fetchone()
    if creator_data:
        message = f"❌ Пользователь {user_fullname} отменил участие в событии '{event_name}' ({date}), так как отметил эту дату как 'занят'"
        bot.send_message(creator_data[0], message)
    cursor.close()
    conn.close()

@bot.message_handler(func=lambda message: message.text == "📨 Мои приглашения")
def my_invitations(message):
    conn = db_connect()
    cursor = conn.cursor()
    # Получаем все неотвеченные приглашения
    cursor.execute("""
        SELECT 
            e.id,
            e.name, 
            e.date_time, 
            e.description,
            u.username as creator_username,
            ep.status,
            (
                SELECT COUNT(*) 
                FROM event_participants ep2 
                WHERE ep2.event_id = e.id 
                AND ep2.status = 'confirmed'
            ) as confirmed_participants
        FROM events e
        JOIN users u ON e.creator_id = u.id
        JOIN event_participants ep ON e.id = ep.event_id
        JOIN users u2 ON ep.user_id = u2.id
        WHERE u2.telegram_id = %s
        AND ep.status = 'pending'
        AND e.date_time > NOW()
        ORDER BY e.date_time
    """, (message.from_user.id,))

    invitations = cursor.fetchall()
    if not invitations:
        bot.reply_to(message, "У вас нет новых приглашений на события.", reply_markup=make_keyboard())
        return

    for invitation in invitations:
        event_id, name, date_time, description, creator_username, status, confirmed_participants = invitation
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_{event_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{event_id}"))

        invitation_text = f"""
📨 Приглашение на событие!

📅 Название: {name}
🕒 Дата и время: {date_time.strftime('%Y-%m-%d %H:%M')}
👥 Участников подтвердило: {confirmed_participants}
👤 Организатор: @{creator_username}
"""
        if description:
            invitation_text += f"📝 Описание: {description}\n"

        bot.send_message(message.chat.id, invitation_text, reply_markup=keyboard)
    cursor.close()
    conn.close()

if __name__ == "__main__":
    print("Бот запущен!")
    bot.infinity_polling()