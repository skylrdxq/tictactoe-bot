import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = "8307156776:AAEeRSzbzR2xuLQGAsWs46o45OG50nEKyfo"

games = {}

def new_board():
    return [" " for _ in range(9)]

def build_board(board):
    buttons = []
    for i in range(0, 9, 3):
        row = [
            InlineKeyboardButton(text=board[i + j] if board[i + j] != " " else str(i + j),
                                 callback_data=str(i + j))
            for j in range(3)
        ]
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def check_winner(board, symbol):
    win_combos = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # строки
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # столбцы
        [0, 4, 8], [2, 4, 6]              # диагонали
    ]
    return any(all(board[i] == symbol for i in combo) for combo in win_combos)

def board_full(board):
    return all(cell != " " for cell in board)

def bot_move_easy(board):
    empty = [i for i, cell in enumerate(board) if cell == " "]
    return random.choice(empty)

def bot_move_hard(board):
    def minimax(board, is_maximizing):
        if check_winner(board, "O"):
            return 1
        if check_winner(board, "X"):
            return -1
        if board_full(board):
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

    best_move = None
    best_score = -float("inf")
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
            InlineKeyboardButton("Лёгкий", callback_data="set_difficulty_easy"),
            InlineKeyboardButton("Сложный", callback_data="set_difficulty_hard"),
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
        text=f"Вы играете против бота ({'лёгкий' if difficulty == 'easy' else 'сложный'} уровень).\nВы ходите первым (❌).",
        reply_markup=build_board(games[user_id]["board"])
    )

async def handle_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in games:
        await query.answer("Сначала напишите /start.")
        return

    game = games[user_id]
    board = game["board"]
    difficulty = game["difficulty"]
    index = int(query.data)

    if board[index] != " ":
        await query.answer("Клетка уже занята!")
        return

    board[index] = "X"

    if check_winner(board, "X"):
        await query.edit_message_text("Вы победили! 🎉")
        del games[user_id]
        return

    if board_full(board):
        await query.edit_message_text("Ничья! 🤝")
        del games[user_id]
        return

    bot_index = bot_move_easy(board) if difficulty == "easy" else bot_move_hard(board)
    board[bot_index] = "O"

    if check_winner(board, "O"):
        await query.edit_message_text("Бот победил! 🤖")
        del games[user_id]
        return

    if board_full(board):
        await query.edit_message_text("Ничья! 🤝")
        del games[user_id]
        return

    await query.edit_message_text("Ваш ход (❌):", reply_markup=build_board(board))

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_difficulty, pattern="set_difficulty_.*"))
    app.add_handler(CallbackQueryHandler(handle_click, pattern="^[0-8]$"))

    print("Бот запущен...")
    app.run_polling()
