import datetime
import time
import pyodbc
from Ping import Ping

from telebot import types

from Settings import CONNECTION_STRING


class Responser(object):
    """Класс, который будет отвечать за работу с отвечающими"""
    user_id = None
    state_id = None
    state_name = None
    fullname = None
    department = 0
    role = ''
    inactive_time = 0
    time_zone = 0
    products = dict()
    answers = 0
    change_state_datetime = ''
    shift = ''

    @staticmethod
    def is_responser(user_id):
        """Проверка на причастность к пингующим"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT u.user_id " \
              f"FROM UKSTGBot.dbo.Users u with(nolock) " \
              f"JOIN UKSTGBot.dbo.Callider c with(nolock) on c.userlogin = u.userlogin " \
              f"WHERE u.user_id = {user_id} " \
              f"  AND u.can_response = 1 " \
              f"  AND u.is_block = 0 " \
              f"  AND c.fired = 0 " \
              f"  AND c.role in (3,4,7,8,9)"
        return sqlserver_cursor.execute(sql).fetchone() is not None

    @staticmethod
    def add_product(user_id, product_id):
        """Добавить продукт пользователю. Возвращает bool"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql_check_product = f"SELECT count(*) " \
                            f"FROM UKSTGBot.dbo.Products with(nolock) " \
                            f"WHERE product_id = {product_id}"
        if sqlserver_cursor.execute(sql_check_product).fetchone() is not None:
            sql_check = f"SELECT DISTINCT user_id " \
                        f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                        f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
                        f"JOIN UKSTGBot.dbo.Departments as d with(nolock) ON d.department_name = c.department " \
                        f"JOIN UKSTGBot.dbo.DepartmentProducts as dp with(nolock) ON dp.department_id = d.department_id " \
                        f"WHERE user_id = {user_id} " \
                        f"  AND product_id = {product_id} " \
                        f"UNION " \
                        f"SELECT DISTINCT user_id " \
                        f"FROM UKSTGBot.dbo.UserOptionalProducts with(nolock) " \
                        f"WHERE user_id = {user_id} " \
                        f"  AND product_id = {product_id} "
            if sqlserver_cursor.execute(sql_check).fetchone() is None:
                sql = f"INSERT INTO UKSTGBot.dbo.UserOptionalProducts (user_id, product_id) " \
                      f"VALUES ({user_id}, {product_id})"
                sqlserver_cursor.execute(sql)
                sqlserver_db.commit()
                return True
        return False

    @staticmethod
    def delete_product(user_id, product_id):
        """Удалить продукт у пользователя. Возвращает bool"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql_delete_product = f"DELETE FROM UKSTGBot.dbo.UserOptionalProducts " \
                             f"WHERE product_id = {product_id} " \
                             f"  AND user_id = {user_id}"
        sqlserver_cursor.execute(sql_delete_product)
        sqlserver_db.commit()
        return True

    def __init__(self, responser_id):
        """Констурктор"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT DISTINCT ud.user_id " \
              f"  , ud.responser_state_id " \
              f"  , rs.state_name " \
              f"  , c.fullname " \
              f"  , ur.role_name " \
              f"  , c.department " \
              f"  , d.time_zone " \
              f"  , p.product_id " \
              f"  , p.product_name " \
              f"  , ud.change_state_last_date " \
              f"  , case " \
              f"  when convert(datetime2(0), isnull(ap.last_close_dt, convert(datetime2(0), convert(date,getdate())))) <= convert(datetime2(0), convert(date,getdate())) " \
              f"  then convert(datetime2(0), convert(date,getdate())) " \
              f"  else convert(datetime2(0), ap.last_close_dt) end " \
              f"  , concat(convert(time(0), cs.start_date), ' - ', convert(time(0), cs.end_date)) " \
              f"  , uop.priority " \
              f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
              f"LEFT JOIN (" \
              f"  SELECT responser_id, max(date_closed) as last_close_dt " \
              f"  FROM UKSTGBot.dbo.ArchivePings with(nolock) " \
              f"  WHERE responser_id = {responser_id} " \
              f"  GROUP BY responser_id ) as ap ON ap.responser_id = ud.user_id " \
              f"JOIN UKSTGBot.dbo.ResponserStates as rs with(nolock) ON rs.state_id = ud.responser_state_id " \
              f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
              f"JOIN UKSTGBot.dbo.Departments as d with(nolock) ON d.department_name = c.department " \
              f"JOIN UKSTGBot.dbo.UserRoles as ur with(nolock) ON ur.role_id = c.role " \
              f"LEFT JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
              f"  AND uop.direction = 'response' " \
              f"LEFT JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = uop.product_id " \
              f"LEFT JOIN UKSTGBot.dbo.CalliderShifts cs with(nolock) ON cs.callider_id = c.callider_id " \
              f"  AND convert(date, getdate()) = convert(date, cs.start_date) " \
              f"WHERE ud.user_id = {responser_id}"
        result = sqlserver_cursor.execute(sql).fetchall()
        self.user_id = result[0][0]
        self.state_id = result[0][1]
        self.state_name = result[0][2]
        self.fullname = result[0][3]
        self.role = result[0][4]
        self.department = result[0][5]
        self.inactive_time = int((datetime.datetime.now() - datetime.datetime.strptime(str(result[0][10]), '%Y-%m-%d %H:%M:%S')).total_seconds()//60)
        self.time_zone = result[0][6]
        self.products = dict()
        self.change_state_datetime = result[0][9]
        self.shift = result[0][11]
        for data in result:
            if data[6] is not None:
                self.products.setdefault(data[7], data[8])
        self.answers = self.count_answers()

    def to_str(self):
        """Вывести информацию по отвечающему"""
        info = ""
        for product in self.products.values():
            info += f"{product} , "
        return f"ID : {self.user_id}\nФИО : {self.fullname}\nОтдел : {self.department}\n" \
               f"Роль : {self.role}\nСмена : {self.shift} (Мск+2)\nНе отвечал уже : {self.inactive_time} мин.\n" \
               f"Статус : {self.state_name}\nДата смены статуса : {self.change_state_datetime}\n" \
               f"Продукты : {info[:-2]}"

    def check_responser_state(self):
        """Проверка статуса отвечающиего"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT rs.state_name " \
              f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
              f"JOIN UKSTGBot.dbo.ResponserStates as rs with(nolock) ON rs.state_id = ud.responser_state_id " \
              f"WHERE ud.user_id={self.user_id}"
        return sqlserver_cursor.execute(sql).fetchone()[0]

    def switch_state(self):
        """Поменять статус отвечающего. Возвращает bool"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        if self.state_id == 0:
            new_state_id = 1
            self.close_all_active_pings()
        else:
            new_state_id = 0

        sql = f"UPDATE UKSTGBot.dbo.Users " \
              f"SET responser_state_id = {new_state_id}" \
              f"  , change_state_last_date = getdate() " \
              f"WHERE user_id={self.user_id}"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    def count_answers(self):
        """Считает количество Закрытых пингов за текущий день"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT count(*) " \
              f"FROM UKSTGBot.dbo.ArchivePings with(nolock)" \
              f"WHERE responser_id = {self.user_id} " \
              f"  AND ping_state_id = 4 " \
              f"  AND convert(date, date_answered) = convert(date, getdate())"
        return sqlserver_cursor.execute(sql).fetchone()[0]

    def update_answer_last_date(self):
        """Обновить время последнего ответа на пинг"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.Users " \
              f"SET answer_last_date = getdate() " \
              f"WHERE user_id = {self.user_id}"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    def create_keyboard(self, change_responser_state=0):
        """Создание клавиатуры после смены статуса"""
        green_state_btn = types.KeyboardButton(text="Сменить статус 🟢")
        red_state_btn = types.KeyboardButton(text="Сменить статус 🔴")

        kbrd = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kbrd.row(types.KeyboardButton(text="Очередь"), types.KeyboardButton(text="Отвечающие"))
        if change_responser_state == 1:
            kbrd.row(red_state_btn, types.KeyboardButton(text="Взять еще пинг"))
        elif self.check_responser_state() == "Зеленый":
            kbrd.row(green_state_btn, types.KeyboardButton(text="Взять еще пинг"))
        else:
            kbrd.row(red_state_btn, types.KeyboardButton(text="Взять еще пинг"))
        kbrd.row(types.KeyboardButton(text="Администрирование"), types.KeyboardButton(text="Обо мне"))
        return kbrd

    def create_commands_keyboard(self):
        """Создание клавиатуры для Администрирования"""
        kbrd = types.InlineKeyboardMarkup()
        kbrd.row(types.InlineKeyboardButton(text="Продуктовая", callback_data=f"products"))
        kbrd.row(types.InlineKeyboardButton(text="Помогаторская", callback_data=f"helpers"))
        kbrd.row(types.InlineKeyboardButton(text="Спасательская", callback_data=f"rescuers"))
        kbrd.row(types.InlineKeyboardButton(text="Сменить отдел", callback_data=f"change_department"))
        kbrd.row(types.InlineKeyboardButton(text="Закрыть", callback_data=f"close_menu"))
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
                                      f"WHERE ud.user_id = {self.user_id} " \
                                      f"  AND ap.date_answered IS NULL " \
                                      f"  AND ap.comment <> '' "
        max_ping_queue_time = sqlserver_cursor.execute(max_by_department_group_sql).fetchone()[0]
        sql = f"SELECT p.product_name, ap.ping_id, maxpt.maxpt " \
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
              f"WHERE ud.user_id = {self.user_id} " \
              f"  AND ap.date_answered IS NULL " \
              f"  AND ap.comment <> '' " \
              f"ORDER BY 1,2"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) == 0:
            return "Пингов в очереди нет..."
        else:
            answer = f"Всего пингов: {len(result)}\n" \
                     f"Макс. ⏱ по всем твоим продуктам = {time.strftime('%H:%M:%S', time.gmtime(max_ping_queue_time))}\n\n"
            pings_list = []
            current_product = result[0][0]
            current_max_ping_queue_time = result[0][2]
            for product_data in result:
                if product_data[0] == current_product:
                    pings_list.append(str(product_data[1]))
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

    def close_all_active_pings(self):
        """Закрыть все активные пинги, если отвечающий переходит из Красного в Зеленый"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT ping_id " \
              f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"WHERE responser_id = {self.user_id} " \
              f"  AND in_work = 1"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) > 0:
            for ping_id in result:
                ping = Ping()
                ping.fill_active_ping(ping_id[0])
                ping.update_ping_state(4)
                ping.close()
        return True

    def get_products_by_action(self, action, user_id):
        """Получить клавиатуру со списком продуктов, которые есть у отвечающего"""
        products = []
        kbrd = types.InlineKeyboardMarkup()
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        if action == "add_product":
            call_action = "add_prod"
            sql = f"SELECT p.product_id, p.product_name, '' " \
                  f"FROM UKSTGBot.dbo.Products as p with(nolock) " \
                  f"WHERE p.product_id not in ( " \
                  f"  SELECT p.product_id " \
                  f"  FROM UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) " \
                  f"  JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = uop.product_id " \
                  f"  WHERE uop.user_id = {user_id} " \
                  f"    AND uop.direction = 'response') " \
                  f"  AND p.is_active = 1 " \
                  f"ORDER BY 2"
        else:
            sql = f"SELECT p.product_id, p.product_name, uop.priority " \
                  f"FROM UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) " \
                  f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = uop.product_id " \
                  f"WHERE uop.user_id = {user_id} " \
                  f"  AND uop.direction = 'response' " \
                  f"ORDER BY 2"
            if action == "remove_product":
                call_action = "rem_prod"
                user_id = self.user_id
            elif action == "chng_prod_prior":
                call_action = "ch_pr_pr"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) > 0:
            for product in result:
                products.append(types.InlineKeyboardButton(text=f"{product[1]} {'('+str(product[2])+')' if product[2] != '' else ''}", callback_data=f"{call_action};{user_id};{product[0]};response"))
            while len(products) > 0:
                if len(products) / 2 >= 1:
                    kbrd.row(products.pop(0), products.pop(0))
                else:
                    kbrd.row(products.pop(0))
        kbrd.row(types.InlineKeyboardButton(text="Закрыть", callback_data="close_menu"))
        return kbrd

    def get_staff_by_action(self, action):
        """Получить список сотрудников отдела отвечающего, которым нужно добавить продукт"""
        kbrd = types.InlineKeyboardMarkup()
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        if action.endswith("product"):
            if action in ["helper_add_product", "helper_remove_product"]:
                sql = f"SELECT ud.user_id, c.fullname " \
                      f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                      f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin=ud.userlogin " \
                      f"WHERE c.department = ( " \
                      f"  SELECT c.department " \
                      f"  FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                      f"  JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin=ud.userlogin " \
                      f"  WHERE ud.user_id={self.user_id}) " \
                      f"  AND c.profession in ('Консультант ', 'Специалист', 'Ведущий специалист', 'Главный специалист') " \
                      f"  AND ud.is_block = 0 " \
                      f"  AND ud.can_response = 1 " \
                      f"ORDER BY c.fullname"
                if action == "helper_add_product":
                    call_action = "hlpr_to_add_prod"
                elif action == "helper_remove_product":
                    call_action = "hlpr_to_rem_prod"
            else:
                sql = f"SELECT ud.user_id, c.fullname " \
                      f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                      f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin=ud.userlogin " \
                      f"WHERE c.department = ( " \
                      f"  SELECT c.department " \
                      f"  FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                      f"  JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin=ud.userlogin " \
                      f"  WHERE ud.user_id={self.user_id}) " \
                      f"  AND c.profession in ('Стажер', 'Консультант ', 'Специалист', 'Ведущий специалист', 'Главный специалист') " \
                      f"  AND ud.is_block = 0 " \
                      f"ORDER BY c.fullname"
                if action == "add_product":
                    call_action = "user_to_add_prod"
                elif action == "remove_product":
                    call_action = "user_to_rem_prod"
        elif action.endswith("helper"):
            if action == "call_helper":
                call_action = "call_helper"
                sql = f"SELECT isnull(ud.user_id, 0) as user_id, c.fullname " \
                      f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                      f"RIGHT JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin=ud.userlogin " \
                      f"WHERE c.department = ( " \
                      f"  SELECT c.department " \
                      f"  FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                      f"  JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin=ud.userlogin " \
                      f"  WHERE ud.user_id={self.user_id}) " \
                      f"  AND ud.can_response = 0 " \
                      f"  AND c.role = 5 " \
                      f"  AND ud.is_block = 0"
            elif action == "recall_helper":
                 call_action = "recall_helper"
                 sql = f"SELECT ud.user_id, c.fullname " \
                       f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                       f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin=ud.userlogin " \
                       f"WHERE c.department = ( " \
                       f"  SELECT c.department " \
                       f"  FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                       f"  JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin=ud.userlogin " \
                       f"  WHERE ud.user_id={self.user_id}) " \
                       f"  AND ud.can_response = 1 " \
                       f"  AND c.role = 7 " \
                       f"  AND ud.is_block = 0"
        elif action == "rescue":
            call_action = "rescue"
            sql = f"SELECT ud.user_id, c.fullname " \
                  f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                  f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin=ud.userlogin " \
                  f"WHERE c.department = ( " \
                  f"  SELECT c.department " \
                  f"  FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                  f"  JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin=ud.userlogin " \
                  f"  WHERE ud.user_id={self.user_id}) " \
                  f"  AND ud.has_started_ping = 1 " \
                  f"  AND ud.is_block = 0 "
        else:
            if action.startswith("chng_prod_prior"):
                call_action = "change_prior_1"
                sql = f"SELECT ud.user_id, c.fullname " \
                      f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                      f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
                      f"WHERE c.department = ( " \
                      f"  SELECT c.department " \
                      f"  FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                      f"  JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
                      f"  WHERE ud.user_id = {self.user_id}) " \
                      f"  AND ud.can_response = 1 " \
                      f"  AND c.role in (2,3,4,7) " \
                      f"  AND ud.is_block = 0 " \
                      f"  AND ud.user_id <> {self.user_id}"
        result = sqlserver_cursor.execute(sql).fetchall()

        if len(result) > 0:
            for user in sorted(result, key=lambda res: res[1]):
                kbrd.row(types.InlineKeyboardButton(text=f"{user[1]}", callback_data=f"{call_action};{user[0]}"))
        kbrd.row(types.InlineKeyboardButton(text="Закрыть", callback_data="close_menu"))
        return kbrd
