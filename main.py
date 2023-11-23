from aiogram import Bot, types
# Память для машины состояний и машина состояний
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
# Машина состояний импорты
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import calendar
import datetime

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


# Создаём бота исходя из полученного токена
bot = Bot(token="6395802297:AAGSL6IBKgTVN8dPRHNVjUzLHuLCHy_y5lM")
dp = Dispatcher(bot, storage=storage)

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


# Обработка команды /start
@dp.message_handler(commands='start', state='*')
async def command_start(message: types.Message, state: FSMContext):
    await state.finish()

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
                num = message.text.replace(",", ".")
                float(num)
                await bot.send_message(message.from_user.id, "На что мы потратили столько денег, брат?"
                                                             " Поясни в двух словах.", reply_markup=back_keyboard)
                await MenuStates.expense_enter_file.set()

            except ValueError:
                await bot.send_message(message.from_user.id, "Напиши цифрами, без букв, знаков и пробелов",
                                       reply_markup=back_keyboard)

            except Exception as e:
                print(f"Ошибка в expense_sum_handle {e}")


@dp.message_handler(state=MenuStates.expense_enter_file)
async def expense_file_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "Так сколько потратили, брат?",
                                   reply_markup=back_keyboard)
            await MenuStates.expense.set()


@dp.message_handler(state=MenuStates.income)
async def income_sum_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "И снова здравствуйте", reply_markup=main_menu_keyboard)
            await MenuStates.start.set()

        case _:
            try:
                num = message.text.replace(",", ".")
                float(num)
                await bot.send_message(message.from_user.id, "На чем подняли такую котлету?"
                                                             " Поясни пацанам по-братски.", reply_markup=back_keyboard)
                await MenuStates.income_enter_file.set()

            except ValueError:
                await bot.send_message(message.from_user.id, "Напиши цифрами, без букв, знаков и пробелов",
                                       reply_markup=back_keyboard)

            except Exception as e:
                print(f"Ошибка в income_sum_handle {e}")


@dp.message_handler(state=MenuStates.income_enter_file)
async def income_file_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "Вы вернулись к шагу ввода суммы",
                                   reply_markup=back_keyboard)
            await MenuStates.income.set()


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
            await bot.send_message(message.from_user.id, "Вы вернулись на шаг выбора получателя",
                                   reply_markup=fraction_choose_who_keyboard)
            await MenuStates.fraction_choose_who.set()
        case _:
            try:
                num = message.text.replace(",", ".")
                float(num)

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
            await bot.send_message(message.from_user.id, "Вы вернулись к шагу выбора доли",
                                   reply_markup=fraction_keyboard)
            await MenuStates.fraction_enter.set()

        case "Миша" | "Дато" | "Глеб":
            await bot.send_message(message.from_user.id, "Пример: На сегодня ему должны выплатить 100 рублей",
                                   reply_markup=back_keyboard)
            await MenuStates.fraction_to_pay.set()

        case _:
            await bot.send_message(message.from_user.id, "Извини, брат, но тут надо пункты выбирать",
                                   reply_markup=fraction_choose_who_keyboard)


@dp.message_handler(state=MenuStates.fraction_to_pay)
async def fraction_pay_handle(message: types.Message, state: FSMContext):
    match message.text:
        case "Назад":
            await bot.send_message(message.from_user.id, "Кому выплачиваем долю?",
                                   reply_markup=fraction_choose_who_keyboard)
            await MenuStates.fraction_to_who.set()
        case _:
            try:
                num = message.text.replace(",", ".")
                float(num)

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
            await bot.send_message(message.from_user.id, "Вы вернулись к выбору периода",
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
            await bot.send_message(message.from_user.id, "Вы вернулись к выбору начала периода",
                                   reply_markup=back_keyboard)
            await bot.send_message(message.from_user.id, "Календарь",
                                   reply_markup=calenda)

            await MenuStates.choose_second_period.set()

executor.start_polling(dp, skip_updates=True)