import datetime

import psycopg2

conn = psycopg2.connect(dbname='fraction', user='shalor1k', password='bd260703', host='localhost')
cur = conn.cursor()


# Проверяем, есть ли юзер в базе
async def user_exists(user_id: int, username: str) -> None:
    try:
        cur.execute("SELECT EXISTS (SELECT * FROM users WHERE tg_id = '{}')".format(str(user_id)))
        if not cur.fetchone()[0]:
            await add_user(user_id, username)
            await insert_users_finances(user_id)
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


async def insert_users_finances(user_id: int) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("INSERT INTO users_finances (user_id, date) VALUES ('{}', '{}')".format(db_user_id,
                                                                                            datetime.datetime.today()))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в insert_users_finances {e}")


async def update_expense(user_id: int, expense: int) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("UPDATE users_finances SET expense = expense + '{}'"
                    " WHERE user_id = '{}' AND closed IS FALSE".format(expense, db_user_id))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в update_expenses {e}")


async def update_income(user_id: int, income: int) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("UPDATE users_finances SET income = income + '{}'"
                    " WHERE user_id = '{}' AND closed IS FALSE".format(income, db_user_id))
        conn.commit()

        await update_update_flag_in_users_debt(user_id, True)

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в update_income {e}")


async def update_attachments_income(user_id: int, attachments: list) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute(
            "UPDATE users_finances "
            "SET attachments_income = attachments_income || ARRAY{} "
            "WHERE user_id = '{}' AND closed IS FALSE".format(attachments, db_user_id, ))
        conn.commit()

    except Exception as e:
        print(f"Ошибка в update_attachments_income {e}")
        conn.rollback()


async def update_attachments_expense(user_id: int, attachments: list) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute(
            "UPDATE users_finances "
            "SET attachments_expense = attachments_expense || ARRAY{} "
            "WHERE user_id = '{}' AND closed IS FALSE".format(attachments, db_user_id, ))
        conn.commit()

    except Exception as e:
        print(f"Ошибка в update_attachments_expense {e}")
        conn.rollback()


async def get_fraction_without_percent(user_id: int) -> int:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("SELECT income, expense FROM users_finances"
                    " WHERE user_id = '{}' AND closed is FALSE".format(db_user_id))
        income, expense = cur.fetchone()

        if income is None:
            income = 0

        if expense is None:
            expense = 0

        return income - expense

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в get_fraction_without_percent {e}")


async def get_old_fraction(user_id: int) -> float:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("SELECT fraction FROM users_finances WHERE user_id = '{}' AND closed IS FALSE".format(db_user_id))
        return cur.fetchone()[0]

    except Exception as e:
        print(f"Ошибка в get_old_fraction {e}")


async def update_fraction(user_id: int, fraction: float) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("UPDATE users_finances SET fraction = '{}'"
                    " WHERE user_id = '{}' AND closed IS FALSE".format(fraction, db_user_id))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в update_fraction {e}")


async def update_fraction_with_name(user_id: int, fraction: float, to_who: str) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        match to_who:
            case "Миша":
                cur.execute("UPDATE users_finances SET fraction_misha = '{}' "
                            "WHERE user_id = '{}'".format(fraction, db_user_id))
                conn.commit()

            case "Дато":
                cur.execute("UPDATE users_finances SET fraction_dato = '{}' "
                            "WHERE user_id = '{}'".format(fraction, db_user_id))
                conn.commit()

            case "Глеб":
                cur.execute("UPDATE users_finances SET fraction_gleb = '{}' "
                            "WHERE user_id = '{}'".format(fraction, db_user_id))
                conn.commit()

            case _:
                print(f"Получил неизвестные данные: {to_who} в update_fraction_with_name")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в update_fraction_with_name {e}")


async def select_fraction_with_name(user_id: int, to_who: str) -> float:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        match to_who:
            case "Миша":
                cur.execute("SELECT fraction_misha FROM users_finances "
                            "WHERE user_id = '{}'".format(db_user_id))
                fraction = cur.fetchone()[0]
                if fraction is None:
                    return 0
                return fraction

            case "Дато":
                cur.execute("SELECT fraction_dato FROM users_finances "
                            "WHERE user_id = '{}'".format(db_user_id))
                fraction = cur.fetchone()[0]
                if fraction is None:
                    return 0
                return fraction

            case "Глеб":
                cur.execute("SELECT fraction_gleb FROM users_finances "
                            "WHERE user_id = '{}'".format(db_user_id))
                fraction = cur.fetchone()[0]
                if fraction is None:
                    return 0
                return fraction

            case _:
                print(f"Получил неизвестные данные: {to_who} в select_fraction_with_name")

    except Exception as e:
        print(f"Ошибка в update_fraction_with_name {e}")


async def update_paid_with_name(user_id: int, paid: float, to_who: str) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        match to_who:
            case "Миша":
                cur.execute("UPDATE users_finances SET paid_misha = '{}' "
                            "WHERE user_id = '{}'".format(paid, db_user_id))
                conn.commit()

            case "Дато":
                cur.execute("UPDATE users_finances SET paid_dato = '{}' "
                            "WHERE user_id = '{}'".format(paid, db_user_id))
                conn.commit()

            case "Глеб":
                cur.execute("UPDATE users_finances SET paid_gleb = '{}' "
                            "WHERE user_id = '{}'".format(paid, db_user_id))
                conn.commit()

            case _:
                print(f"Получил неизвестные данные: {to_who} в update_paid_with_name")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в update_paid_with_name {e}")


async def select_paid_with_name(user_id: int, to_who: str) -> float:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        match to_who:
            case "Миша":
                cur.execute("SELECT paid_misha FROM users_finances "
                            "WHERE user_id = '{}'".format(db_user_id))
                paid = cur.fetchone()[0]
                if paid is None:
                    return 0
                return paid

            case "Дато":
                cur.execute("SELECT paid_dato FROM users_finances "
                            "WHERE user_id = '{}'".format(db_user_id))
                paid = cur.fetchone()[0]
                if paid is None:
                    return 0
                return paid

            case "Глеб":
                cur.execute("SELECT paid_gleb FROM users_finances "
                            "WHERE user_id = '{}'".format(db_user_id))
                paid = cur.fetchone()[0]
                if paid is None:
                    return 0
                return paid

            case _:
                print(f"Получил неизвестные данные: {to_who} в select_paid_with_name")

    except Exception as e:
        print(f"Ошибка в select_paid_with_name {e}")


async def update_negative_debt(user_id: int, debt: float) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("UPDATE users_debt SET debt = debt - '{}' "
                    "WHERE user_id = '{}'".format(debt, db_user_id))
        conn.commit()

        await update_update_flag_in_users_debt(user_id, False)

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в update_negative_debt {e}")


async def update_positive_debt(user_id: int, debt: float) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("UPDATE users_debt SET debt = debt + '{}' "
                    "WHERE user_id = '{}' AND update IS TRUE".format(debt, db_user_id))
        conn.commit()

        await update_update_flag_in_users_debt(user_id, False)

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в update_positive_debt {e}")


async def update_update_flag_in_users_debt(user_id: int, flag: bool) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("UPDATE users_debt SET update = '{}' "
                    "WHERE user_id = '{}'".format(flag, db_user_id))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в update_update_flag_in_users_debt {e}")


async def update_pay_fraction(user_id: int, pay: float) -> None:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("UPDATE users_finances SET pay_fraction = '{}' "
                    " WHERE user_id = '{}' AND closed IS FALSE".format(pay, db_user_id))
        conn.commit()

        cur.execute("UPDATE users_finances SET closed = TRUE "
                    "WHERE user_id = '{}' AND closed IS FALSE".format(db_user_id))
        conn.commit()

        await insert_users_finances(user_id)

    except Exception as e:
        conn.rollback()
        print(f"Ошибка в update_pay_fraction {e}")


async def get_debt(user_id: int) -> float:
    try:
        cur.execute(
            "SELECT a.id FROM users as a WHERE a.tg_id = '{}'".format(str(user_id)))
        db_user_id = cur.fetchone()[0]

        cur.execute("SELECT debt FROM users_debt WHERE user_id = '{}'".format(db_user_id))
        debt = cur.fetchone()[0]

        return float(debt)

    except Exception as e:
        print(f"Ошибка в get_debt {e}")
