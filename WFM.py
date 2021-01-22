import pyodbc
import time

from telebot import types

from Settings import CONNECTION_STRING


class WFM():
    """Класс, который отвечает за WFM"""

    user_id = None
    fullname = ""
    role = ""

    @staticmethod
    def is_wfm(user_id):
        """Проверить является ли пользователь сотрудником WFM"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT u.user_id " \
              f"FROM UKSTGBot.dbo.Users u with(nolock) " \
              f"JOIN UKSTGBot.dbo.Callider c with(nolock) on c.userlogin = u.userlogin " \
              f"WHERE u.user_id = {user_id} " \
              f"  AND u.is_block = 0 " \
              f"  AND c.role = 10"
        result = sqlserver_cursor.execute(sql).fetchone()
        return result is not None

    def __init__(self, spectator_id):
        """Ининциализация руководителя / продуктового эксперта"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT u.user_id " \
              f"  , c.fullname " \
              f"  , ur.role_name " \
              f"FROM UKSTGBot.dbo.Users as u with(nolock) " \
              f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = u.userlogin " \
              f"JOIN UKSTGBot.dbo.UserRoles as ur with(nolock) ON ur.role_id = c.role " \
              f"WHERE u.user_id = {spectator_id} " \
              f"  AND u.is_block = 0 "
        data = sqlserver_cursor.execute(sql).fetchone()
        self.user_id = data[0]
        self.fullname = data[1]
        self.role = data[2]
        sqlserver_db.close()

    def to_str(self):
        """Вывести информацию по WFM"""
        return f"ID : {self.user_id}\nФИО : {self.fullname}\nРоль : {self.role}\n"

    def create_keyboard(self):
        """Создание клавиатуры после смены статуса"""
        kbrd = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kbrd.row(types.KeyboardButton(text="Очередь"), types.KeyboardButton(text="Обо мне"))
        return kbrd

    def show_pings_in_queue(self):
        """Показывает пинги по продуктам"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        max_by_department_group_sql = f"SELECT max(datediff(ss, ap.date_created, getdate())) " \
                                      f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                                      f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
                                      f"  AND uop.direction = 'response' " \
                                      f"JOIN UKSTGBot.dbo.ActivePings as ap with(nolock) ON ap.product_id = uop.product_id " \
                                      f"WHERE ap.date_answered IS NULL " \
                                      f"  AND ap.comment <> '' "
        max_ping_queue_time = sqlserver_cursor.execute(max_by_department_group_sql).fetchone()[0]
        sql = f"SELECT DISTINCT p.product_name, ap.ping_id, maxpt.maxpt " \
              f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
              f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
              f"  AND uop.direction = 'response' " \
              f"JOIN UKSTGBot.dbo.ActivePings as ap with(nolock) ON ap.product_id = uop.product_id " \
              f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = ap.product_id " \
              f"JOIN (SELECT product_id, max(datediff(ss, date_created, getdate())) as maxpt " \
              f"      FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"      WHERE date_answered is null " \
              f"        AND comment <> '' " \
              f"      GROUP BY product_id ) as maxpt on maxpt.product_id = p.product_id " \
              f"WHERE ap.date_answered IS NULL " \
              f"  AND ap.comment <> '' " \
              f"ORDER BY 1,2"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) == 0:
            return "Пингов в очереди нет..."
        else:
            answer = f"Всего пингов: {len(result)}\n" \
                     f"Макс. ⏱ по всем продуктам = {time.strftime('%H:%M:%S', time.gmtime(max_ping_queue_time))}\n\n"
            pings_list = []
            current_product = result[0][0]
            current_max_ping_queue_time = result[0][2]
            for product_data in result:
                if product_data[0] == current_product:
                    pings_list.append(str(product_data[1]))
                    if product_data[2] > current_max_ping_queue_time:
                        current_max_ping_queue_time = product_data[2]
                else:
                    answer += f"{current_product} | {' , '.join(pings_list) if len(pings_list) > 1 else pings_list[0]} | Макс. ⏱ = {time.strftime('%H:%M:%S', time.gmtime(current_max_ping_queue_time))}\n"
                    pings_list.clear()
                    current_product = product_data[0]
                    current_max_ping_queue_time = product_data[2]
                    pings_list.append(str(product_data[1]))
            answer += f"{current_product} | " \
                      f"{' , '.join(pings_list) if len(pings_list) > 1 else pings_list[0]} | " \
                      f"Макс. ⏱ = {time.strftime('%H:%M:%S', time.gmtime(current_max_ping_queue_time))}\n"
        return answer
