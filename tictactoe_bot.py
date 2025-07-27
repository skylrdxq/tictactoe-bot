from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Хранилище всех игр и настроек
player_settings = {}  # user_id -> {"board": [...], "difficulty": "easy"/"hard"}

# Создание пустого поля
def new_board():
    return [" " for _ in range(9)]

# Проверка победителя
def check_winner(board):
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    for a, b, c in wins:
        if board[a] == board[b] == board[c] and board[a] != " ":
            return board[a]
    if " " not in board:
        return "Ничья"
    return None

# Генерация кнопок
def get_keyboard(board):
    keyboard = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i + j
            text = board[idx] if board[idx] != " " else "⬜"
            row.append(InlineKeyboardButton(text, callback_data=str(idx)))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# Умный бот
def bot_move_smart(board):
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]

    # 1. Победить, если есть возможность
    for a, b, c in wins:
        line = [board[a], board[b], board[c]]
        if line.count("⭕") == 2 and line.count(" ") == 1:
            board[[a, b, c][line.index(" ")]] = "⭕"
            return

    # 2. Блокировать игрока
    for a, b, c in wins:
        line = [board[a], board[b], board[c]]
        if line.count("❌") == 2 and line.count(" ") == 1:
            board[[a, b, c][line.index(" ")]] = "⭕"
            return

    # 3. Центр
    if board[4] == " ":
        board[4] = "⭕"
        return

    # 4. Углы
    for i in [0, 2, 6, 8]:
        if board[i] == " ":
            board[i] = "⭕"
            return

    # 5. Любая свободная
    for i in range(9):
        if board[i] == " ":
            board[i] = "⭕"
            return

# Старт — выбор сложности
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("😎 Легко", callback_data="set_difficulty_easy")],
        [InlineKeyboardButton("🧠 Сложно", callback_data="set_difficulty_hard")]
    ]
    await update.message.reply_text("Выбери уровень сложности:", reply_markup=InlineKeyboardMarkup(keyboard))

# Установка сложности и начало игры
async def set_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    difficulty = "easy" if "easy" in query.data else "hard"
    player_settings[user_id] = {
        "board": new_board(),
        "difficulty": difficulty
    }

    await query.edit_message_text(
        f"Игра началась! Ты выбрал уровень: {'Легко' if difficulty == 'easy' else 'Сложно'}\nТы играешь за ❌",
        reply_markup=get_keyboard(player_settings[user_id]["board"])
    )

# Обработка нажатий на клетки
async def handle_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    game = player_settings.get(user_id)
    if not game:
        await query.edit_message_text("Сначала начни игру командой /start.")
        return

    board = game["board"]
    difficulty = game["difficulty"]
    idx = int(query.data)

    if board[idx] != " ":
        return

    board[idx] = "❌"
    winner = check_winner(board)
    if winner:
        await query.edit_message_text(f"Победитель: {winner}", reply_markup=None)
        player_settings.pop(user_id)
        return

    # Ход бота
    if difficulty == "easy":
        for i in range(9):
            if board[i] == " ":
                board[i] = "⭕"
                break
    else:
        bot_move_smart(board)

    winner = check_winner(board)
    if winner:
        await query.edit_message_text(f"Победитель: {winner}", reply_markup=None)
        player_settings.pop(user_id)
    else:
        await query.edit_message_reply_markup(reply_markup=get_keyboard(board))

# Точка входа
if __name__ == '__main__':
    TOKEN = "8307156776:AAEeRSzbzR2xuLQGAsWs46o45OG50nEKyfo"  # 👈 Вставь сюда токен от @BotFather

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_difficulty, pattern="set_difficulty_.*"))
    app.add_handler(CallbackQueryHandler(handle_click, pattern="^[0-8]$"))

    print("Бот запущен...")
    app.run_polling()