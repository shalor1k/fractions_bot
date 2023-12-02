import datetime

import psycopg2

conn = psycopg2.connect(dbname='fractions', user='shalor1k', password='ffff', host='localhost')
cur = conn.cursor()


# Проверяем, есть ли юзер в базе
async def user_exists(user_id: int, username: str) -> None:
    try:
        cur.execute("SELECT EXISTS (SELECT * FROM users WHERE tg_id = '{}')".format(str(user_id)))
        if not cur.fetchone()[0]:
            await add_user(user_id, username)
            await add_user_to_users_debt(user_id)

    except Exception as e:
        print(f'Ошибка в user_exists {e}')


# Добвляем юзера в базу
async def add_user(user_id: int, username: str) -> None:
    try:
        cur.execute("SELECT MAX(id) FROM users")
        db_user_id = cur.fetchone()
        if db_user_id[0] is None:
            db_user_id = 0
        else:
            db_user_id = db_user_id[0] + 1
        cur.execute(
            "INSERT INTO users (id, tg_id, username) VALUES ('{}', '{}', '{}')".format(db_user_id, str(user_id),
                                                                                       username))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f'Ошибка в add_user {e}')


# Добвляем юзера в базу
async def add_user_to_users_debt(user_id) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO users_debt (user_id) VALUES ('{}')".format(db_user_id))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f'Ошибка в add_user_to_users_debt {e}')


async def insert_users_finances(user_id: int, type_request: str, amount: float, comment: str,
                                attachments=None) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]
        cur.execute("SELECT MAX(id) FROM users_finances")
        db_max_row_id = cur.fetchone()
        if db_max_row_id[0] is None:
            db_max_row_id = 0
        else:
            db_max_row_id = db_max_row_id[0] + 1

        if attachments is None:
            cur.execute("INSERT INTO users_finances (id, user_id, type, amount, comment, date)"
                        " VALUES ('{}', '{}', '{}', '{}', '{}', '{}')".format(db_max_row_id,  db_user_id, type_request,
                                                                              amount, comment,
                                                                              datetime.datetime.today()
                                                                              .strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
        else:
            cur.execute("INSERT INTO users_finances (id, user_id, type, amount, comment, date)"
                        " VALUES ('{}', '{}', '{}', '{}', '{}', '{}')".format(db_max_row_id, db_user_id, type_request,
                                                                              amount, comment,
                                                                              datetime.datetime.today()
                                                                              .strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            await update_attachments(user_id, attachments)

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в insert_users_finances {e}")


async def update_attachments(user_id: int, attachments: list) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute(
            "UPDATE users_finances "
            "SET attachments = attachments || ARRAY{} "
            "WHERE user_id = '{}' AND"
            " id = (SELECT MAX(id) FROM users_finances WHERE user_id = '{}')".format(attachments, db_user_id,
                                                                                     db_user_id))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в update_attachments {e}")


async def select_fraction(user_id: int, to_who: str) -> tuple:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = '{db_user_id}' AND type = 'Доход'")
        res_incomes = cur.fetchone()
        if res_incomes[0] is not None:
            incomes = res_incomes[0]
        else:
            incomes = 0

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = '{db_user_id}' AND type = 'Расход'")
        res_expenses = cur.fetchone()

        if res_expenses[0] is not None:
            expenses = res_expenses[0]
        else:
            expenses = 0

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = '{db_user_id}' AND type = 'Выплата' AND"
                    f" comment = '{to_who}'")
        res_payment = cur.fetchone()

        if res_payment[0] is not None:
            cur_payment = res_payment[0]
            return float(incomes - expenses), float(cur_payment)

        return float(incomes - expenses), 0

    except Exception as e:
        print(f"Ошибка в select_fraction {e}")


async def report_cur_month() -> list:
    try:
        cur.execute(f"SELECT * FROM users_finances WHERE DATE_PART('month', date) = {datetime.datetime.now().month}")
        cur_month_res = cur.fetchall()

        return cur_month_res

    except Exception as e:
        print(f"Ошибка в report_cur_month {e}")


async def report_period(start_date: str, end_date: str) -> list:
    try:
        cur.execute(f"SELECT * FROM users_finances WHERE date >= '{start_date}' AND date <= '{end_date}'")
        period_res = cur.fetchall()

        return period_res

    except Exception as e:
        print(f"Ошибка в report_period {e}")


async def get_user_by_id(db_id: int) -> tuple:
    try:
        cur.execute(f"SELECT * FROM users WHERE id = '{db_id}'")
        about_user = cur.fetchone()

        return about_user

    except Exception as e:
        print(f"Ошибка в get_user_by_id {e}")


async def get_id_by_username(username: str) -> int:
    try:
        cur.execute(f"SELECT tg_id FROM users WHERE username = '{username}'")
        tg_id = cur.fetchone()

        return tg_id[0]

    except Exception as e:
        print(f"Ошибка в get_id_by_username {e}")


async def get_sum_by_user(user_id: int) -> list:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = {db_user_id} AND type = 'Доход'")
        incomes = cur.fetchone()[0]
        if incomes is None:
            incomes = 0

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = {db_user_id} AND type = 'Расход'")
        expenses = cur.fetchone()[0]
        if expenses is None:
            expenses = 0

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = {db_user_id}"
                    f" AND type = 'Выплата' AND comment = 'Миша'")
        pays_misha = cur.fetchone()[0]
        if pays_misha is None:
            pays_misha = 0

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = {db_user_id}"
                    f" AND type = 'Выплата' AND comment = 'Дато'")
        pays_dato = cur.fetchone()[0]
        if pays_dato is None:
            pays_dato = 0

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = {db_user_id}"
                    f" AND type = 'Выплата' AND comment = 'Глеб'")
        pays_gleb = cur.fetchone()[0]

        if pays_gleb is None:
            pays_gleb = 0

        return [incomes, expenses, float(incomes - expenses)*0.4 - float(pays_misha),
                float(incomes - expenses) * 0.24 - float(pays_dato), float(incomes - expenses)*0.36 - float(pays_dato),
                pays_misha, pays_dato, pays_gleb]

    except Exception as e:
        print(f"Ошибка в get_sum_by_user {e}")


async def get_sum_by_user_with_period(user_id: int, start_date: str, end_date: str) -> list:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = {db_user_id} AND type = 'Доход' AND"
                    f" date >= '{start_date}' AND date <= '{end_date}'")
        incomes = cur.fetchone()[0]
        if incomes is None:
            incomes = 0

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = {db_user_id} AND type = 'Расход' AND"
                    f" date >= '{start_date}' AND date <= '{end_date}'")
        expenses = cur.fetchone()[0]
        if expenses is None:
            expenses = 0

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = {db_user_id}"
                    f" AND type = 'Выплата' AND comment = 'Миша' AND date >= '{start_date}' AND date <= '{end_date}'")
        pays_misha = cur.fetchone()[0]
        if pays_misha is None:
            pays_misha = 0

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = {db_user_id}"
                    f" AND type = 'Выплата' AND comment = 'Дато' AND date >= '{start_date}' AND date <= '{end_date}'")
        pays_dato = cur.fetchone()[0]
        if pays_dato is None:
            pays_dato = 0

        cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE user_id = {db_user_id}"
                    f" AND type = 'Выплата' AND comment = 'Глеб' AND date >= '{start_date}' AND date <= '{end_date}'")
        pays_gleb = cur.fetchone()[0]

        if pays_gleb is None:
            pays_gleb = 0

        return [incomes, expenses, float(incomes - expenses)*0.4 - float(pays_misha),
                float(incomes - expenses) * 0.24 - float(pays_dato), float(incomes - expenses)*0.36 - float(pays_dato),
                pays_misha, pays_dato, pays_gleb]

    except Exception as e:
        print(f"Ошибка в get_sum_by_user {e}")


async def get_all_info_without_user() -> list:
    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Доход' AND DATE_PART('month', date) = "
                f"{datetime.datetime.now().month}")
    cur_month_incomes = cur.fetchone()[0]

    if cur_month_incomes is None:
        cur_month_incomes = 0

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Доход'")
    all_incomes = cur.fetchone()[0]

    if all_incomes is None:
        all_incomes = 0

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Расход' AND DATE_PART('month', date) = "
                f"{datetime.datetime.now().month}")
    cur_month_expenses = cur.fetchone()[0]

    if cur_month_expenses is None:
        cur_month_expenses = 0

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Расход'")
    all_expenses = cur.fetchone()[0]

    if all_expenses is None:
        all_expenses = 0

    profit = cur_month_incomes - cur_month_expenses

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата' AND DATE_PART('month', date) = "
                f"{datetime.datetime.now().month}")
    cur_month_pays = cur.fetchone()[0]

    if cur_month_pays is None:
        cur_month_pays = 0

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата'")
    all_pays = cur.fetchone()[0]

    if all_pays is None:
        all_pays = 0

    in_cashier = all_incomes - all_expenses - all_pays

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата' AND comment = 'Миша'")
    to_pay_misha = cur.fetchone()[0]
    if to_pay_misha is None:
        to_pay_misha = 0
    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата' AND comment = 'Дато'")
    to_pay_dato = cur.fetchone()[0]
    if to_pay_dato is None:
        to_pay_dato = 0
    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата' AND comment = 'Глеб'")
    to_pay_gleb = cur.fetchone()[0]
    if to_pay_gleb is None:
        to_pay_gleb = 0

    return [cur_month_incomes, cur_month_expenses, profit, cur_month_pays, in_cashier,
            float(all_incomes-all_expenses)*0.4-float(to_pay_misha),
            float(all_incomes-all_expenses)*0.24-float(to_pay_dato),
            float(all_incomes-all_expenses)*0.36-float(to_pay_gleb)]


async def get_all_info_without_user_with_period(start_date: str, end_date: str) -> list:
    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Доход' AND "
                f"date >= '{start_date}' AND date <= '{end_date}'")
    cur_period_incomes = cur.fetchone()[0]

    if cur_period_incomes is None:
        cur_period_incomes = 0

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Доход'")
    all_incomes = cur.fetchone()[0]

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Расход' AND "
                f"date >= '{start_date}' AND date <= '{end_date}'")
    cur_period_expenses = cur.fetchone()[0]

    if cur_period_expenses is None:
        cur_period_expenses = 0

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Расход'")
    all_expenses = cur.fetchone()[0]

    profit = cur_period_incomes - cur_period_expenses

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата' AND "
                f"date >= '{start_date}' AND date <= '{end_date}'")
    cur_period_pays = cur.fetchone()[0]

    if cur_period_pays is None:
        cur_period_pays = 0

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата'")
    all_pays = cur.fetchone()[0]

    in_cashier = all_incomes - all_expenses - all_pays

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата' AND comment = 'Миша'")
    to_pay_misha = cur.fetchone()[0]
    if to_pay_misha is None:
        to_pay_misha = 0
    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата' AND comment = 'Дато'")
    to_pay_dato = cur.fetchone()[0]
    if to_pay_dato is None:
        to_pay_dato = 0
    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата' AND comment = 'Миша'")
    to_pay_gleb = cur.fetchone()[0]
    if to_pay_gleb is None:
        to_pay_gleb = 0

    return [cur_period_incomes, cur_period_expenses, profit, cur_period_pays, in_cashier,
            float(all_incomes-all_expenses)*0.4-float(to_pay_misha),
            float(all_incomes-all_expenses)*0.24-float(to_pay_dato),
            float(all_incomes-all_expenses)*0.36-float(to_pay_gleb)]


async def get_in_cashier_all() -> float:
    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Доход'")
    all_incomes = cur.fetchone()[0]

    if all_incomes is None:
        all_incomes = 0

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Расход'")
    all_expenses = cur.fetchone()[0]

    if all_expenses is None:
        all_expenses = 0

    cur.execute(f"SELECT SUM(amount) FROM users_finances WHERE type = 'Выплата'")
    all_pays = cur.fetchone()[0]

    if all_pays is None:
        all_pays = 0

    return all_incomes - all_expenses - all_pays
