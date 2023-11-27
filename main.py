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
    expense_enter_file = State()
    income = State()
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
    KeyboardButton(text="Выплатить"), KeyboardButton(text="Назад"))


# Обработка команды /start
@dp.message_handler(commands='start', state='*')
async def command_start(message: types.Message, state: FSMContext):
    await state.finish()

    await db.user_exists(message.from_user.id)

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
                    if "income" not in data:
                        data["expense"] = message.text
                await bot.send_message(message.from_user.id, "На что мы потратили столько денег, брат?"
                                                             " Поясни в двух словах.", reply_markup=back_keyboard)

                await MenuStates.expense_enter_file.set()

            except ValueError:
                await bot.send_message(message.from_user.id, "Напиши цифрами, без букв, знаков и пробелов",
                                       reply_markup=back_keyboard)

            except Exception as e:
                print(f"Ошибка в expense_sum_handle {e}")


@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=MenuStates.expense_enter_file)
async def handle_photos(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "photos" not in data:
            data["photos"] = []

        # Добавление фотографий в список
        data["photos"].append(message.photo[-1].file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Фотография добавлена", reply_markup=back_n_next_button)


@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state=MenuStates.expense_enter_file)
async def handle_docs(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "documents" not in data:
            data["documents"] = []

        # Добавление фотографий в список
        data["documents"].append(message.document.file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Документ добавлен", reply_markup=back_n_next_button)


@dp.message_handler(content_types=types.ContentTypes.VIDEO, state=MenuStates.expense_enter_file)
async def handle_docs(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "video" not in data:
            data["video"] = []

        # Добавление фотографий в список
        data["video"].append(message.photo[-1].file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Видео добавлено", reply_markup=back_n_next_button)


# Функция обрабатывающая кнопку назад, если пользователь выбрал отправить фотографию
@dp.message_handler(content_types=types.ContentTypes.TEXT, state=MenuStates.expense_enter_file)
async def choose_will_be_photo(message: types.Message, state: FSMContext):
    if 'Назад' in message.text:
        await bot.send_message(message.from_user.id, "Так сколько потратили, брат?",
                               reply_markup=back_keyboard)
        await MenuStates.expense.set()

    elif "Далее" in message.text:
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

                await db.update_attachments_expense(message.from_user.id, photos_for_save)

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

                await db.update_attachments_expense(message.from_user.id, documents_for_save)

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

                await db.update_attachments_expense(message.from_user.id, video_for_save)

            except KeyError:
                pass

        async with state.proxy() as data:
            expense = data["expense"]

            await db.update_expense(message.from_user.id, expense)

        # Очистка состояния
        await state.reset_state()

        # Ответное сообщение об успешной обработке
        await message.reply("Зафиксировано", reply_markup=main_menu_keyboard)
        await MenuStates.start.set()

    else:
        await bot.send_message(message.from_user.id, "Брат, отправь мне видео, фото, документ или нажми на кнопку",
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
                    if "income" not in data:
                        data["income"] = message.text
                await bot.send_message(message.from_user.id, "На чем подняли такую котлету?"
                                                             " Поясни пацанам по-братски.", reply_markup=back_keyboard)
                await MenuStates.income_enter_file.set()

            except ValueError:
                await bot.send_message(message.from_user.id, "Напиши цифрами, без букв, знаков и пробелов",
                                       reply_markup=back_keyboard)

            except Exception as e:
                print(f"Ошибка в income_sum_handle {e}")


@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=MenuStates.income_enter_file)
async def handle_photos(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "photos" not in data:
            data["photos"] = []

        # Добавление фотографий в список
        data["photos"].append(message.photo[-1].file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Фотография добавлена", reply_markup=back_n_next_button)


@dp.message_handler(content_types=types.ContentTypes.DOCUMENT, state=MenuStates.income_enter_file)
async def handle_docs(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "documents" not in data:
            data["documents"] = []

        # Добавление фотографий в список
        data["documents"].append(message.document.file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Документ добавлен", reply_markup=back_n_next_button)


@dp.message_handler(content_types=types.ContentTypes.VIDEO, state=MenuStates.income_enter_file)
async def handle_docs(message: types.Message, state: FSMContext):
    # Получение текущего состояния пользователя
    async with state.proxy() as data:
        if "video" not in data:
            data["video"] = []

        # Добавление фотографий в список
        data["video"].append(message.photo[-1].file_id)

    # Ответное сообщение о сохранении фотографии
    await message.reply("Видео добавлено", reply_markup=back_n_next_button)


# Функция обрабатывающая кнопку назад, если пользователь выбрал отправить фотографию
@dp.message_handler(content_types=types.ContentTypes.TEXT, state=MenuStates.income_enter_file)
async def choose_will_be_photo(message: types.Message, state: FSMContext):
    if 'Назад' in message.text:
        await bot.send_message(message.from_user.id, "Так сколько подняли бабла, брат?",
                               reply_markup=back_keyboard)
        await MenuStates.income.set()

    elif "Далее" in message.text:
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

                await db.update_attachments_income(message.from_user.id, photos_for_save)

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

                await db.update_attachments_income(message.from_user.id, documents_for_save)

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

                await db.update_attachments_income(message.from_user.id, video_for_save)

            except KeyError:
                pass

        async with state.proxy() as data:
            expense = data["income"]

            await db.update_income(message.from_user.id, expense)

        # Очистка состояния
        await state.reset_state()

        # Ответное сообщение об успешной обработке
        await message.reply("Зафиксировано", reply_markup=main_menu_keyboard)
        await MenuStates.start.set()

    else:
        await bot.send_message(message.from_user.id, "Брат, отправь мне видео, фото, документ или нажми на кнопку",
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
                num = message.text.replace(",", ".")
                float(num)

                await db.update_pay_fraction(message.from_user.id, message.text)
                await db.update_negative_debt(message.from_user.id, message.text)

                await bot.send_message(message.from_user.id, "Принято",
                                       reply_markup=main_menu_keyboard)
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
            fraction_without_percent = await db.get_fraction_without_percent(message.from_user.id)

            fraction = fraction_without_percent*0.4

            old_fraction = await db.get_old_fraction(message.from_user.id)
            if old_fraction != 0:
                await db.update_positive_debt(message.from_user.id, old_fraction)
            else:
                await db.update_positive_debt(message.from_user.id, fraction)

            await db.update_fraction(message.from_user.id, fraction, "Миша")

            debt = await db.get_debt(message.from_user.id)

            await bot.send_message(message.from_user.id, f"На сегодня Мише должны выплатить"
                                                         f" {debt} руб.",
                                   reply_markup=pay_keyboard)



            await MenuStates.fraction_to_pay.set()

        case "Дато":
            fraction_without_percent = await db.get_fraction_without_percent(message.from_user.id)

            fraction = fraction_without_percent * 0.24

            old_fraction = await db.get_old_fraction(message.from_user.id)
            if old_fraction != 0:
                await db.update_positive_debt(message.from_user.id, old_fraction)
            else:
                await db.update_positive_debt(message.from_user.id, fraction)

            await db.update_fraction(message.from_user.id, fraction, "Дато")

            debt = await db.get_debt(message.from_user.id)

            await bot.send_message(message.from_user.id, f"На сегодня Дато должны выплатить"
                                                         f" {debt} руб.",
                                   reply_markup=pay_keyboard)

            await MenuStates.fraction_to_pay.set()

        case "Глеб":
            fraction_without_percent = await db.get_fraction_without_percent(message.from_user.id)

            fraction = fraction_without_percent * 0.36

            old_fraction = await db.get_old_fraction(message.from_user.id)
            if old_fraction != 0:
                await db.update_positive_debt(message.from_user.id, old_fraction)
            else:
                await db.update_positive_debt(message.from_user.id, fraction)

            await db.update_fraction(message.from_user.id, fraction, "Глеб")

            debt = await db.get_debt(message.from_user.id)

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

        case "Выплатить":
            await bot.send_message(message.from_user.id, "Отправь мне сумму, которую хочешь выплатить",
                                   reply_markup=back_keyboard)

        case _:
            try:
                num = message.text.replace(",", ".")
                float(num)

                await db.update_pay_fraction(message.from_user.id, message.text)
                await db.update_negative_debt(message.from_user.id, message.text)

                await bot.send_message(message.from_user.id, "Принято", reply_markup=main_menu_keyboard)
                await MenuStates.start.set()

            except ValueError:
                await bot.send_message(message.from_user.id, "Напиши цифрами, без букв, знаков и пробелов",
                                       reply_markup=back_keyboard)

            except Exception as e:
                print(f"Ошибка в fraction_to_pay_handle {e}")


@dp.message_handler(state=MenuStates.report)
async def report_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "И снова здравствуйте", reply_markup=main_menu_keyboard)
            await MenuStates.start.set()

        case "Текущий месяц":
            await bot.send_message(message.from_user.id, "Отправляю данные")
            await bot.send_message(message.from_user.id, "И снова здравствуйте", reply_markup=main_menu_keyboard)

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
        await bot.send_message(callback_query.from_user.id, "Генерирую отчёт")
        await bot.send_message(callback_query.from_user.id, "Меню", reply_markup=main_menu_keyboard)
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
