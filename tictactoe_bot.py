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

# 🔐 ВСТРОЕННЫЙ ТОКЕН (только для локального запуска!)
TOKEN = "8307156776:AAEeRSzbzR2xuLQGAsWs46o45OG50nEKyfo"

games = {}

def new_board():
    return [" "] * 9

def build_board(board):
    keyboard = []
    for i in range(0, 9, 3):
        row = [
            InlineKeyboardButton(board[j] if board[j] != " " else "⬜", callback_data=str(j))
            for j in range(i, i + 3)
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def check_win(board, player):
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    return any(all(board[i] == player for i in line) for line in wins)

def is_draw(board):
    return all(cell != " " for cell in board)

def bot_move_easy(board):
    empty = [i for i, cell in enumerate(board) if cell == " "]
    return random.choice(empty)

def minimax(board, is_maximizing):
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Лёгкий 🤖", callback_data="set_difficulty_easy"),
            InlineKeyboardButton("Сложный 🧠", callback_data="set_difficulty_hard"),
        ]
    ]
    await update.message.reply_text("Выбери уровень сложности:", reply_markup=InlineKeyboardMarkup(keyboard))

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
        f"Вы играете против бота ({'лёгкий' if difficulty == 'easy' else 'сложный'} уровень
