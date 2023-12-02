import psycopg2
from prettytable import PrettyTable

# Установите соединение с базой данных PostgreSQL
connection = psycopg2.connect(dbname='fractions', user='shalor1k',
                              password='bd260703', host='localhost')
# Создание курсора
cursor = connection.cursor()
# Выполнение запроса для получения всех таблиц
cursor.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
)

# Получение результатов
tables = cursor.fetchall()

# Вывод таблиц, названий столбцов и их значений
for table_name in tables:

    # Выполнение запроса к базе данных и получение результатов
    cursor.execute(f"SELECT * FROM {table_name[0]}")
    rows = cursor.fetchall()

    # Создание объекта PrettyTable
    table = PrettyTable()

    table.title = f"{table_name[0]}"
    # Добавление заголовков столбцов
    column_names = [desc[0] for desc in cursor.description]
    table.field_names = column_names

    # Добавление данных в таблицу
    for row in rows:
        table.add_row(row)

    # Вывод таблицы
    print(table)

    # Закрытие курсора и соединения с базой данных
cursor.close()
connection.close()





