import datetime

import psycopg2

conn = psycopg2.connect(dbname='fractions', user='postgres', password='bd260703', host='192.168.0.10')
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


async def report_cur_month():
    try:
        cur.execute(f"SELECT * FROM users_finances WHERE DATE_PART('month', date) = {datetime.datetime.now().month}")
        cur.execute(f"SELECT * FROM users_finances WHERE EXTRACT(MONTH FROM date) > 10;")
        res = cur.fetchall()

        print(res)

    except Exception as e:
        print(f"Ошибка в report_cur_month {e}")