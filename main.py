import csv
import os
import logging

import aiogram.utils.exceptions
from aiogram import Bot, types
# Память для машины состояний и машина состояний
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
# Машина состояний импорты
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import calendar
import datetime

import db

# Хранение памяти для машины состояний
storage = MemoryStorage()


class MenuStates(StatesGroup):
    start = State()
    expense = State()
    expense_comment = State()
    expense_approve_enter_file = State()
    expense_enter_file = State()
    income = State()
    income_comment = State()
    income_approve_enter_file = State()
    income_enter_file = State()
    fraction_enter = State()
    fraction_pay = State()
    fraction_choose_who = State()
    fraction_enter_sum = State()
    fraction_to_pay = State()
    fraction_to_who = State()
    report = State()
    choose_period = State()
    choose_second_period = State()
    send_report = State()


def generate_prev_month_button(year, month):
    # Вычисляем предыдущий месяц
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    # Создаем кнопку для переключения на предыдущий месяц
    button = InlineKeyboardButton("<", callback_data=f"calendar-month-{prev_year}-{prev_month}")
    return button


def generate_next_month_button(year, month):
    # Вычисляем следующий месяц
    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1
    # Создаем кнопку для переключения на следующий месяц
    button = InlineKeyboardButton(">", callback_data=f"calendar-month-{next_year}-{next_month}")
    return button


def generate_calendar(year, month):
    # Создаем кнопки для календаря
    keyboard = InlineKeyboardMarkup(row_width=7)
    keyboard.add(InlineKeyboardButton(f"{calendar.month_name[month]} {year}", callback_data="ignore"))
    # Получаем первый день месяца
    first_day = datetime.date(year, month, 1)
    # Получаем день недели первого дня месяца (0 - понедельник, 6 - воскресенье)
    first_weekday = first_day.weekday()
    # Получаем количество дней в месяце
    _, days_in_month = calendar.monthrange(year, month)
    # Создаем кнопки для дней месяца
    days_of_week = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    row = []
    for day in days_of_week:
        row.append(types.InlineKeyboardButton(text=day, callback_data=f"ignore"))
    keyboard.row(*row)
    day = 1
    for i in range(6):
        row = []
        for j in range(7):
            if i == 0 and j < first_weekday:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            elif day > days_in_month:
                break
            else:
                row.append(InlineKeyboardButton(str(day),
                                                callback_data="calendar-day-" + str(day) + '-' + str(month) + '-' + str(
                                                    year)))
                day += 1
        keyboard.row(*row)
    # Создаем кнопки для переключения месяца
    prev_month_button = generate_prev_month_button(year, month)
    next_month_button = generate_next_month_button(year, month)
    keyboard.row(
        prev_month_button,
        next_month_button
    )
    return keyboard


def gen_markup(texts: int, prefix: str, row_width: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=row_width)
    for num in range(texts):
        markup.insert(InlineKeyboardButton(f"{prefix} {num + 1}", callback_data=f"{prefix} {num + 1}"))
    return markup


logging.basicConfig(level=logging.INFO)

# Создаём бота исходя из полученного токена
bot = Bot(token="6395802297:AAGSL6IBKgTVN8dPRHNVjUzLHuLCHy_y5lM")
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(
    KeyboardButton(text="Расход"), KeyboardButton(text="Доход"), KeyboardButton(text="Доли"),
    KeyboardButton(text="Отчёт"))

fraction_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(
    KeyboardButton(text="Выплатить"), KeyboardButton(text="К выплате")).add(KeyboardButton(text="Назад"))

fraction_choose_who_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(
    KeyboardButton(text="Миша"), KeyboardButton(text="Дато"), KeyboardButton(text="Глеб")).add(
    KeyboardButton(text="Назад"))

choose_period_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(
    KeyboardButton(text="Текущий месяц"), KeyboardButton(text="Период")).add(KeyboardButton(text="Назад"))

back_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton(text="Назад"))

back_n_next_button = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(
    KeyboardButton(text="Далее"), KeyboardButton(text="Назад"))

pay_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(
    KeyboardButton(text="Меню"), KeyboardButton(text="Назад"))

yes_or_no_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(
    KeyboardButton(text="Да"), KeyboardButton(text="Нет")).add(KeyboardButton("Назад"))


# Обработка команды /start
@dp.message_handler(commands='start', state='*')
async def command_start(message: types.Message, state: FSMContext):
    await state.finish()

    await db.user_exists(message.from_user.id, message.from_user.username)

    await bot.send_message(message.from_user.id, "Салам, брат! Речь пойдет о трехзначных цифрах 💷💷💷",
                           reply_markup=main_menu_keyboard)
    await MenuStates.start.set()


@dp.message_handler(state=MenuStates.start)
async def menu_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Расход":
            await bot.send_message(message.from_user.id, "Сколько потратили?", reply_markup=back_keyboard)
            await MenuStates.expense.set()

        case "Доход":
            await bot.send_message(message.from_user.id, "Слава Всевышнему! Сколько подняли?",
                                   reply_markup=back_keyboard)
            await MenuStates.income.set()

        case "Доли":
            await bot.send_message(message.from_user.id, "Выплатить: отчитаться о выплате доли себе или брату.\n"
                                                         "К выплате: посмотреть, сколько на сегодня должны выплатить"
                                                         " тебе или брату.", reply_markup=fraction_keyboard)
            await MenuStates.fraction_enter.set()

        case "Отчёт":
            await bot.send_message(message.from_user.id, "Выберите период", reply_markup=choose_period_keyboard)
            await MenuStates.report.set()

        case _:
            await bot.send_message(message.from_user.id, "Извини, брат, но тут надо пункты выбирать")


@dp.message_handler(state=MenuStates.expense)
async def expense_sum_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "И снова здравствуйте", reply_markup=main_menu_keyboard)
            await MenuStates.start.set()

        case _:
            try:
                int(message.text)
                async with state.proxy() as data:
                    data["expense"] = message.text

                await bot.send_message(message.from_user.id, "На что мы потратили столько денег, брат?"
                                                             " Поясни в двух словах.", reply_markup=back_keyboard)

                await MenuStates.expense_comment.set()

            except ValueError:
                await bot.send_message(message.from_user.id, "Напиши цифрами, без букв, знаков и пробелов",
                                       reply_markup=back_keyboard)

            except Exception as e:
                print(f"Ошибка в expense_sum_handle {e}")


@dp.message_handler(content_types=types.ContentTypes.TEXT, state=MenuStates.expense_comment)
async def handle_text(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "Сколько потратили?", reply_markup=back_keyboard)
            await MenuStates.expense.set()

        case _:
            async with state.proxy() as data:
                if "comment" not in data:
                    data["comment"] = message.text
            await bot.send_message(message.from_user.id, "Есть чеки или другое подтверждение?",
                                   reply_markup=yes_or_no_keyboard)
            await MenuStates.expense_approve_enter_file.set()


@dp.message_handler(content_types=types.ContentTypes.TEXT, state=MenuStates.expense_approve_enter_file)
async def handle_approve_photos(message: types.Message, state: FSMContext):
    match message.text:
        case "Да":
            await bot.send_message(message.from_user.id, "Присылай всё, что есть", reply_markup=back_keyboard)
            await MenuStates.expense_enter_file.set()

        case "Нет":
            await bot.send_message(message.from_user.id, "Понял-принял", reply_markup=main_menu_keyboard)

            async with state.proxy() as data:
                expense = data["expense"]
                comment = data["comment"]

            await db.insert_users_finances(message.from_user.id, "Расход", expense, comment)

            with open(f"{message.from_user.username}_расход.csv", mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Имя', 'Тип', 'Сумма', 'Комментарий'])

                writer.writerow([message.from_user.username, "Расход", f'{expense} руб.', comment])

            await bot.send_message(message.from_user.id, f"#расход\n"
                                                         f"@{message.from_user.username} {expense} руб. {comment}")

            # await bot.send_document(message.from_user.id, open(f"{message.from_user.username}_расход.csv", "rb"),
            #                         caption="#расход")

            # Очистка состояния
            await state.reset_state()

            await MenuStates.start.set()

        case "Назад":
            await bot.send_message(message.from_user.id, "На что мы потратили столько денег, брат?"
                                                         " Поясни в двух словах.", reply_markup=back_keyboard)

            await MenuStates.expense_comment.set()

        case _:
            await bot.send_message(message.from_user.id, "Брат, тут надо пункты выбирать",
                                   reply_markup=yes_or_no_keyboard)


@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=MenuStates.expense_enter_file)
async def handle_photos(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "photos" not in data:
            data["photos"] = []

        # Добавление фотографий в список
        data["photos"].append(message.photo[-1].file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Это всё?", reply_markup=yes_or_no_keyboard)


@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state=MenuStates.expense_enter_file)
async def handle_docs(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "documents" not in data:
            data["documents"] = []

        # Добавление фотографий в список
        data["documents"].append(message.document.file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Это всё?", reply_markup=yes_or_no_keyboard)


@dp.message_handler(content_types=types.ContentTypes.VIDEO, state=MenuStates.expense_enter_file)
async def handle_docs(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "video" not in data:
            data["video"] = []

        # Добавление фотографий в список
        data["video"].append(message.photo[-1].file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Это всё?", reply_markup=yes_or_no_keyboard)


# Функция обрабатывающая кнопку назад, если пользователь выбрал отправить фотографию
@dp.message_handler(content_types=types.ContentTypes.TEXT, state=MenuStates.expense_enter_file)
async def choose_will_be_photo(message: types.Message, state: FSMContext):
    if 'Назад' in message.text:
        await bot.send_message(message.from_user.id, "Так сколько потратили, брат?",
                               reply_markup=back_keyboard)
        await MenuStates.expense.set()

    elif "Да" in message.text:
        # Получение списка сохраненных фотографий из состояния
        async with state.proxy() as data:
            try:
                photos = data["photos"]

                photos_for_save = []

                os.makedirs('photos', exist_ok=True)

                # Обработка сохраненных фотографий
                for photo_id in photos:
                    try:
                        file_info = await bot.get_file(photo_id)

                    except aiogram.utils.exceptions.FileIsTooBig:
                        await message.reply("Брат, ты мне слишком большую фотографию отправил")

                    file_path = file_info.file_path

                    # Сохранение фотографии локально
                    await bot.download_file(file_path, f'photos/{photo_id}.jpg')
                    photos_for_save.append(f'photos/{photo_id}.jpg')

                expense = data["expense"]
                comment = data["comment"]

                await db.insert_users_finances(message.from_user.id, "Расход", expense, comment, photos_for_save)

                with open(f"{message.from_user.username}_расход.csv", mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Имя', 'Тип', 'Сумма', 'Комментарий'])

                    writer.writerow([message.from_user.username, "Расход", f'{expense} руб.', comment])

                media = types.MediaGroup()

                for path in photos_for_save:
                    if photos_for_save.index(path) == 0:
                        media.attach_photo(types.InputMediaPhoto(open(path, 'rb'),
                                                                 caption=f"#расход\n"
                                                                         f"@{message.from_user.username} {expense} руб."
                                                                         f" {comment}"))
                    else:
                        media.attach_photo(types.InputMediaPhoto(open(path, 'rb')))
                await bot.send_media_group(chat_id=message.from_user.id, media=media)

                # await bot.send_document(message.from_user.id, open(f"{message.from_user.username}_расход.csv", "rb"),
                #                         caption="#расход")

            except KeyError:
                pass

            try:
                documents = data["documents"]

                documents_for_save = []

                os.makedirs('documents', exist_ok=True)

                # Обработка сохраненных документов
                for docs_id in documents:
                    try:
                        file_info = await bot.get_file(docs_id)

                    except aiogram.utils.exceptions.FileIsTooBig:
                        await message.reply("Брат, слишком большой файл ты мне отправил")

                    file_path = file_info.file_path

                    # Сохранение фотографии локально
                    await bot.download_file(file_path, f'documents/{docs_id}.pdf')
                    documents_for_save.append(f'documents/{docs_id}.pdf')

                expense = data["expense"]
                comment = data["comment"]

                await db.insert_users_finances(message.from_user.id, "Расход", expense, comment, documents_for_save)

                with open(f"{message.from_user.username}_расход.csv", mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Имя', 'Тип', 'Сумма', 'Комментарий'])

                    writer.writerow([message.from_user.username, "Расход", f'{expense} руб.', comment])

                media = types.MediaGroup()

                for path in documents_for_save:
                    if documents_for_save.index(path) == 0:
                        media.attach_photo(types.InputMediaDocument(open(path, 'rb'),
                                                                 caption=f"#расход\n"
                                                                         f"@{message.from_user.username} {expense} руб."
                                                                         f" {comment}"))
                    else:
                        media.attach_photo(types.InputMediaDocument(open(path, 'rb')))
                await bot.send_media_group(chat_id=message.from_user.id, media=media)

                # await bot.send_document(message.from_user.id, open(f"{message.from_user.username}_расход.csv", "rb"),
                #                         caption="#расход")

            except KeyError:
                pass

            try:
                video = data["video"]

                video_for_save = []

                os.makedirs('video', exist_ok=True)

                # Обработка сохраненных видео
                for video_id in video:
                    try:
                        file_info = await bot.get_file(video_id)

                    except aiogram.utils.exceptions.FileIsTooBig:
                        await message.reply("Брат, слишком большой видос ты мне отправил")

                    file_path = file_info.file_path

                    # Сохранение фотографии локально
                    await bot.download_file(file_path, f'video/{video_id}.mp4')
                    video_for_save.append(f'video/{video_id}.mp4')

                expense = data["expense"]
                comment = data["comment"]

                await db.insert_users_finances(message.from_user.id, "Расход", expense, comment, video_for_save)

                with open(f"{message.from_user.username}_расход.csv", mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Имя', 'Тип', 'Сумма', 'Комментарий'])

                    writer.writerow([message.from_user.username, "Расход", f'{expense} руб.', comment])

                media = types.MediaGroup()

                for path in video_for_save:
                    if video_for_save.index(path) == 0:
                        media.attach_photo(types.InputMediaVideo(open(path, 'rb'),
                                                                 caption=f"#расход\n"
                                                                         f"@{message.from_user.username} {expense} руб."
                                                                         f" {comment}"))
                    else:
                        media.attach_photo(types.InputMediaVideo(open(path, 'rb')))
                await bot.send_media_group(chat_id=message.from_user.id, media=media)

                # await bot.send_document(message.from_user.id, open(f"{message.from_user.username}_расход.csv", "rb"),
                #                         caption="#расход")

            except KeyError:
                pass

        # Очистка состояния
        await state.reset_state()

        # Ответное сообщение об успешной обработке
        await message.reply("Понял-принял", reply_markup=main_menu_keyboard)
        await MenuStates.start.set()

    elif "Нет" in message.text:
        await bot.send_message(message.from_user.id, "Присылай всё, что есть", reply_markup=back_keyboard)

    else:
        await bot.send_message(message.from_user.id, "Брат, отправь мне видео, фото, документ или нажми на кнопку",
                               reply_markup=back_keyboard)


# Функция обрабатывающая кнопку назад, если пользователь выбрал отправить фотографию
@dp.message_handler(content_types=types.ContentTypes.ANY, state=MenuStates.expense_enter_file)
async def choose_will_be_photo(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, "Брат, я тебя не понимаю, отправь фото, видео или документ",
                           reply_markup=back_keyboard)


@dp.message_handler(state=MenuStates.income)
async def income_sum_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "И снова здравствуйте", reply_markup=main_menu_keyboard)
            await MenuStates.start.set()

        case _:
            try:
                int(message.text)
                async with state.proxy() as data:
                    data["income"] = message.text
                await bot.send_message(message.from_user.id, "На чем подняли такую котлету?"
                                                             " Поясни пацанам по-братски.", reply_markup=back_keyboard)
                await MenuStates.income_comment.set()

            except ValueError:
                await bot.send_message(message.from_user.id, "Напиши цифрами, без букв, знаков и пробелов",
                                       reply_markup=back_keyboard)

            except Exception as e:
                print(f"Ошибка в income_sum_handle {e}")


@dp.message_handler(content_types=types.ContentTypes.TEXT, state=MenuStates.income_comment)
async def handle_text(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "Слава Всевышнему! Сколько подняли?",
                                   reply_markup=back_keyboard)
            await MenuStates.income.set()

        case _:
            async with state.proxy() as data:
                data["comment"] = message.text
            await bot.send_message(message.from_user.id, "Есть заказ-наряд или другое подтверждение?",
                                   reply_markup=yes_or_no_keyboard)
            await MenuStates.income_approve_enter_file.set()


@dp.message_handler(content_types=types.ContentTypes.TEXT, state=MenuStates.income_approve_enter_file)
async def handle_approve_photos(message: types.Message, state: FSMContext):
    match message.text:
        case "Да":
            await bot.send_message(message.from_user.id, "Присылай всё, что есть", reply_markup=back_keyboard)
            await MenuStates.income_enter_file.set()

        case "Нет":
            await bot.send_message(message.from_user.id, "Понял-принял", reply_markup=main_menu_keyboard)
            async with state.proxy() as data:
                income = data["income"]
                comment = data["comment"]

            await db.insert_users_finances(message.from_user.id, "Доход", income, comment)

            with open(f"{message.from_user.username}_доход.csv", mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Имя', 'Тип', 'Сумма', 'Комментарий'])

                writer.writerow([message.from_user.username, "Доход", f'{income} руб.', comment])

            # await bot.send_document(message.from_user.id, open(f"{message.from_user.username}_доход.csv", "rb"),
            #                         caption="#доход")
            await bot.send_message(message.from_user.id, f"#доход\n"
                                                         f"@{message.from_user.username} {income} руб. {comment}")

            # Очистка состояния
            await state.reset_state()
            await MenuStates.start.set()

        case "Назад":
            await bot.send_message(message.from_user.id, "На чем подняли такую котлету? Поясни пацанам по-братски.",
                                   reply_markup=back_keyboard)

            await MenuStates.income_comment.set()

        case _:
            await bot.send_message(message.from_user.id, "Брат, тут надо пункты выбирать",
                                   reply_markup=yes_or_no_keyboard)


@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=MenuStates.income_enter_file)
async def handle_photos(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "photos" not in data:
            data["photos"] = []

        # Добавление фотографий в список
        data["photos"].append(message.photo[-1].file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Это всё?", reply_markup=yes_or_no_keyboard)


@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state=MenuStates.income_enter_file)
async def handle_docs(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "documents" not in data:
            data["documents"] = []

        # Добавление фотографий в список
        data["documents"].append(message.document.file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Это всё?", reply_markup=yes_or_no_keyboard)


@dp.message_handler(content_types=types.ContentTypes.VIDEO, state=MenuStates.income_enter_file)
async def handle_docs(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "video" not in data:
            data["video"] = []

        # Добавление фотографий в список
        data["video"].append(message.photo[-1].file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Это всё?", reply_markup=yes_or_no_keyboard)


# Функция обрабатывающая кнопку назад, если пользователь выбрал отправить фотографию
@dp.message_handler(content_types=types.ContentTypes.TEXT, state=MenuStates.income_enter_file)
async def choose_will_be_photo(message: types.Message, state: FSMContext):
    if 'Назад' in message.text:
        await bot.send_message(message.from_user.id, "Так сколько подняли бабла, брат?",
                               reply_markup=back_keyboard)
        await MenuStates.income.set()

    elif "Да" in message.text:
        # Получение списка сохраненных фотографий из состояния
        async with state.proxy() as data:
            try:
                photos = data["photos"]

                photos_for_save = []

                os.makedirs('photos', exist_ok=True)

                # Обработка сохраненных фотографий
                for photo_id in photos:
                    file_info = await bot.get_file(photo_id)
                    file_path = file_info.file_path

                    # Сохранение фотографии локально
                    await bot.download_file(file_path, f'photos/{photo_id}.jpg')
                    photos_for_save.append(f'photos/{photo_id}.jpg')

                income = data["income"]
                comment = data["comment"]

                await db.insert_users_finances(message.from_user.id, "Доход", income, comment, photos_for_save)
                with open(f"{message.from_user.username}_доход.csv", mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Имя', 'Тип', 'Сумма', 'Комментарий'])

                    writer.writerow([message.from_user.username, "Доход", f'{income} руб.', comment])

                # await bot.send_document(message.from_user.id, open(f"{message.from_user.username}_доход.csv", "rb"),
                #                         caption="#доход")
                media = types.MediaGroup()

                for path in photos_for_save:
                    if photos_for_save.index(path) == 0:
                        media.attach_photo(types.InputMediaPhoto(open(path, 'rb'),
                                                                 caption=f"#доход\n"
                                                                         f"@{message.from_user.username} {income} руб."
                                                                         f" {comment}"))
                    else:
                        media.attach_photo(types.InputMediaPhoto(open(path, 'rb')))
                await bot.send_media_group(chat_id=message.from_user.id, media=media)

            except KeyError:
                pass

            try:
                documents = data["documents"]

                documents_for_save = []

                os.makedirs('documents', exist_ok=True)

                # Обработка сохраненных документов
                for docs_id in documents:
                    try:
                        file_info = await bot.get_file(docs_id)

                    except aiogram.utils.exceptions.FileIsTooBig:
                        await message.reply("Брат, слишком большой файл ты мне отправил")

                    file_path = file_info.file_path

                    # Сохранение фотографии локально
                    await bot.download_file(file_path, f'documents/{docs_id}.pdf')
                    documents_for_save.append(f'documents/{docs_id}.pdf')

                income = data["income"]
                comment = data["comment"]

                await db.insert_users_finances(message.from_user.id, "Доход", income, comment, documents_for_save)

                with open(f"{message.from_user.username}_доход.csv", mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Имя', 'Тип', 'Сумма', 'Комментарий'])

                    writer.writerow([message.from_user.username, "Доход", f'{income} руб.', comment])

                media = types.MediaGroup()

                for path in photos_for_save:
                    if photos_for_save.index(path) == 0:
                        media.attach_photo(types.InputMediaDocument(open(path, 'rb'),
                                                                 caption=f"#доход\n"
                                                                         f"@{message.from_user.username} {income} руб."
                                                                         f" {comment}"))
                    else:
                        media.attach_photo(types.InputMediaDocument(open(path, 'rb')))
                await bot.send_media_group(chat_id=message.from_user.id, media=media)
                # await bot.send_document(message.from_user.id, open(f"{message.from_user.username}_доход.csv", "rb"),
                #                         caption="#доход")

            except KeyError:
                pass

            try:
                video = data["video"]

                video_for_save = []

                os.makedirs('video', exist_ok=True)

                # Обработка сохраненных видео
                for video_id in video:
                    file_info = await bot.get_file(video_id)
                    file_path = file_info.file_path

                    # Сохранение фотографии локально
                    await bot.download_file(file_path, f'video/{video_id}.mp4')
                    video_for_save.append(f'video/{video_id}.mp4')

                income = data["income"]
                comment = data["comment"]

                await db.insert_users_finances(message.from_user.id, "Доход", income, comment, video_for_save)

                with open(f"{message.from_user.username}_доход.csv", mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Имя', 'Тип', 'Сумма', 'Комментарий'])

                    writer.writerow([message.from_user.username, "Доход", f'{income} руб.', comment])

                media = types.MediaGroup()

                for path in photos_for_save:
                    if photos_for_save.index(path) == 0:
                        media.attach_photo(types.InputMediaVideo(open(path, 'rb'),
                                                                 caption=f"#доход\n"
                                                                         f"@{message.from_user.username} {income} руб."
                                                                         f" {comment}"))
                    else:
                        media.attach_photo(types.InputMediaVideo(open(path, 'rb')))
                await bot.send_media_group(chat_id=message.from_user.id, media=media)

                # await bot.send_document(message.from_user.id, open(f"{message.from_user.username}_доход.csv", "rb"),
                #                         caption="#доход")

            except KeyError:
                pass

        # Очистка состояния
        await state.reset_state()

        # Ответное сообщение об успешной обработке
        await message.reply("Понял-принял", reply_markup=main_menu_keyboard)
        await MenuStates.start.set()

    elif "Нет" in message.text:
        await bot.send_message(message.from_user.id, "Присылай всё, что есть", reply_markup=back_keyboard)

    else:
        await bot.send_message(message.from_user.id, "Брат, отправь мне видео, фото, документ или нажми на кнопку",
                               reply_markup=back_keyboard)


# Функция обрабатывающая кнопку назад, если пользователь выбрал отправить фотографию
@dp.message_handler(content_types=types.ContentTypes.ANY, state=MenuStates.income_enter_file)
async def choose_will_be_photo(message: types.Message, state: FSMContext):
    await bot.send_message(message.from_user.id, "Брат, я тебя не понимаю, отправь фото, видео или документ",
                           reply_markup=back_keyboard)


@dp.message_handler(state=MenuStates.fraction_enter)
async def fraction_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "И снова здравствуйте", reply_markup=main_menu_keyboard)
            await MenuStates.start.set()

        case "Выплатить":
            await bot.send_message(message.from_user.id, "Кому выплачиваем долю?",
                                   reply_markup=fraction_choose_who_keyboard)
            await MenuStates.fraction_choose_who.set()

        case "К выплате":
            await bot.send_message(message.from_user.id, "Кому?", reply_markup=fraction_choose_who_keyboard)
            await MenuStates.fraction_to_who.set()

        case _:
            await bot.send_message(message.from_user.id, "Извини, брат, но тут надо пункты выбирать",
                                   reply_markup=fraction_keyboard)


@dp.message_handler(state=MenuStates.fraction_choose_who)
async def fraction_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "Так выплачиваем или хотим поинтересоваться?",
                                   reply_markup=fraction_keyboard)
            await MenuStates.fraction_enter.set()

        case "Миша" | "Дато" | "Глеб":
            async with state.proxy() as data:
                data["to_who"] = message.text
            await bot.send_message(message.from_user.id, "Сколько выплатили?", reply_markup=back_keyboard)
            await MenuStates.fraction_pay.set()

        case _:
            await bot.send_message(message.from_user.id, "Извини, брат, но тут надо пункты выбирать",
                                   reply_markup=fraction_choose_who_keyboard)


@dp.message_handler(state=MenuStates.fraction_pay)
async def fraction_pay_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "Выплатить: отчитаться о выплате доли себе или брату.\n"
                                                         "К выплате: посмотреть, сколько на сегодня должны выплатить"
                                                         " тебе или брату.",
                                   reply_markup=fraction_choose_who_keyboard)
            await MenuStates.fraction_choose_who.set()
        case _:
            try:
                num = float(message.text.replace(",", "."))

                async with state.proxy() as data:
                    data["amount"] = message.text
                    to_who = data["to_who"]
                    amount = data["amount"]

                await db.insert_users_finances(message.from_user.id, "Выплата", amount, to_who)

                await bot.send_message(message.from_user.id, "Принято",
                                       reply_markup=main_menu_keyboard)

                with open(f"{message.from_user.username}_выплата.csv", mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['Имя', 'Тип', 'Сумма', 'Кому'])

                    writer.writerow([message.from_user.username, "Выплата доли", f'{amount} руб.', to_who])

                # await bot.send_document(message.from_user.id, open(f"{message.from_user.username}_выплата.csv", "rb"),
                #                         caption="#доля")
                await bot.send_message(message.from_user.id, f"#доля\n"
                                                             f"@{message.from_user.username} {amount} руб. {to_who}")

                await MenuStates.start.set()

            except ValueError:
                await bot.send_message(message.from_user.id, "Напиши цифрами, без букв, знаков и пробелов",
                                       reply_markup=back_keyboard)

            except Exception as e:
                print(f"Ошибка в fraction_pay_handle {e}")


@dp.message_handler(state=MenuStates.fraction_to_who)
async def fraction_to_who_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "Так выплачиваем или хотим поинтересоваться?",
                                   reply_markup=fraction_keyboard)
            await MenuStates.fraction_enter.set()

        case "Миша":
            cur_debt, cur_payment = await db.select_fraction(message.from_user.id, "Миша")
            debt = cur_debt * 0.4 - cur_payment

            if debt == 0:
                await bot.send_message(message.from_user.id, "На сегодня у Миши нет выплат",
                                       reply_markup=pay_keyboard)

            elif debt < 0:
                await bot.send_message(message.from_user.id, f"На сегодня Миша задолжал "
                                                             f"{debt} руб. в общак",
                                       reply_markup=pay_keyboard)

            else:
                await bot.send_message(message.from_user.id, f"На сегодня Мише должны выплатить"
                                                             f" {debt} руб.",
                                       reply_markup=pay_keyboard)

            await MenuStates.fraction_to_pay.set()

        case "Дато":
            cur_debt, cur_payment = await db.select_fraction(message.from_user.id, "Дато")
            debt = cur_debt*0.24 - cur_payment
            if debt == 0:
                await bot.send_message(message.from_user.id, "На сегодня у Дато нет выплат",
                                       reply_markup=pay_keyboard)

            elif debt < 0:
                await bot.send_message(message.from_user.id, f"На сегодня Дато задолжал "
                                                             f"{debt} руб. в общак",
                                       reply_markup=pay_keyboard)

            else:
                await bot.send_message(message.from_user.id, f"На сегодня Дато должны выплатить"
                                                             f" {debt} руб.",
                                       reply_markup=pay_keyboard)

            await MenuStates.fraction_to_pay.set()

        case "Глеб":
            cur_debt, cur_payment = await db.select_fraction(message.from_user.id, "Глеб")
            debt = cur_debt * 0.36 - cur_payment

            if debt == 0:
                await bot.send_message(message.from_user.id, "На сегодня у Глеба нет выплат",
                                       reply_markup=pay_keyboard)

            elif debt < 0:
                await bot.send_message(message.from_user.id, f"На сегодня Глеб задолжал "
                                                             f"{debt} руб. в общак",
                                       reply_markup=pay_keyboard)

            else:
                await bot.send_message(message.from_user.id, f"На сегодня Глебу должны выплатить"
                                                             f" {debt} руб.",
                                       reply_markup=pay_keyboard)

            await MenuStates.fraction_to_pay.set()

        case _:
            await bot.send_message(message.from_user.id, "Извини, брат, но тут надо пункты выбирать",
                                   reply_markup=fraction_choose_who_keyboard)


@dp.message_handler(state=MenuStates.fraction_to_pay)
async def fraction_pay_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "Чью долю к выплате хочешь узнать?",
                                   reply_markup=fraction_choose_who_keyboard)
            await MenuStates.fraction_to_who.set()

        case "Меню":
            await bot.send_message(message.from_user.id, "И снова здравствуйте",
                                   reply_markup=main_menu_keyboard)
            await MenuStates.start.set()

        case _:
            await bot.send_message(message.from_user.id, "Брат, тут надо пункты выбирать",
                                   reply_markup=pay_keyboard)


@dp.message_handler(state=MenuStates.report)
async def report_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "И снова здравствуйте", reply_markup=main_menu_keyboard)
            await MenuStates.start.set()

        case "Текущий месяц":
            report = await db.report_cur_month()

            await bot.send_message(message.from_user.id, "Генерирую отчёт")

            with open(f"{message.from_user.username}_отчёт.csv", mode='w', newline='', encoding='utf-8') as file:
                global_users_id = []

                writer = csv.writer(file)
                writer.writerow(["Все данные за текущий месяц", '', '', '', '', '', '', '',
                                 'Суммарно каждый пользователь'])
                writer.writerow(['Имя', 'Тип', 'Сумма', 'Комментарий', 'Дата', '', '', '', 'Имя', 'Доходы', 'Расходы',
                                 'К выплате Мише', 'К выплате Дато', 'К выплате Глебу', 'Выплачено Мише',
                                 'Выплачено Дато', 'Выплачено Глебу'])

                for i in report:
                    username = await db.get_user_by_id(i[1])

                    if username[2] not in global_users_id:
                        tg_id = await db.get_id_by_username(username[2])
                        incomes, expenses, to_pay_misha, to_pay_dato, to_pay_gleb, pays_misha, pays_dato, \
                            pays_gleb = await db.get_sum_by_user(tg_id)
                        type_request = i[2]
                        if type_request == "Выплата":
                            type_request = "Выплата доли"
                        writer.writerow([username[2], type_request, f'{i[3]} руб.', i[5], i[6], '', '', '', username[2],
                                         incomes, expenses, to_pay_misha, to_pay_dato, to_pay_gleb, pays_misha,
                                         pays_dato, pays_gleb])
                        global_users_id.append(username[2])
                    else:
                        type_request = i[2]
                        if type_request == "Выплата":
                            type_request = "Выплата доли"
                        writer.writerow([username[2], type_request, f'{i[3]} руб.', i[5], i[6]])

            cur_month_incomes, cur_month_expenses, profit, cur_month_pays, in_cashier, to_pay_misha, to_pay_dato,\
                to_pay_gleb = await db.get_all_info_without_user()

            await bot.send_document(message.from_user.id, open(f"{message.from_user.username}_отчёт.csv", "rb"),
                                    caption=f"Наши показатели за текущий месяц:\n"
                                            f"Доходы: {cur_month_incomes} руб.\n"
                                            f"Расходы: {cur_month_expenses} руб.\n"
                                            f"Прибыль: {profit} руб.\n"
                                            f"Выплаченные доли: {cur_month_pays} руб.\n"
                                            f"В кассе: {in_cashier} руб.\n\n"
                                            f"Доли к выплате:\n"
                                            f"Дато: {str(to_pay_dato)[:str(to_pay_dato).index('.') + 3]} руб.\n"
                                            f"Миша: {str(to_pay_misha)[:str(to_pay_misha).index('.') + 3]} руб.\n"
                                            f"Глеб: {str(to_pay_gleb)[:str(to_pay_gleb).index('.') + 3]} руб.",
                                    reply_markup=main_menu_keyboard)

            await bot.send_message(message.from_user.id, "И снова здравствуйте", reply_markup=main_menu_keyboard)

            await MenuStates.start.set()

        case "Период":
            calenda = generate_calendar(datetime.datetime.now().year, datetime.datetime.now().month)
            await bot.send_message(message.from_user.id, 'Сегодня - ' +
                                   str(datetime.datetime.today().strftime("%#d %B %Y")), reply_markup=back_keyboard)
            await bot.send_message(message.from_user.id, "Выбери дату начала отчётного периода",
                                   reply_markup=calenda)
            await MenuStates.choose_second_period.set()

        case _:
            await bot.send_message(message.from_user.id, "Извини, брат, но тут надо пункты выбирать",
                                   reply_markup=choose_period_keyboard)


@dp.callback_query_handler(state=MenuStates.choose_second_period)
async def day_chosen(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data.startswith('calendar-month'):
        year, month = callback_query.data.split('-')[2:]
        year, month = int(year), int(month)
        # Создаем новый календарь
        calendar_markup = generate_calendar(year, month)
        # Отправляем обновленный календарь
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=calendar_markup)

    else:
        selected_date = callback_query.data.split('-')[2]
        string = f"{selected_date}.{callback_query.data.split('-')[3]}.{callback_query.data.split('-')[4]}"
        date_object_for_bd = datetime.datetime.strptime(string, "%d.%m.%Y")
        async with state.proxy() as data:
            data["start"] = date_object_for_bd
        calenda = generate_calendar(datetime.datetime.now().year, datetime.datetime.now().month)
        await bot.send_message(callback_query.from_user.id, "Выбери дату окончания отчётного периода",
                               reply_markup=back_keyboard)
        await bot.send_message(callback_query.from_user.id, "Календарь",
                               reply_markup=calenda)
        await MenuStates.send_report.set()


@dp.message_handler(state=MenuStates.choose_second_period)
async def report_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "Так за какой период?",
                                   reply_markup=choose_period_keyboard)
            await MenuStates.report.set()


@dp.callback_query_handler(state=MenuStates.send_report)
async def day_chosen(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data.startswith('calendar-month'):
        year, month = callback_query.data.split('-')[2:]
        year, month = int(year), int(month)
        # Создаем новый календарь
        calendar_markup = generate_calendar(year, month)
        # Отправляем обновленный календарь
        await bot.edit_message_reply_markup(callback_query.message.chat.id, callback_query.message.message_id,
                                            reply_markup=calendar_markup)

    else:
        selected_date = callback_query.data.split('-')[2]
        string = f"{selected_date}.{callback_query.data.split('-')[3]}.{callback_query.data.split('-')[4]}"
        date_object_for_bd = datetime.datetime.strptime(string, "%d.%m.%Y")
        async with state.proxy() as data:
            data["end"] = date_object_for_bd
            start = data["start"]
        report = await db.report_period(start, date_object_for_bd)

        await bot.send_message(callback_query.from_user.id, "Генерирую отчёт")

        try:
            with open(f"{callback_query.from_user.username}_отчёт.csv", mode='w', newline='', encoding='utf-8')\
                    as file:
                global_users_id = []

                writer = csv.writer(file)
                writer.writerow(["Все данные за текущий месяц", '', '', '', '', '', '', '',
                                 'Суммарно каждый пользователь'])
                writer.writerow(['Имя', 'Тип', 'Сумма', 'Комментарий', 'Дата', '', '', '', 'Имя', 'Доходы',
                                 'Расходы', 'К выплате Мише', 'К выплате Дато', 'К выплате Глебу', 'Выплачено Мише',
                                 'Выплачено Дато', 'Выплачено Глебу'])

                for i in report:
                    username = await db.get_user_by_id(i[1])
                    if username[2] not in global_users_id:
                        tg_id = await db.get_id_by_username(username[2])
                        incomes, expenses, to_pay_misha, to_pay_dato, to_pay_gleb, pays_misha, pays_dato, \
                            pays_gleb = await db.get_sum_by_user_with_period(tg_id, start, date_object_for_bd)
                        type_request = i[2]
                        if type_request == "Выплата":
                            type_request = "Выплата доли"
                        writer.writerow([username[2], type_request, f'{i[3]} руб.', i[5], i[6], '', '', '', username[2],
                                         incomes, expenses, to_pay_misha, to_pay_dato, to_pay_gleb, pays_misha,
                                         pays_dato, pays_gleb])
                        global_users_id.append(username[2])
                    else:
                        type_request = i[2]
                        if type_request == "Выплата":
                            type_request = "Выплата доли"
                        writer.writerow([username[2], type_request, f'{i[3]} руб.', i[5], i[6]])

            # await bot.send_document(callback_query.from_user.id,
            #                         open(f"{callback_query.from_user.username}_отчёт.csv", "rb"),
            #                         caption="excel файл")
            cur_month_incomes, cur_month_expenses, profit, cur_month_pays, in_cashier, to_pay_misha, to_pay_dato, \
                to_pay_gleb = await db.get_all_info_without_user()

            await bot.send_document(callback_query.from_user.id,
                                    open(f"{callback_query.from_user.username}_отчёт.csv", "rb"),
                                    caption=f"Наши показатели за период с {start.strftime('%#d %B %Y')} по "
                                            f"{date_object_for_bd.strftime('%#d %B %Y')}:\n"
                                            f"Доходы: {cur_month_incomes} руб.\n"
                                            f"Расходы: {cur_month_expenses} руб.\n"
                                            f"Прибыль: {profit} руб.\n"
                                            f"Выплаченные доли: {cur_month_pays} руб.\n"
                                            f"В кассе: {in_cashier} руб.\n\n"
                                            f"Доли к выплате:\n"
                                            f"Дато: {str(to_pay_dato)[:str(to_pay_dato).index('.') + 3]} руб.\n"
                                            f"Миша: {str(to_pay_misha)[:str(to_pay_misha).index('.') + 3]} руб.\n"
                                            f"Глеб: {str(to_pay_gleb)[:str(to_pay_gleb).index('.') + 3]} руб.",
                                    reply_markup=main_menu_keyboard)

        except aiogram.utils.exceptions.MessageTextIsEmpty:
            await bot.send_message(callback_query.from_user.id, "Брат, по выбранному периоду нет инфы")

        await state.reset_state()
        await bot.send_message(callback_query.from_user.id, "И снова здравствуйте", reply_markup=main_menu_keyboard)
        await MenuStates.start.set()


@dp.message_handler(state=MenuStates.send_report)
async def report_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            calenda = generate_calendar(datetime.datetime.now().year, datetime.datetime.now().month)
            await bot.send_message(message.from_user.id, "Откуда начинаем?",
                                   reply_markup=back_keyboard)
            await bot.send_message(message.from_user.id, "Календарь",
                                   reply_markup=calenda)

            await MenuStates.choose_second_period.set()


executor.start_polling(dp, skip_updates=True)
