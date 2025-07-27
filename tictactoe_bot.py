import os
import random
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Словарь для хранения состояния игр
games = {}

# Получение токена из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")

# Создание пустого поля
def new_board():
    return [" "] * 9

# Отображение поля кнопками
def build_board(board):
    keyboard = []
    for i in range(0, 9, 3):
        row = [
            InlineKeyboardButton(board[j] if board[j] != " " else "⬜", callback_data=str(j))
            for j in range(i, i + 3)
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# Проверка победы
def check_win(board, player):
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # ряды
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # колонки
        [0, 4, 8], [2, 4, 6]              # диагонали
    ]
    return any(all(board[i] == player for i in line) for line in wins)

# Проверка ничьи
def is_draw(board):
    return all(cell != " " for cell in board)

# Ход бота — лёгкий уровень
def bot_move_easy(board):
    empty = [i for i, cell in enumerate(board) if cell == " "]
    return random.choice(empty)

# Ход бота — сложный уровень (минимакс)
def minimax(board, is_maximizing):
    winner = None
    if check_win(board, "O"):
        return 1
    elif check_win(board, "X"):
        return -1
    elif is_draw(board):
        return 0

    if is_maximizing:
        best_score = -float("inf")
        for i in range(9):
            if board[i] == " ":
                board[i] = "O"
                score = minimax(board, False)
                board[i] = " "
                best_score = max(score, best_score)
        return best_score
    else:
        best_score = float("inf")
        for i in range(9):
            if board[i] == " ":
                board[i] = "X"
                score = minimax(board, True)
                board[i] = " "
                best_score = min(score, best_score)
        return best_score

def bot_move_hard(board):
    best_score = -float("inf")
    best_move = None
    for i in range(9):
        if board[i] == " ":
            board[i] = "O"
            score = minimax(board, False)
            board[i] = " "
            if score > best_score:
                best_score = score
                best_move = i
    return best_move

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Лёгкий 🤖", callback_data="set_difficulty_easy"),
            InlineKeyboardButton("Сложный 🧠", callback_data="set_difficulty_hard"),
        ]
    ]
    await update.message.reply_text("Выбери уровень сложности:", reply_markup=InlineKeyboardMarkup(keyboard))

# Обработка выбора сложности
async def set_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    difficulty = query.data.split("_")[-1]
    user_id = query.from_user.id

    games[user_id] = {
        "board": new_board(),
        "difficulty": difficulty,
        "turn": "X"
    }

    await query.edit_message_text(
        f"Вы играете против бота ({'лёгкий' if difficulty == 'easy' else 'сложный'} уровень).\nВы ходите первым (❌).",
        reply_markup=build_board(games[user_id]["board"])
    )

# Обработка кликов по кнопкам поля
async def handle_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in games:
        await query.edit_message_text("Сначала начните игру: /start")
        return

    game = games[user_id]
    board = game["board"]
    pos = int(query.data)

    if board[pos] != " ":
        return  # игнор хода по занятой клетке

    board[pos] = "X"

    if check_win(board, "X"):
        await query.edit_message_text("Вы победили! 🎉", reply_markup=build_board(board))
        del games[user_id]
        return
    elif is_draw(board):
        await query.edit_message_text("Ничья 🤝", reply_markup=build_board(board))
        del games[user_id]
        return

    # Ход бота
    bot_pos = (
        bot_move_easy(board) if game["difficulty"] == "easy"
        else bot_move_hard(board)
    )
    board[bot_pos] = "O"

    if check_win(board, "O"):
        await query.edit_message_text("Бот победил! 🤖", reply_markup=build_board(board))
        del games[user_id]
    elif is_draw(board):
        await query.edit_message_text("Ничья 🤝", reply_markup=build_board(board))
        del games[user_id]
    else:
        await query.edit_message_text("Ваш ход:", reply_markup=build_board(board))

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_difficulty, pattern="^set_difficulty_"))
    app.add_handler(CallbackQueryHandler(handle_click, pattern="^[0-8]$"))

    print("Бот запущен...")
    app.run_polling()
