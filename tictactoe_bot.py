import os
import random
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = "8307156776:AAEeRSzbzR2xuLQGAsWs46o45OG50nEKyfo"

games = {}

def new_board():
    return [" " for _ in range(9)]

def build_board(board):
    buttons = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            symbol = board[i + j]
            label = symbol if symbol != " " else "⬜"
            row.append(InlineKeyboardButton(label, callback_data=str(i + j)))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def check_winner(board, symbol):
    wins = [
        [0,1,2],[3,4,5],[6,7,8],
        [0,3,6],[1,4,7],[2,5,8],
        [0,4,8],[2,4,6]
    ]
    return any(all(board[i] == symbol for i in line) for line in wins)

def board_full(board):
    return all(cell != " " for cell in board)

def bot_move_easy(board):
    empty = [i for i, cell in enumerate(board) if cell == " "]
    return random.choice(empty)

def bot_move_hard(board):
    for i in range(9):
        if board[i] == " ":
            board[i] = "O"
            if check_winner(board, "O"):
                board[i] = " "
                return i
            board[i] = " "
    for i in range(9):
        if board[i] == " ":
            board[i] = "X"
            if check_winner(board, "X"):
                board[i] = " "
                return i
            board[i] = " "
    return bot_move_easy(board)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Лёгкий", callback_data="difficulty_easy")],
        [InlineKeyboardButton("Сложный", callback_data="difficulty_hard")]
    ]
    await update.message.reply_text("Выберите уровень сложности:", reply_markup=InlineKeyboardMarkup(keyboard))

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

async def handle_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    game = games.get(user_id)

    if not game:
        await query.edit_message_text("Игра не найдена. Напишите /start чтобы начать.")
        return

    index = int(query.data)
    board = game["board"]

    if board[index] != " ":
        return

    board[index] = "X"
    if check_winner(board, "X"):
        await query.edit_message_text("Вы победили! 🎉", reply_markup=build_board(board))
        games.pop(user_id)
        return

    if board_full(board):
        await query.edit_message_text("Ничья 🤝", reply_markup=build_board(board))
        games.pop(user_id)
        return

    if game["difficulty"] == "easy":
        move = bot_move_easy(board)
    else:
        move = bot_move_hard(board)

    board[move] = "O"
    if check_winner(board, "O"):
        await query.edit_message_text("Бот победил 😢", reply_markup=build_board(board))
        games.pop(user_id)
        return

    if board_full(board):
        await query.edit_message_text("Ничья 🤝", reply_markup=build_board(board))
        games.pop(user_id)
        return

    await query.edit_message_reply_markup(reply_markup=build_board(board))

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_difficulty, pattern="^difficulty_"))
    app.add_handler(CallbackQueryHandler(handle_move, pattern="^[0-8]$"))
    app.run_polling()
