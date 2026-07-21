from http.client import responses
import asyncio
from telegram import Update, CallbackQuery
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons, send_text)

import credentials
user_events = {}
chat_modes = {}
talk_characters = {
                                'talk_cobain': '1.',
                                'talk_hawking': '2.',
                                'talk_nietzsche': '3.',
                                'talk_queen' : '4.',
                                'talk_tolkien' : '5.'
                            }

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'main')
    await send_text(update, context, load_message('main'))
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓',
        'translate' : 'Перекласти текст'
        # Додати команду в меню можна так:
        # 'command': 'button text'

    })


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'random')
    prompt_random = load_prompt('random')
    response = await chat_gpt.send_question(prompt_random, 'Давай рандомний факт')
    await send_text_buttons(
        update, context,
        response,
        {
            'finish' : 'Закінчити',
            'random_one_more' :'Хочу ще факт',
            }
        )
    await update.callback_query.answer()

async def random_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == 'random_one_more':
        await random(update, context)


async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.message.from_user.id] = 'GPT_MODE'
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message('gpt'))

async def plain_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = chat_modes.get(update.message.from_user.id)
    if mode is None:
        await send_text(update, context, 'Я не розумію такої команди. Відправ команду /start для допомоги')
    elif mode == 'GPT_MODE':
        prompt_gpt = load_prompt('gpt')
        response = await chat_gpt.send_question(prompt_gpt, update.message.text)
        await send_text_buttons(update, context, response,
                            {
                                'finish': 'Закінчити'
                            })

async def talk_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_modes[user_id] = 'TALK_MODE'
    await send_image(update, context, 'talk')
    text = load_message('talk')
    await send_text_buttons(update, context, text, talk_characters)
    await update.callback_query.answer()

async def talking_process(update: Update, context: ContextTypes.DEFAULT_TYPE, person : str):
    query = update.callback_query
    prompt_talk = load_prompt(person)
    chat_modes[query.from_user.id] = f'talking_with_{person}'
    response = await chat_gpt.send_question(prompt_talk, update.callback_query.data)
    await send_image(update, context, person)
    await send_text_buttons(update, context, response, {'finish': 'Закінчити розмову'})
    await update.callback_query.answer()


async def choosing_characters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    mode = chat_modes.get(user_id)
    click_data = query.data
    if mode is None:
        await send_text(update, context, 'Я не розумію такої команди. Відправ команду /start для допомоги')
        return
    elif mode == 'TALK_MODE':
        if click_data in talk_characters:
            await talking_process(update, context, click_data)
    if query == 'talk_finish':
        await start(update, context)
        chat_modes[update.message.from_user.id] = None


async def quiz_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_modes[user_id] = 'QUIZ_MODE'
    await send_image(update, context, 'quiz')
    await send_text_buttons(update, context, load_message('quiz'), {
                                                                    'quiz_prog': 'Програмування на python',
                                                                    'quiz_math': 'Математика',
                                                                    'quiz_biology' : 'Біологія',
                                                                    'finish': 'Закінчити'
                                                                    })
    await update.callback_query.answer()

async def quiz_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt_quiz = load_prompt('quiz')
    query = update.callback_query
    quiz_score = 0
    await chat_gpt.send_question(prompt_quiz, query.data)
    answer = await chat_gpt.add_message(update.message.text)
    if answer == "Правильно!":
        quiz_score += 1
        await send_text(update, context, answer)
        await send_text_buttons(update, context, f'Кількість правильних відповідей{quiz_score}', {
                                                                    'quiz_prog': 'Програмування на python',
                                                                    'quiz_math': 'Математика',
                                                                    'quiz_biology' : 'Біологія',
                                                                    'quiz_more' : 'Попередня тема',
                                                                    'finish' : 'Закінчити'})
    else:
        await send_text(update, context, answer)
        await send_text_buttons(update, context, f'Кількість правильних відповідей{quiz_score}', {
            'quiz_prog': 'Програмування на python',
            'quiz_math': 'Математика',
            'quiz_biology': 'Біологія',
            'quiz_more': 'Попередня тема',
            'finish': 'Закінчити'})
    await update.callback_query.answer()

async def translate_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_modes[update.message.from_user.id] = 'TRANSLATION_MODE'
    await send_image(update, context, 'translate')
    await send_text_buttons(update, context, load_message('translate1'), {'translate_ukrainian': 'Українська',
                                                                                'translate_english': 'Англійська',
                                                                                'translate_german': 'Німецька',
                                                                                'translate_russian': 'Російська',
                                                                                'finish':'Закінчити'} )
    await update.callback_query.answer()


async def translate_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.answer()
    prompt_translate = load_prompt('translate')
    await chat_gpt.send_question(prompt_translate, str(query))



    await send_text(update, context, 'translate2')
    response = await chat_gpt.add_message(update.message.text)
    await send_text_buttons(update, context, response, {'finish' : 'Закінчити'})






async def finish_buttons_handler(update: Update, context : ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query == 'finish':
        await start(update, context)
        chat_modes[update.message.from_user.id] = None






chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник команди можна так:
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', gpt))
app.add_handler(CommandHandler('talk', talk_start))
app.add_handler(CommandHandler('quiz', quiz_start))
app.add_handler(CommandHandler('translate', translate_start))
app.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, plain_text_handler))

# Зареєструвати обробник колбеку можна так:
app.add_handler(CallbackQueryHandler(finish_buttons_handler, pattern='^finish.*'))
app.add_handler(CallbackQueryHandler(plain_text_handler, pattern='^gpt_.*'))
app.add_handler(CallbackQueryHandler(choosing_characters, pattern='^talk_.*'))
app.add_handler(CallbackQueryHandler(quiz_process, pattern='^quiz_.*'))
app.add_handler(CallbackQueryHandler(translate_process, pattern='^translate_.*'))

# app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
