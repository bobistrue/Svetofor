import pyodbc
import datetime
import time

from telebot import types

from Ping import Ping
from Responser import Responser
from Requester import Requester
from Spectator import Spectator

from Settings import CONNECTION_STRING


class Helper(object):
    """Класс, который будет отвечать за почти все """

    @staticmethod
    def auth(user_id):
        """Проверка на то, что пользователь есть в БД"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT u.user_id " \
              f"FROM UKSTGBot.dbo.Users u with(nolock) " \
              f"JOIN UKSTGBot.dbo.Callider c with(nolock) on c.userlogin = u.userlogin " \
              f"WHERE u.user_id = {user_id} " \
              f"  AND u.is_block = 0 " \
              f"  AND c.fired = 0"
        return sqlserver_cursor.execute(sql).fetchone() is not None

    @staticmethod
    def is_exist_login(login):
        """Вернуть сотрудника, если есть такой LOGIN"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT 1 " \
              f"FROM UKSTGBot.dbo.Callider with(nolock) " \
              f"WHERE userlogin = '{login}' " \
              f"  AND fired = 0"
        sql_check = f"SELECT u.user_id " \
                    f"FROM UKSTGBot.dbo.Callider as c with(nolock) " \
                    f"JOIN UKSTGBot.dbo.Users as u with(nolock) ON u.userlogin = c.userlogin " \
                    f"WHERE c.userlogin = '{login}' " \
                    f"  AND u.is_block = 0 " \
                    f"  AND c.fired = 0"
        return sqlserver_cursor.execute(sql).fetchone() is not None \
               and sqlserver_cursor.execute(sql_check).fetchone() is None

    @staticmethod
    def write_log(object_id, subject_id, action):
        """Сделать запись в логе о действии"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"INSERT INTO UKSTGBot.dbo.Logs (object_id, subject_id, action, action_datetime) " \
              f"VALUES ({object_id}, {subject_id}, '{action}', getdate()) "
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    @staticmethod
    def get_from_flag_name(from_flag_id):
        """Получить название флага пинга"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT flag_name " \
              f"FROM UKSTGBot.dbo.FromFlag " \
              f"WHERE flag_id = {from_flag_id}"
        return sqlserver_cursor.execute(sql).fetchone()[0]

    @staticmethod
    def get_all_users_id(can_response):
        """Получить user_id всех пользователей"""
        users_id = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT user_id " \
              f"FROM UKSTGBot.dbo.Users " \
              f"WHERE is_block = 0 " \
              f"  AND can_response = {can_response} " \
              f"ORDER BY 1"
        for user_id in sqlserver_cursor.execute(sql).fetchall():
            users_id.append(user_id[0])
        return users_id

    @staticmethod
    def get_rare_products():
        """Получить Редкие продукты для Экстерна"""
        products = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT product_id " \
              f"FROM UKSTGBot.dbo.Products with(nolock) " \
              f"WHERE product_id BETWEEN 601 AND 650 " \
              f"ORDER BY 1"
        for user_id in sqlserver_cursor.execute(sql).fetchall():
            products.append(user_id[0])
        return products


    @staticmethod
    def get_last_ping_without_comment(user_id):
        """Получить последний пинг, в котором нет комментария"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT TOP 1 ping_id " \
              f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"WHERE requester_id = {user_id} " \
              f"  AND comment IS NULL " \
              f"ORDER BY ping_id DESC"
        ping = sqlserver_cursor.execute(sql)
        if ping is not None:
            return ping.fetchone()[0]
        return None

    @staticmethod
    def add_new_user(user_id, login):
        """Добавить нового пользователя"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT userlogin" \
              f"  , callider_department" \
              f"  , callider_profession " \
              f"FROM UKSTGBot.dbo.Callider with(nolock) " \
              f"WHERE userlogin = '{login}' " \
              f"  AND fired = 0"
        userlogin, department, profession = sqlserver_cursor.execute(sql).fetchone()
        sql_insert = f"INSERT INTO UKSTGBot.dbo.Users " \
                     f"(user_id, userlogin, can_response, responser_state_id, has_started_ping, was_notification, " \
                     f"change_state_last_date, answer_last_date, notified_date) " \
                     f"VALUES " \
                     f"({user_id}, '{userlogin}', 0, 0, 0, 0, '', '', '')"
        sqlserver_cursor.execute(sql_insert)
        sql_update = f"UPDATE UKSTGBot.dbo.Callider " \
                     f"SET role = case when profession like '%уководитель%' then 1 " \
                     f"                when profession like '%ксперт%' then 3 " \
                     f"                when profession like '%ентор%' then 4 " \
                     f"                when profession like '%тажер%' then 6 " \
                     f"                else 5 end " \
                     f"WHERE userlogin = '{login}'"
        sqlserver_cursor.execute(sql_update)
        sql_update = f"UPDATE u " \
                     f"SET u.is_spectator = case when c.role in (1,2)  then 1 " \
                     f"                          else 0 end " \
                     f"  , u.can_response = case when c.role in (3,4) then 1 " \
                     f"                          else 0 end " \
                     f"FROM UKSTGBot.dbo.Callider c " \
                     f"JOIN UKSTGBot.dbo.Users u on u.userlogin = c.userlogin " \
                     f"WHERE c.userlogin = '{login}'"
        sqlserver_cursor.execute(sql_update)
        sqlserver_db.commit()

    @staticmethod
    def add_product_to_user(user_id, product_id, direction):
        """Добавить продукт указанному пользователю"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"INSERT INTO UKSTGBot.dbo.UserOptionalProducts " \
              f"(user_id, product_id, direction, priority, was_notification) " \
              f"VALUES ({user_id}, {product_id}, '{direction}', 5, 0)"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    @staticmethod
    def add_products_to_helper(user_id):
        """Добавить продукты помогатору после призыва"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"INSERT INTO UKSTGBot.dbo.UserOptionalProducts (user_id, product_id, direction, priority, was_notification) " \
              f"SELECT u.user_id, dp.product_id, 'response', 1, 0 " \
              f"FROM UKSTGBot.dbo.Users as u with(nolock)" \
              f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = u.userlogin " \
              f"JOIN UKSTGBot.dbo.Departments as d with(nolock) ON d.department_name = c.department " \
              f"JOIN UKSTGBot.dbo.DepartmentProducts as dp with(nolock) ON dp.department_id = d.department_id " \
              f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = dp.product_id " \
              f"WHERE p.for_helper = 1 " \
              f"  AND u.user_id = {user_id} " \
              f"  AND c.fired = 0 " \
              f"  AND p.is_active = 1 "
        sql2 = f"UPDATE UKSTGBot.dbo.Users " \
               f"SET notification_alert_state = 1 " \
               f"WHERE user_id = {user_id}"
        sqlserver_cursor.execute(sql)
        sqlserver_cursor.execute(sql2)
        sqlserver_db.commit()

    @staticmethod
    def remove_product_from_user(user_id, product_id, direction):
        """Удалить продукт у указанного пользователя"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"DELETE FROM UKSTGBot.dbo.UserOptionalProducts " \
              f"WHERE user_id = {user_id} " \
              f"  AND product_id = {product_id} " \
              f"  AND direction = '{direction}'"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    @staticmethod
    def remove_products_to_helper(user_id):
        """Добавить продукты помогатору после призыва"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"DELETE FROM UKSTGBot.dbo.UserOptionalProducts " \
              f"WHERE user_id = {user_id} " \
              f"  AND direction = 'response'"
        sql2 = f"UPDATE UKSTGBot.dbo.Users " \
               f"SET notification_alert_state = 0 " \
               f"WHERE user_id = {user_id}"
        sqlserver_cursor.execute(sql)
        sqlserver_cursor.execute(sql2)
        sqlserver_db.commit()

    @staticmethod
    def check_active_responser_by_products(product_id, requester_id):
        """Проверить наличие смен у отвечающих с такими продуктами. Для менторов идет проверка на отдел."""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        if product_id in Helper.get_mentor_products():
            sql = f"SELECT 1 " \
                  f"FROM UKSTGBot.dbo.Callider as c with(nolock) " \
                  f"JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
                  f"  AND getdate() BETWEEN cs.start_date AND cs.end_date " \
                  f"JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.userlogin = c.userlogin " \
                  f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
                  f"WHERE uop.product_id = {product_id} " \
                  f"  AND uop.direction = 'response' " \
                  f"  AND ud.is_block = 0 " \
                  f"  AND ud.can_response = 1 " \
                  f"  AND c.fired = 0 " \
                  f"  AND c.department = (SELECT department " \
                  f"                      FROM UKSTGBot.dbo.Users u with(nolock) " \
                  f"                      JOIN UKSTGBot.dbo.Callider c with(nolock) on c.userlogin = u.userlogin " \
                  f"                      WHERE c.user_id = {requester_id}) "
        else:
            sql = f"SELECT 1 " \
                  f"FROM UKSTGBot.dbo.Callider as c with(nolock) " \
                  f"JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
                  f"  AND getdate() BETWEEN cs.start_date AND cs.end_date " \
                  f"JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.userlogin = c.userlogin " \
                  f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
                  f"WHERE uop.product_id = {product_id} " \
                  f"  AND uop.direction = 'response' " \
                  f"  AND ud.is_block = 0 " \
                  f"  AND ud.can_response = 1 " \
                  f"  AND c.fired = 0"
        return sqlserver_cursor.execute(sql).fetchone() is not None

    @staticmethod
    def get_pings_by_incident(incident_number):
        """Все пинги в течение месяца по номеру инцидента"""
        pings = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT req.fullname " \
              f"  , res.fullname " \
              f"  , convert(datetime2(0), ap.date_created) " \
              f"  , convert(datetime2(0), ap.date_sent) " \
              f"  , s.section_name " \
              f"  , p.product_name " \
              f"  , ps.state_name " \
              f"  , ap.ping_id " \
              f"  , ap.comment " \
              f"  , convert(datetime2(0), ap.date_closed) " \
              f"FROM UKSTGBot.dbo.ArchivePings as ap with(nolock) " \
              f"JOIN UKSTGBot.dbo.Sections as s with(nolock) on s.section_id = ap.section_id " \
              f"JOIN UKSTGBot.dbo.Products as p with(nolock) on p.product_id = ap.product_id " \
              f"JOIN UKSTGBot.dbo.PingStates as ps with(nolock) on ps.state_id = ap.ping_state_id " \
              f"JOIN UKSTGBot.dbo.Users as requ with(nolock) ON requ.user_id = ap.requester_id " \
              f"JOIN UKSTGBot.dbo.Callider as req with(nolock) ON req.userlogin = requ.userlogin " \
              f"LEFT JOIN UKSTGBot.dbo.Users as resu with(nolock) ON resu.user_id = ap.responser_id " \
              f"LEFT JOIN UKSTGBot.dbo.Callider as res with(nolock) ON res.userlogin = resu.userlogin " \
              f"WHERE substring(ap.comment, 1, 8) = '{incident_number}' " \
              f"  AND datediff(mi, ap.date_created, getdate()) <= 60*24*30 " \
              f"UNION " \
              f"SELECT req.fullname " \
              f"  , res.fullname " \
              f"  , convert(datetime2(0), ap.date_created) " \
              f"  , convert(datetime2(0), ap.date_sent) " \
              f"  , s.section_name " \
              f"  , p.product_name " \
              f"  , ps.state_name " \
              f"  , ap.ping_id " \
              f"  , ap.comment " \
              f"  , convert(datetime2(0), ap.date_closed) " \
              f"FROM UKSTGBot.dbo.ActivePings as ap with(nolock) " \
              f"JOIN UKSTGBot.dbo.Sections as s with(nolock) on s.section_id = ap.section_id " \
              f"JOIN UKSTGBot.dbo.Products as p with(nolock) on p.product_id = ap.product_id " \
              f"JOIN UKSTGBot.dbo.PingStates as ps with(nolock) on ps.state_id = ap.ping_state_id " \
              f"JOIN UKSTGBot.dbo.Users as requ with(nolock) ON requ.user_id = ap.requester_id " \
              f"JOIN UKSTGBot.dbo.Callider as req with(nolock) ON req.userlogin = requ.userlogin " \
              f"LEFT JOIN UKSTGBot.dbo.Users as resu with(nolock) ON resu.user_id = ap.responser_id " \
              f"LEFT JOIN UKSTGBot.dbo.Callider as res with(nolock) ON res.userlogin = resu.userlogin " \
              f"WHERE substring(ap.comment, 1, 8) = '{incident_number}' " \
              f"ORDER BY convert(datetime2(0), ap.date_created) " \
              f"  , convert(datetime2(0), ap.date_sent) "
        pings_raw = sqlserver_cursor.execute(sql).fetchall()
        for ping in pings_raw:
            pings.append([ping[0], ping[1], ping[2], ping[3], ping[4], ping[5], ping[6], ping[7], ping[8], ping[9]])

        if len(pings) > 0:
            incidents_data = []
            for result in pings:
                incidents_data.append(f"Пинг #s{result[7]}"
                                    f"\nРаздел {result[4]} по продукту {result[5]}"
                                    f"\nCтатус пинга {result[6]}"
                                    f"\nФИО пингующего {result[0]}"
                                    f"\nДата создания {result[2]}"
                                    f"\nДата отправки {result[3] if result[3] != None else 'не отправлен'}"
                                    f"\nДата закрытия {result[9] if result[9] != None else 'не закрыт'}"
                                    f"\nФИО отвечающего {result[1] if result[1] != None else 'не назначен'}\n"
                                    f"\nКоммент : {result[8]}")
        else:
            return [f"Пинги по инциденту {incident_number} не найдены"]
        return incidents_data

    @staticmethod
    def get_pings_by_requester_fullname(requester_fullname):
        """Найти все пинги за месяц от сотрудника"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT convert(datetime2(0), ap.date_created) " \
              f"  , convert(datetime2(0), ap.date_sent) " \
              f"  , ap.ping_id " \
              f"  , ap.comment " \
              f"  , s.section_name " \
              f"  , p.product_name " \
              f"  , res.fullname " \
              f"  , ps.state_name " \
              f"  , convert(datetime2(0), ap.date_closed) " \
              f"FROM UKSTGBot.dbo.ArchivePings as ap with(nolock) " \
              f"JOIN UKSTGBot.dbo.PingStates as ps with(nolock) on ps.state_id = ap.ping_state_id " \
              f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = ap.product_id " \
              f"JOIN UKSTGBot.dbo.Sections as s with(nolock) ON s.section_id = ap.section_id " \
              f"JOIN UKSTGBot.dbo.Users as requ with(nolock) ON requ.user_id = ap.requester_id " \
              f"JOIN UKSTGBot.dbo.Callider as req with(nolock) ON req.userlogin = requ.userlogin " \
              f"LEFT JOIN UKSTGBot.dbo.Users as resu with(nolock) ON resu.user_id = ap.responser_id " \
              f"LEFT JOIN UKSTGBot.dbo.Callider as res with(nolock) ON res.userlogin = resu.userlogin " \
              f"WHERE req.fullname LIKE '{requester_fullname}%' " \
              f"  AND convert(date, ap.date_created) = convert(date, getdate()) " \
              f"UNION " \
              f"SELECT convert(datetime2(0), ap.date_created) " \
              f"  , convert(datetime2(0), ap.date_sent) " \
              f"  , ap.ping_id " \
              f"  , ap.comment " \
              f"  , s.section_name " \
              f"  , p.product_name " \
              f"  , res.fullname " \
              f"  , ps.state_name " \
              f"  , convert(datetime2(0), ap.date_closed) " \
              f"FROM UKSTGBot.dbo.ActivePings as ap with(nolock) " \
              f"JOIN UKSTGBot.dbo.PingStates as ps with(nolock) on ps.state_id = ap.ping_state_id " \
              f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = ap.product_id " \
              f"JOIN UKSTGBot.dbo.Sections as s with(nolock) ON s.section_id = ap.section_id " \
              f"JOIN UKSTGBot.dbo.Users as requ with(nolock) ON requ.user_id = ap.requester_id " \
              f"JOIN UKSTGBot.dbo.Callider as req with(nolock) ON req.userlogin = requ.userlogin " \
              f"LEFT JOIN UKSTGBot.dbo.Users as resu with(nolock) ON resu.user_id = ap.responser_id " \
              f"LEFT JOIN UKSTGBot.dbo.Callider as res with(nolock) ON res.userlogin = resu.userlogin " \
              f"WHERE req.fullname LIKE '{requester_fullname}%' " \
              f"ORDER BY convert(datetime2(0), ap.date_created) " \
              f"  , convert(datetime2(0), ap.date_sent)"
        pings_raw = sqlserver_cursor.execute(sql).fetchall()
        pings = []
        print(pings_raw)
        if len(pings_raw) > 0:
            for ping in pings_raw:
                pings.append([ping[0], ping[1], ping[2], ping[3], ping[4], ping[5], ping[6], ping[7], ping[8]])

        pings_answer = []
        if len(pings) > 0:
            for result in pings:
                pings_answer.append(f"Пинг #s{result[2]}"
                             f"\nРаздел {result[4]} по продукту {result[5]}"
                             f"\nСтатус пинга {result[7]}"
                             f"\nДата создания {result[0]}"
                             f"\nДата отправки {result[1] if result[1] is not None else 'не отправлен'}"
                             f"\nДата закрытия {result[8] if result[8] is not None else 'не закрыт'}"
                             f"\nФИО отвечающего {result[6] if result[6] is not None else 'не назначен'}\n"
                             f"\nКоммент : {result[3]}")
        else:
            pings_answer.append(f"Пинги от {requester_fullname} не найдены")
            
        return pings_answer

    @staticmethod
    def get_pings_by_ping_id(ping_id):
        """Найти пинг по ping_id"""
        pings = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT ap.ping_id " \
              f"  , s.section_name " \
              f"  , p.product_name " \
              f"  , req.fullname " \
              f"  , ap.date_created " \
              f"  , ap.comment " \
              f"  , convert(datetime2(0), ap.date_sent) " \
              f"  , convert(datetime2(0), ap.date_answered) " \
              f"  , res.fullname " \
              f"  , ps.state_name " \
              f"  , convert(datetime2(0), ap.date_closed) " \
              f"FROM UKSTGBot.dbo.ActivePings as ap with(nolock) " \
              f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = ap.product_id " \
              f"JOIN UKSTGBot.dbo.Sections as s with(nolock) ON s.section_id = ap.section_id " \
              f"JOIN UKSTGBot.dbo.Users as requ with(nolock) ON requ.user_id = ap.requester_id " \
              f"JOIN UKSTGBot.dbo.Callider as req with(nolock) ON req.userlogin = requ.userlogin " \
              f"JOIN UKSTGBot.dbo.PingStates as ps with(nolock) ON ps.state_id = ap.ping_state_id " \
              f"LEFT JOIN UKSTGBot.dbo.Users as resu with(nolock) ON resu.user_id = ap.responser_id " \
              f"LEFT JOIN UKSTGBot.dbo.Callider as res with(nolock) ON res.userlogin = resu.userlogin " \
              f"WHERE convert(nvarchar(10), ap.ping_id) = '{ping_id}' " \
              f"UNION " \
              f"SELECT ap.ping_id " \
              f"  , s.section_name " \
              f"  , p.product_name " \
              f"  , req.fullname " \
              f"  , ap.date_created " \
              f"  , ap.comment " \
              f"  , convert(datetime2(0), ap.date_sent) " \
              f"  , convert(datetime2(0), ap.date_answered) " \
              f"  , res.fullname " \
              f"  , ps.state_name " \
              f"  , convert(datetime2(0), ap.date_closed) " \
              f"FROM UKSTGBot.dbo.ArchivePings as ap with(nolock) " \
              f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = ap.product_id " \
              f"JOIN UKSTGBot.dbo.Sections as s with(nolock) ON s.section_id = ap.section_id " \
              f"JOIN UKSTGBot.dbo.Users as requ with(nolock) ON requ.user_id = ap.requester_id " \
              f"JOIN UKSTGBot.dbo.Callider as req with(nolock) ON req.userlogin = requ.userlogin " \
              f"JOIN UKSTGBot.dbo.PingStates as ps with(nolock) ON ps.state_id = ap.ping_state_id " \
              f"LEFT JOIN UKSTGBot.dbo.Users as resu with(nolock) ON resu.user_id = ap.responser_id " \
              f"LEFT JOIN UKSTGBot.dbo.Callider as res with(nolock) ON res.userlogin = resu.userlogin " \
              f"WHERE convert(nvarchar(10), ap.ping_id) = '{ping_id}' " \
              f"ORDER BY 7"
        pings_raw = sqlserver_cursor.execute(sql).fetchall()
        if len(pings_raw) > 0:
            for ping in pings_raw:
                pings.append([ping[0], ping[1], ping[2], ping[3], ping[4], ping[5], ping[6], ping[7], ping[8], ping[9], ping[10]])

        if pings:
            pings_str = []
            if len(pings) > 1:
                pings_str.append(f"Пинг #s{pings[0][0]}"
                                 f"\nРаздел {pings[0][1]} по продукту {pings[0][2]}"
                                 f"\nТекущий статус пинга {pings[len(pings) - 1][9]}"
                                 f"\nФИО пингующего {pings[0][3]}"
                                 f"\nДата создания {pings[0][4]}"
                                 f"\nДата закрытия {pings[0][10] if pings[0][10] != None else 'еще не закрыт'}"
                                 f"\nКоммент : {pings[0][5]}\n\n"
                                 f"Отвечали:")
                for row in pings:
                    pings_str.append(f"Дата получения {row[6] if row[6] != None else 'не отправлен'}"
                                     f"\nДата ответа {row[7] if row[7] != None else 'не было ответа'}"
                                     f"\nСтатус пинга {row[9]}"
                                     f"\nФИО отвечающего {row[8] if row[8] != None else 'не назначен'}")
            else:
                pings_str.append(f"Пинг #s{pings[0][0]}"
                                 f"\nРаздел {pings[0][1]} по продукту {pings[0][2]}"
                                 f"\nСтатус пинга {pings[len(pings) - 1][9]}"
                                 f"\nФИО пингующего {pings[0][3]}"
                                 f"\nДата создания {pings[0][4]}"
                                 f"\nДата закрытия {pings[0][10] if pings[0][10] != None else 'еще не закрыт'}"
                                 f"\nКоммент : {pings[0][5]}\n"
                                 f"\nДата получения {pings[0][6] if pings[0][6] != None else 'не отправлен'}"
                                 f"\nДата ответа {pings[0][7] if pings[0][7] != None else 'не было ответа'}"
                                 f"\nФИО отвечающего {pings[0][8] if pings[0][8] != None else 'не назначен'}")
        else:
            return [f"Пинг {ping_id} не найден"]
        return pings_str

    @staticmethod
    def create_priority_keyboard(user_id, product_id):
        """Создать клавиатуру со шкалой для установки приоритета"""
        kbrd = types.InlineKeyboardMarkup()
        kbrd.row(*[types.InlineKeyboardButton(text=f"{i}", callback_data=f"set_new_pr;{i};{user_id};{product_id}") for i in range(1, 6)])
        return kbrd

    @staticmethod
    def get_product_priority(user_id, product_id):
        """Получить текущий приоритет продукта у пользователя"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT priority " \
              f"FROM UKSTGBot.dbo.UserOptionalProducts with(nolock) " \
              f"WHERE user_id = {user_id} " \
              f"  AND product_id = {product_id} " \
              f"  AND direction = 'response'"
        return sqlserver_cursor.execute(sql).fetchone()[0]

    @staticmethod
    def set_product_priority(new_priority, user_id, product_id):
        """Получить текущий приоритет продукта у пользователя"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.UserOptionalProducts " \
              f"SET priority = {new_priority} " \
              f"WHERE user_id = {user_id} " \
              f"  AND product_id = {product_id} " \
              f"  AND direction = 'response'"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    @staticmethod
    def create_departments_keyboard():
        """Клавитура для смены отдела"""
        kbrd = types.InlineKeyboardMarkup()
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT department_id" \
              f"  , department_name " \
              f"FROM UKSTGBot.dbo.Departments with(nolock) " \
              f"ORDER BY 2"
        for department in sqlserver_cursor.execute(sql).fetchall():
            kbrd.row(types.InlineKeyboardButton(text=f"{department[1]}", callback_data=f"new_dep;{department[0]}"))
        kbrd.row(types.InlineKeyboardButton(text=f"Закрыть меню", callback_data=f"close_menu"))
        return kbrd

    @staticmethod
    def set_new_department_to_user(user_id, department_id):
        """Установить новый отдел"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.Callider " \
              f"SET department = (SELECT department_name " \
              f"                  FROM UKSTGBot.dbo.Departments with(nolock) " \
              f"                  WHERE department_id = {department_id}) " \
              f"WHERE userlogin = (SELECT userlogin " \
              f"                   FROM UKSTGBot.dbo.Users with(nolock) " \
              f"                   WHERE user_id = {user_id} " \
              f"                     AND is_block = 0) "
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    @staticmethod
    def rescue_user(user_id):
        """Спасти пользовтеля (изменить параметр has_started_ping на 0)"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.Users " \
              f"SET has_started_ping = 0 " \
              f"WHERE user_id = {user_id}"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    @staticmethod
    def is_cons(user_id):
        """Проверка на то, что профессия вызывающего не консультантская. Возвращает bool"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT 1 " \
              f"FROM UKSTGBot.dbo.Callider as c with(nolock) " \
              f"JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.userlogin = c.userlogin " \
              f"WHERE ud.user_id = {user_id} " \
              f"  AND c.role in (5, 6, 7) " \
              f"  AND c.fired = 0"
        return sqlserver_cursor.execute(sql).fetchone() is not None

    @staticmethod
    def is_helper(user_id):
        """Проверка на то, что профессия вызывающего не консультантская. Возвращает bool"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT 1 " \
              f"FROM UKSTGBot.dbo.Callider as c with(nolock) " \
              f"JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.userlogin = c.userlogin " \
              f"WHERE ud.user_id = {user_id} " \
              f"  AND ud.can_response = 1 " \
              f"  AND c.role = 7 " \
              f"  AND c.fired = 0"
        return sqlserver_cursor.execute(sql).fetchone() is not None

    @staticmethod
    def is_expert_in_department(user_id):
        """Проверка на то, что профессия вызывающего не консультантская. Возвращает bool"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT 1 " \
              f"FROM UKSTGBot.dbo.Callider as c with(nolock) " \
              f"JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.userlogin = c.userlogin " \
              f"WHERE ud.user_id = {user_id} " \
              f"  AND ud.can_response = 1 " \
              f"  AND c.role = 3 " \
              f"  AND c.fired = 0"
        return sqlserver_cursor.execute(sql).fetchone() is not None

    @staticmethod
    def ping_in_queue():
        """Показывает есть ли хотя бы 1 пинг в очереди"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT count(*) " \
              f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"WHERE date_answered is null " \
              f"  AND comment <> ''"
        return sqlserver_cursor.execute(sql).fetchone()[0]

    @staticmethod
    def find_last_responser_by_incident(incident_number):
        """Пробует найти "Зеленого" отвечающего, который уже работал над этим инцидентом сегодня. Возвращает int"""
        if incident_number.isdigit():
            sqlserver_db = pyodbc.connect(CONNECTION_STRING)
            sqlserver_cursor = sqlserver_db.cursor()
            sql = f"SELECT TOP 1 ap.responser_id " \
                  f"FROM UKSTGBot.dbo.ArchivePings as ap with(nolock) " \
                  f"JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.user_id = ap.responser_id " \
                  f"WHERE ud.responser_state_id = 1 " \
                  f"  AND ap.comment like '{incident_number}%' " \
                  f"  AND ap.ping_state_id = 4 " \
                  f"  AND ap.date_answered <= getdate() " \
                  f"  AND u.is_block = 0 " \
                  f"ORDER BY date_closed DESC "
            result = sqlserver_cursor.execute(sql).fetchone()
            if result is not None:
                return result[0]
        return 0

    @staticmethod
    def active_responsers():
        """Проверка на то, что есть работающие отвечающие. Возвращает bool"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT count(*) " \
              f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
              f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
              f"WHERE ud.can_response = 1 " \
              f"  AND ud.responser_state_id = 1 " \
              f"  AND ud.is_block = 0 " \
              f"  AND uop.direction = 'response' "
        return sqlserver_cursor.execute(sql).fetchone()[0]

    # ЕЩЕ АКУТАЛЬНО?
    @staticmethod
    def update_product_moving_log(who, whom, product_id, action, direction):
        """Занести в лог данные об добавлении/удалении продукта отвечающим"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"INSERT INTO UKSTGBot.dbo.ProductMovingLog " \
              f"VALUES ({who},{whom},{product_id},'{action}','{direction}',getdate())"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    @staticmethod
    def not_route_user(user_id):
        """Проверить что пингующий не должен маршрутизироваться"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT user_id " \
              f"FROM UKSTGBot.dbo.NotRouteUsers with(nolock) " \
              f"WHERE user_id = {user_id}"
        return sqlserver_cursor.execute(sql).fetchone() is not None

    @staticmethod
    def get_product_queue(product_id):
        """Показать очередь по продукту"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT count(*) " \
              f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"WHERE product_id = {product_id} " \
              f"  AND date_answered is null " \
              f"  AND comment <> ''"
        return sqlserver_cursor.execute(sql).fetchone()[0]

    @staticmethod
    def get_mentor_products():
        """Получить список product_id менторов"""
        products_id = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT product_id " \
              f"FROM UKSTGBot.dbo.Products with(nolock) " \
              f"WHERE for_mentor = 1"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) > 0:
            products_id = [product_id[0] for product_id in result]
        return products_id

    @staticmethod
    def get_departments_by_requester(department):
        """Найти группу для распределения пингов"""
        departments = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT department_name " \
              f"FROM UKSTGBot.dbo.Departments with(nolock) " \
              f"WHERE group_id = ( " \
              f"  SELECT distinct CASE " \
              f"  WHEN '{department}' like '%УЦ%' then 1 " \
              f"  WHEN '{department}' like '%Экстерн%' then 2 " \
              f"  WHEN '{department}' like '%Диадок%' then 3 " \
              f"  WHEN '{department}' like '%ФМС%' then 4 " \
              f"  WHEN '{department}' like '%Эльба%' then 5 " \
              f"  WHEN '{department}' like '%Бухгалтерия%' then 6 " \
              f"  WHEN '{department}' like '%Маркет%' then 7 " \
              f"  WHEN '{department}' like '%Ритейл%' then 8 " \
              f"  WHEN '{department}' like '%ОФД%' then 9 " \
              f"  WHEN '{department}' like '%отдел%' then 0 " \
              f"  ELSE -1 END " \
              f"  FROM UKSTGBot.dbo.Departments with(nolock) )"
        result = sqlserver_cursor.execute(sql).fetchall()
        for department in result:
            departments.append(department[0])
        return departments

    @staticmethod
    def find_own_mentor(requester_id):
        """Проверить есть свободен ли сейчас ментор сотрудника"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT user_id " \
              f"FROM UKSTGBot.dbo.Users as res_u with(nolock) " \
              f"JOIN UKSTGBot.dbo.Callider as res_c with(nolock) ON res_c.userlogin = res_u.userlogin " \
              f"JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = res_c.callider_id " \
              f"WHERE res_c.fullname = (SELECT c.supervisor " \
              f"                        FROM UKSTGBot.dbo.Users as u with(nolock) " \
              f"                        JOIN UKSTGBot.dbo.Callider as c with(nolock) on c.userlogin = u.userlogin " \
              f"                        WHERE u.user_id = {requester_id}) " \
              f"  AND res_u.can_response = 1 " \
              f"  AND res_u.responser_state_id = 1 " \
              f"  AND res_u.is_block = 0 " \
              f"  AND getdate() BETWEEN cs.start_date AND cs.end_date " \
              f"  AND res_c.fired = 0"
        result = sqlserver_cursor.execute(sql).fetchone()
        if result is not None:
            return Responser(result[0])
        return 0

    @staticmethod
    def find_correct_responser(responsers, own_mentor=None):
        """Найти нужного отвечающего согласно логике распределения
        returns Resoponser object"""
        target_responser = None
        priority_responsers = list()
        check_inactive_time = 0
        check_min_answers = 999
        max_priority = min(set(responser_priority[1] for responser_priority in responsers))
        for responser in responsers:
            if responser[1] == max_priority:
                priority_responsers.append(responser[0])

        if own_mentor != 0 and own_mentor is not None:
            for mentor in priority_responsers:
                if own_mentor.user_id == mentor.user_id:
                    return own_mentor

        for responser in priority_responsers:
            if responser.inactive_time >= check_inactive_time:
                check_inactive_time = responser.inactive_time
                target_responser = responser

        if target_responser == None:
            return

        target_responsers = [target_responser]
        for responser in priority_responsers:
            if responser.user_id != target_responser.user_id and \
                target_responser.inactive_time - 5 <= responser.inactive_time and \
                target_responser.inactive_time + 5 >= responser.inactive_time:
                target_responsers.append(responser)

        for responser in target_responsers:
            if responser.answers <= check_min_answers:
                check_min_answers = responser.answers
                target_responser = responser

        finally_responsers = [target_responser]
        for responser in target_responsers:
            if responser.answers == target_responser.answers:
                finally_responsers.append(responser)

        check_inactive_time = 0
        for responser in finally_responsers:
            if responser.inactive_time >= check_inactive_time:
                check_inactive_time = responser.inactive_time
                target_responser = responser
        return target_responser

    @staticmethod
    def send_ping(bot):
        """Метод для автоматической отправки активных пингов активным отвечающим"""
        while True:
            target_responser = 0
            pings = Helper.get_active_pings()
            if len(pings) > 0 and Helper.active_responsers() != 0:
                for ping in pings:
                    requester = Requester(ping.requester_id)
                    if ping.product_id in Helper.get_mentor_products():
                        mentors = Helper.get_active_mentors(ping.product_id, ping.requester_id)
                        if len(mentors) > 0:
                            own_mentor = Helper.find_own_mentor(ping.requester_id)
                            same_department = []
                            for mentor_data in mentors:
                                mentor = Responser(mentor_data[0])
                                if mentor.department == requester.department:
                                    same_department.append([mentor, mentor_data[1]])

                            if len(same_department) > 0:
                                target_responser = Helper.find_correct_responser(same_department, own_mentor)
                    else:
                        helpers = Helper.get_active_helpers(ping.product_id, ping.requester_id)
                        responsers = Helper.get_active_responsers(ping.product_id, ping.requester_id)
                        if len(helpers) > 0 and ping.from_helper == 0:
                            helpers_ready = []
                            for helper_data in helpers:
                                helper = Responser(helper_data[0])
                                helpers_ready.append([helper, helper_data[0]])
                            target_responser = Helper.find_correct_responser(helpers_ready)
                        elif len(responsers) > 0:
                            responsers_ready = []
                            for responser_data in responsers:
                                if Spectator.is_spectator(responser_data[0]):
                                    responser = Spectator(responser_data[0])
                                else:
                                    responser = Responser(responser_data[0])
                                responsers_ready.append([responser, responser_data[1]])
                            target_responser = Helper.find_correct_responser(responsers_ready)
                        else:
                            target_responser = 0

                    if target_responser != 0:
                        try:
                            ping.update_ping_state(2, target_responser.user_id)
                            target_responser.switch_state()
                            bot.send_message(chat_id=target_responser.user_id
                                             , text="Статус изменен на \"Красный\""
                                             , reply_markup=target_responser.create_keyboard(change_responser_state=1))
                            bot.send_message(chat_id=target_responser.user_id
                                             , parse_mode="markdown"
                                             , text=f"Пинг #s{ping.ping_id}\n{ping.section_name} по {ping.product_name}"
                                                    f"\nПингующий [{ping.requester_fullname}](tg://user?id={ping.requester_id}) "
                                                    f"из отдела {requester.department}"
                                             , reply_markup=ping.answer_keyboard(ping.ping_id))
                            print(f"Отправка пинга:\n{ping.to_str()}\n")

                            Helper.write_log(607, target_responser.user_id
                                             , f"Бот отправил пинг №{ping.ping_id} от {requester.fullname}")

                        except Exception as e:
                            pass

            products = Helper.get_product_pings_count_for_notificate()
            products_denotificate = Helper.get_product_pings_count_for_denotificate()

            products_id_zero = {product[0] for product in products_denotificate if product[2] == 0}
            products_id_not_zero = {product[0] for product in products if product[2] > 0}

            if len(products_id_zero) > 0:
                for responser, responser_shift_state in Helper.get_responsers_for_notificate(was_notificate=1):
                    responser_products = set(responser.products.keys())
                    if responser_products.issubset(products_id_zero):
                        if responser_shift_state == 1:
                            try:
                                bot.send_message(chat_id=responser.user_id
                                                 , text=f"✅ Очередь закончилась ✅"
                                                 , reply_markup=responser.create_keyboard(change_responser_state=0))
                            except Exception as e:
                                pass
                        Helper.update_notification_user_flag(responser.user_id,
                                                             new_was_notification_state=0)
                        Helper.write_log(607, responser.user_id, f"Бот отправил уведомление об окончании очереди")

            if len(products_id_not_zero) > 0:
                for responser, responser_shift_state in Helper.get_responsers_for_notificate(was_notificate=0):
                    responser_products = set(responser.products.keys())
                    if len(responser_products.difference(products_id_not_zero)) < len(responser_products):
                        try:
                            bot.send_message(chat_id=responser.user_id
                                             , text=f"⚠ Образовалась очередь ⚠"
                                             , reply_markup=responser.create_keyboard(change_responser_state=0))
                            Helper.update_notification_user_flag(responser.user_id,
                                                                 new_was_notification_state=1)
                            Helper.write_log(607, responser.user_id, f"Бот отправил уведомление о появлении очереди")
                        except Exception as e:
                            pass

            time.sleep(2)

    @staticmethod
    def check_no_answer(bot):
        """Метод для автоматической проверки, что активные пинги не зависли более х минут на отвечающим без ответа"""
        while True:
            sqlserver_db = pyodbc.connect(CONNECTION_STRING)
            sqlserver_cursor = sqlserver_db.cursor()
            sql = f"SELECT ping_id " \
                  f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
                  f"WHERE in_work = 1 " \
                  f"  AND date_answered is null " \
                  f"  AND datediff(ss, date_sent, getdate()) >= 60"
            result = sqlserver_cursor.execute(sql).fetchall()
            if result is not None:
                for ping_row in result:
                    ping = Ping()
                    ping.fill_active_ping(ping_row[0])
                    if ping.date_answered is None:
                        ping.update_ping_state(7)
                        ping.return_to_queue()
                        try:
                            bot.send_message(chat_id=ping.responser_id
                                             , text=f"Ты не ответил(а) на пинг #s{ping.ping_id} по {ping.section_name} "
                                                    f"по {ping.product_name} в течение минуты.\nПинг был возвращен в очередь.")
                            Helper.write_log(607, ping.responser_id, f"Бот забрал пинг №{ping.ping_id}")
                        except:
                            pass
            time.sleep(20)

    @staticmethod
    def send_notification(bot):
        """Метод для уведомления об очередях в пингах"""
        while True:
            # Оповестить отвечающих, которые сидят с пингом более 15 минут
            sqlserver_db = pyodbc.connect(CONNECTION_STRING)
            sqlserver_cursor = sqlserver_db.cursor()
            sql = f"SELECT ap.ping_id" \
                  f"  , ap.responser_id" \
                  f"  , datediff(ss, ap.date_sent, getdate()) " \
                  f"FROM UKSTGBot.dbo.ActivePings as ap with(nolock) " \
                  f"JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.user_id = ap.responser_id " \
                  f"WHERE in_work = 1 " \
                  f"  AND ud.is_block = 0 " \
                  f"  AND date_answered is not null " \
                  f"  AND datediff(ss, ap.notification_datetime, getdate()) > 900 "
            result = sqlserver_cursor.execute(sql).fetchall()
            if len(result) > 0:
                for responser in result:
                    bot.send_message(chat_id=responser[1]
                                     , text=f"Ты решаешь вопрос #s{responser[0]} уже более {int(responser[2]/60)} минут."
                                            f"\nЕсли ты забыл(а) закрыть пинг, то, пожалуйста, закрой его.")
                    sql = f"UPDATE UKSTGBot.dbo.ActivePings " \
                          f"SET notification_datetime = getdate() " \
                          f"WHERE ping_id = {responser[0]}"
                    sqlserver_cursor.execute(sql)
                    sqlserver_db.commit()
                    Helper.write_log(607, responser[1], f"Бот отправил уведомление о долгом решении пинга №{responser[0]}")
            time.sleep(10)

    @staticmethod
    def auto_close_pings(bot):
        """Метод для уведомления об очередях в пингах"""
        while True:
            # Оповестить пингующего о том, что его пинг будет автоматически закрыт.
            sqlserver_db = pyodbc.connect(CONNECTION_STRING)
            sqlserver_cursor = sqlserver_db.cursor()
            sql = f"SELECT DISTINCT " \
                  f"  ap.ping_id " \
                  f"  , requ.user_id " \
                  f"  , sum(case when datediff(ss, rescs.end_date, getdate()) >= 60 then 0 else 1 end) " \
                  f"FROM UKSTGBot.dbo.ActivePings as ap with(nolock) " \
                  f"JOIN UKSTGBot.dbo.Users as requ with(nolock) on requ.user_id = ap.requester_id " \
                  f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) on uop.product_id = ap.product_id " \
                  f"  AND uop.direction = 'response' " \
                  f"JOIN UKSTGBot.dbo.Users as resu with(nolock) on resu.user_id = uop.user_id " \
                  f"JOIN UKSTGBot.dbo.Callider as resc with(nolock) on resc.userlogin = resu.userlogin " \
                  f"LEFT JOIN UKSTGBot.dbo.CalliderShifts as rescs with(nolock) on rescs.callider_id = resc.callider_id " \
                  f"  AND convert(date, rescs.start_date) = convert(date, ap.date_created) " \
                  f"WHERE ap.comment <> '' " \
                  f"  AND ap.date_answered is null " \
                  f"  AND rescs.end_date is not null " \
                  f"GROUP BY ap.ping_id, requ.user_id "
            result = sqlserver_cursor.execute(sql).fetchall()
            if len(result) > 0:
                for data in result:
                    if data[2] == 0:
                        ping = Ping()
                        ping.fill_active_ping(data[0])
                        ping.update_ping_state(10)
                        ping.close()
                        bot.edit_message_text(chat_id=data[1]
                                              , message_id=ping.message_id
                                              , text=f"Пинг #s{ping.ping_id} по {ping.product_name} был автоматически закрыт")
                        bot.send_message(chat_id=data[1]
                                         , text=f"Рабочий день сотрудников завершен. "
                                                f"Если пинг #s{ping.ping_id} по продукту {ping.product_name} ещё актуален, то поставь инцидент.")
                        requester = Requester(ping.requester_id)
                        requester.has_started_ping(False)
                        Helper.write_log(607, data[1], f"Бот автоматически закрыл пинг #s{data[0]}")

            sql = f"SELECT DISTINCT " \
                  f"  ping_id " \
                  f"  , requester_id " \
                  f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
                  f"WHERE comment = '' " \
                  f"  AND datediff(ss, date_created, getdate()) > 60*4 "
            result = sqlserver_cursor.execute(sql).fetchall()
            if len(result) > 0:
                for data in result:
                    ping = Ping()
                    ping.fill_active_ping(data[0])
                    ping.update_ping_state(11)
                    ping.close()
                    bot.edit_message_text(chat_id=data[1]
                                          , message_id=ping.message_id
                                          , text=f"Пинг #s{ping.ping_id} по продукту {ping.product_name} был автоматически закрыт.")
                    bot.send_message(chat_id=data[1]
                                     , text=f"У пинга #s{ping.ping_id} по продукту {ping.product_name} не найден комментарий. Пинг был закрыт автоматически. "
                                            f"Если вопрос актуален, то отправь новый пинг и не забудь добавить комментарий.")
                    requester = Requester(ping.requester_id)
                    requester.has_started_ping(False)
                    Helper.write_log(607, data[1], f"Бот автоматически закрыл пинг #s{data[0]} из-за отсутствия комментария.")
            time.sleep(60)

    @staticmethod
    def get_users_by_fullname(last_name, first_name):
        """Позволяет отвечающему получить список пользователей по команде 'найти Фамилия Имя'"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT case c.department " \
              f"when 'Эльба' then 'Эльба' " \
              f"when 'Сектор г.Новосибирск, Отдел Экстерн №1' then 'НВС КЭ1' " \
              f"when 'Сектор г.Новосибирск, Отдел Маркет №1' then 'НВС Мркт1' " \
              f"when 'Сектор г.Новосибирск, Отдел Диадок №1' then 'НВС ДД1' " \
              f"when 'Сектор г.Екатеринбург, Отдел Экстерн №2' then 'ЕКБ КЭ2' " \
              f"when 'Сектор г.Екатеринбург, Отдел Экстерн №1' then 'ЕКБ КЭ1' " \
              f"when 'Сектор г.Екатеринбург, Отдел ФМС №1' then 'ЕКБ ФМС1' " \
              f"when 'Сектор г.Екатеринбург, Отдел УЦ №1' then 'ЕКБ УЦ1' " \
              f"when 'Сектор г.Екатеринбург, Отдел Ритейл №1' then 'ЕКБ Рит1' " \
              f"when 'Сектор г.Екатеринбург, Отдел ОФД №1' then 'ЕКБ ОФД1' " \
              f"when 'Сектор г.Екатеринбург, Отдел Маркет №1' then 'ЕКБ Мркт1' " \
              f"when 'Сектор г.Екатеринбург, Отдел Диадок №2' then 'ЕКБ ДД2' " \
              f"when 'Сектор г.Екатеринбург, Отдел Диадок №1' then 'ЕКБ ДД1' " \
              f"when 'Сектор г.Воронеж, Отдел Экстерн №1' then 'ВРН КЭ1' " \
              f"when 'Сектор г.Воронеж, Отдел Диадок №1' then 'ВРН ДД1' " \
              f"when 'Сектор г.Волгоград, Отдел Экстерн №2' then 'ВЛГ КЭ2' " \
              f"when 'Сектор г.Волгоград, Отдел Экстерн №1' then 'ВЛГ КЭ1' " \
              f"when 'Сектор г.Волгоград, Отдел УЦ №1' then 'ВЛГ УЦ1' " \
              f"when 'Сектор г.Барнаул, Отдел УЦ №1' then 'БРН УЦ1' " \
              f"when 'Контур.Бухгалтерия' then 'КБ' " \
              f"when 'Аналитический отдел' then 'АО' " \
              f"when 'Экспертный отдел' then 'ЭО' " \
              f"when 'Отдел проверки знаний' then 'ОПЗ' " \
              f"when 'Отдел обучения Воронеж' then 'ОО ВРН' " \
              f"when 'Отдел обучения АУБ' then 'ОО АУБ' " \
              f"when 'Отдел обучения Барнаул' then 'ОО БРН' " \
              f"when 'Отдел обучения НТТ' then 'ОО НТТ' " \
              f"when 'Сектор г.Екатеринбург, Группа Поддержки Корпоративных Клиентов \"Экстерн\"' then 'ЕКБ ГПКК1' " \
              f"when 'VIP-линия ЭДО' then 'VIP ЭДО' " \
              f"when 'Отдел обучения' then 'ОО' " \
              f"when 'Отдел обучения Новосибирск' then 'ОО НВС' " \
              f"when 'Отдел обучения Волгоград' then 'ОО ВЛГ' " \
              f"when 'Первая линия' then '1 лин.' " \
              f"else '?' end " \
              f"  , c.fullname" \
              f"  , ud.user_id " \
              f"FROM UKSTGBot.dbo.Callider as c with(nolock) " \
              f"LEFT JOIN UKSTGBot.dbo.Users as ud with(nolock) on ud.userlogin = c.userlogin " \
              f"WHERE c.fullname like '{last_name} {first_name}%' " \
              f"  AND c.fired = 0 " \
              f"ORDER BY 1,2"
        result = sqlserver_cursor.execute(sql).fetchall()
        kbrd = types.InlineKeyboardMarkup()
        for user in result:
            kbrd.row(types.InlineKeyboardButton(text=f"{user[0]} {user[1]}", callback_data=f"find_user;{user[2]}"))
        kbrd.row(types.InlineKeyboardButton(text=f"Закрыть", callback_data=f"close_menu"))
        return kbrd

    @staticmethod
    def get_responsers_who_answered(user_id, mode):
        """Показать всех отвечающих за сегодня по продуктам пользователя"""
        answer = "--\n"
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        if mode == "responser":
            sql = f"WITH cte_user_products AS " \
                  f"( SELECT product_id " \
                  f"  FROM UKSTGBot.dbo.DepartmentProducts dp with(nolock) " \
                  f"  JOIN UKSTGBot.dbo.Departments d with(nolock) on d.department_id = dp.department_id " \
                  f"  JOIN UKSTGBot.dbo.Callider c with(nolock) on c.department = d.department_name " \
                  f"  JOIN UKSTGBot.dbo.Users u with(nolock) on u.userlogin = c.userlogin " \
                  f"  WHERE u.user_id = {user_id} ) " \
                  f"SELECT DISTINCT c.department " \
                  f"  , c.fullname " \
                  f"  , rs.state_name " \
                  f"  , case " \
                  f"    when isnull(convert(date, aap.last_close_dt), convert(date, '2020-01-01')) <> convert(date,getdate()) " \
                  f"    then convert(datetime2(0), convert(date, getdate())) " \
                  f"    else convert(datetime2(0), aap.last_close_dt) end " \
                  f"  , isnull(cnt.cnt, 0) " \
                  f"  , ur.role_name " \
                  f"  , case when getdate() between cs.start_date and cs.end_date then 1 " \
                  f"    when getdate() >= cs.end_date then 2 " \
                  f"    else 0 end as WorkState " \
                  f"  , case when sl.responser_id is not null then 1 else 0 end " \
                  f"FROM UKSTGBot.dbo.Callider as c with(nolock) " \
                  f"JOIN UKSTGBot.dbo.UserRoles as ur with(nolock) ON ur.role_id = c.role " \
                  f"JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.userlogin = c.userlogin " \
                  f"JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
                  f"JOIN UKSTGBot.dbo.ResponserStates as rs with(nolock) ON rs.state_id = ud.responser_state_id " \
                  f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
                  f"  AND uop.direction = 'response' " \
                  f"LEFT JOIN ( SELECT responser_id, max(date_closed) as last_close_dt " \
                  f"            FROM UKSTGBot.dbo.ArchivePings with(nolock) " \
                  f"            WHERE product_id in ( SELECT product_id " \
                  f"                                  FROM cte_user_products ) " \
                  f"            GROUP BY responser_id ) as aap ON aap.responser_id = ud.user_id " \
                  f"LEFT JOIN ( SELECT DISTINCT responser_id " \
                  f"            FROM UKSTGBot.dbo.ActivePings with(nolock) ) as sl ON sl.responser_id = ud.user_id " \
                  f"LEFT JOIN ( SELECT ap.responser_id, count(*) as cnt " \
                  f"            FROM UKSTGBot.dbo.ArchivePings as ap with(nolock) " \
                  f"            WHERE product_id in ( SELECT product_id " \
                  f"                                  FROM cte_user_products ) " \
                  f"              AND convert(date, ap.date_answered) = convert(date, getdate()) " \
                  f"              AND ap.ping_state_id = 4 " \
                  f"            GROUP BY ap.responser_id ) as cnt ON cnt.responser_id = ud.user_id " \
                  f"WHERE convert(date, cs.start_date) = convert(date, getdate()) " \
                  f"  AND case when getdate() between cs.start_date and cs.end_date then 1 " \
                  f"      when getdate() >= cs.end_date then 2 " \
                  f"      else 0 end > 0 " \
                  f"  AND ud.can_response = 1 " \
                  f"  AND ur.can_response = 1 " \
                  f"  AND uop.product_id in ( SELECT product_id " \
                  f"                          FROM cte_user_products ) " \
                  f"  AND uop.product_id not in (3,4,5,22494,79976,600) " \
                  f" ORDER BY case when getdate() between cs.start_date and cs.end_date then 1 " \
                  f"          when getdate() >= cs.end_date then 2 " \
                  f"          else 0 end  " \
                  f"  , c.department " \
                  f"  , ur.role_name " \
                  f"  , rs.state_name " \
                  f"  , case when sl.responser_id is not null then 1 else 0 end DESC " \
                  f"  , case " \
                  f"    when isnull(convert(date, aap.last_close_dt), convert(date, '2020-01-01')) <> convert(date,getdate()) " \
                  f"    then convert(datetime2(0), convert(date, getdate())) " \
                  f"    else convert(datetime2(0), aap.last_close_dt) end " \
                  f"  , isnull(cnt.cnt, 0) DESC "
        else:
            sql = f"SELECT DISTINCT c.department" \
                  f"  , c.fullname" \
                  f"  , rs.state_name " \
                  f"  , case " \
                  f"    when isnull(convert(date, aap.last_close_dt), convert(date, '2020-01-01')) <> convert(date,getdate()) " \
                  f"    then convert(datetime2(0), convert(date, getdate())) " \
                  f"    else convert(datetime2(0), aap.last_close_dt) end " \
                  f"  , isnull(cnt.cnt, 0) " \
                  f"  , ur.role_name " \
                  f"  , case when getdate() between cs.start_date and cs.end_date then 1 " \
                  f"    when getdate() >= cs.end_date then 2 " \
                  f"    else 0 end as WorkState " \
                  f"  , case when sl.responser_id is not null then 1 else 0 end " \
                  f"FROM UKSTGBot.dbo.Callider as c with(nolock) " \
                  f"JOIN UKSTGBot.dbo.UserRoles as ur with(nolock) ON ur.role_id = c.role " \
                  f"JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.userlogin = c.userlogin " \
                  f"JOIN UKSTGBot.dbo.ResponserStates as rs with(nolock) ON rs.state_id = ud.responser_state_id " \
                  f"JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
                  f"LEFT JOIN ( SELECT responser_id, max(date_closed) as last_close_dt " \
                  f"       FROM UKSTGBot.dbo.ArchivePings with(nolock) " \
                  f"       GROUP BY responser_id ) as aap ON aap.responser_id = ud.user_id " \
                  f"LEFT JOIN ( SELECT DISTINCT responser_id " \
                  f"            FROM UKSTGBot.dbo.ActivePings with(nolock) ) as sl ON sl.responser_id = ud.user_id " \
                  f"LEFT JOIN ( SELECT ap.responser_id, count(*) as cnt " \
                  f"            FROM UKSTGBot.dbo.ArchivePings as ap with(nolock) " \
                  f"            WHERE convert(date, ap.date_answered) = convert(date, getdate()) " \
                  f"              AND ap.ping_state_id = 4 " \
                  f"            GROUP BY ap.responser_id ) as cnt ON cnt.responser_id = ud.user_id " \
                  f"WHERE convert(date, cs.start_date) = convert(date, getdate()) " \
                  f"  AND case when getdate() between cs.start_date and cs.end_date then 1 " \
                  f"      when getdate() >= cs.end_date then 2 " \
                  f"      else 0 end > 0 " \
                  f"  AND ud.can_response = 1 " \
                  f"  AND ur.can_response = 1 " \
                  f"  AND c.department in ( " \
                  f"    SELECT department_name " \
                  f"    FROM UKSTGBot.dbo.Departments with(nolock) " \
                  f"    WHERE group_id = (" \
                  f"      SELECT group_id " \
                  f"      FROM UKSTGBot.dbo.Users as u with(nolock) " \
                  f"      JOIN UKSTGBot.dbo.Callider as c with(nolock) ON u.userlogin = c.userlogin " \
                  f"      JOIN UKSTGBot.dbo.Departments as d with(nolock) ON d.department_name = c.department " \
                  f"      WHERE u.user_id = {user_id} )) " \
                  f" ORDER BY case when getdate() between cs.start_date and cs.end_date then 1 " \
                  f"          when getdate() >= cs.end_date then 2 " \
                  f"          else 0 end  " \
                  f"  , c.department " \
                  f"  , ur.role_name " \
                  f"  , rs.state_name " \
                  f"  , case when sl.responser_id is not null then 1 else 0 end DESC " \
                  f"  , case " \
                  f"    when isnull(convert(date, aap.last_close_dt), convert(date, '2020-01-01')) <> convert(date,getdate()) " \
                  f"    then convert(datetime2(0), convert(date, getdate())) " \
                  f"    else convert(datetime2(0), aap.last_close_dt) end " \
                  f"  , isnull(cnt.cnt, 0) DESC "
        result = sqlserver_cursor.execute(sql).fetchall()

        if len(result) > 0:
            responser = None
            for responser_data in result:
                if responser is None:
                    responser_department = responser_data[0]
                    last_name, first_name, *args = responser_data[1].split(" ")
                    responser_fullname = f"{last_name} {first_name}"
                    responser = responser_data[1]
                    responser_state = ''
                    if responser_data[2] == 'Зеленый':
                        responser_state = '🟢' 
                    elif responser_data[2] == 'Красный' and responser_data[7] == 1:
                        responser_state = '📝' 
                    else:
                        responser_state = '🔴'
                    minutes = int((datetime.datetime.now() - datetime.datetime.strptime(str(responser_data[3]),
                                                                                        "%Y-%m-%d %H:%M:%S")).total_seconds() // 60)
                    closed_pings = responser_data[4]
                    responser_role = responser_data[5]
                    responser_work_state = responser_data[6]
                    answer = f"{'---На смене---' if responser_work_state == 1 else '---Смена закончилась---'}\n\n{responser_department}\n\n{responser_role}\n" \
                             f"{responser_state} | {responser_fullname:<} | {minutes:<4} мин. | {closed_pings:<3}\n"

                elif responser_data[6] == responser_work_state:
                    if responser_data[0] == responser_department:
                        if responser_data[5] == responser_role:
                            if responser_data[1] != responser:
                                last_name, first_name, *args = responser_data[1].split(" ")
                                responser_fullname = f"{last_name} {first_name}"
                                responser = responser_data[1]
                                responser_state = ''
                                if responser_data[2] == 'Зеленый':
                                    responser_state = '🟢' 
                                elif responser_data[2] == 'Красный' and responser_data[7] == 1:
                                    responser_state = '📝' 
                                else:
                                    responser_state = '🔴'
                                minutes = int((datetime.datetime.now() - datetime.datetime.strptime(str(responser_data[3]), "%Y-%m-%d %H:%M:%S")).total_seconds() // 60)
                                closed_pings = responser_data[4]
                                answer += f"{responser_state} | {responser_fullname:<} | {minutes:<4} мин. | {closed_pings:<3}\n"
                        else:
                            last_name, first_name, *args = responser_data[1].split(" ")
                            responser_fullname = f"{last_name} {first_name}"
                            responser = responser_data[1]
                            responser_state = ''
                            if responser_data[2] == 'Зеленый':
                                responser_state = '🟢' 
                            elif responser_data[2] == 'Красный' and responser_data[7] == 1:
                                responser_state = '📝' 
                            else:
                                responser_state = '🔴'
                            minutes = int((datetime.datetime.now() - datetime.datetime.strptime(str(responser_data[3]), "%Y-%m-%d %H:%M:%S")).total_seconds() // 60)
                            closed_pings = responser_data[4]
                            responser_role = responser_data[5]
                            answer += f"\n{responser_role}\n{responser_state} | {responser_fullname:<} | {minutes:<4} мин. | {closed_pings:<3}\n"

                    else:
                        responser_department = responser_data[0]
                        last_name, first_name, *args = responser_data[1].split(" ")
                        responser_fullname = f"{last_name} {first_name}"
                        responser = responser_data[1]
                        responser_state = ''
                        if responser_data[2] == 'Зеленый':
                            responser_state = '🟢' 
                        elif responser_data[2] == 'Красный' and responser_data[7] == 1:
                            responser_state = '📝' 
                        else:
                            responser_state = '🔴'
                        minutes = int((datetime.datetime.now() - datetime.datetime.strptime(str(responser_data[3]), "%Y-%m-%d %H:%M:%S")).total_seconds() // 60)
                        closed_pings = responser_data[4]
                        responser_role = responser_data[5]
                        answer += f"\n\n{responser_department}\n\n{responser_role}\n{responser_state} | {responser_fullname:<} | {minutes:<4} мин. | {closed_pings:<3}\n"

                else:
                    responser_department = responser_data[0]
                    last_name, first_name, *args = responser_data[1].split(" ")
                    responser_fullname = f"{last_name} {first_name}"
                    responser = responser_data[1]
                    responser_state = ''
                    if responser_data[2] == 'Зеленый':
                        responser_state = '🟢' 
                    elif responser_data[2] == 'Красный' and responser_data[7] == 1:
                        responser_state = '📝' 
                    else:
                        responser_state = '🔴'
                    minutes = int((datetime.datetime.now() - datetime.datetime.strptime(str(responser_data[3]),
                                                                                        "%Y-%m-%d %H:%M:%S")).total_seconds() // 60)
                    closed_pings = responser_data[4]
                    responser_role = responser_data[5]
                    responser_work_state = responser_data[6]
                    answer += f"\n\n{'---На смене---' if responser_work_state == 1 else '---Смена закончилась---'}\n\n{responser_department}\n\n{responser_role}\n" \
                              f"{responser_state} | {responser_fullname:<} | {minutes:<4} мин. | {closed_pings:<3}\n"

        return answer

    @staticmethod
    def get_active_pings_for_notificate():
        """Получить список продуктов по которым есть активные пинги. Возвращает string"""
        pings = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT ping_id, date_created " \
              f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"WHERE comment <> '' " \
              f"  and in_work = 0 " \
              f"  and convert(datetime2(0), convert(date,getdate())) > dateadd(ss, 120, date_created)"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) > 0:
            for ping in result:
                pings.append(ping[0])
        return pings

    @staticmethod
    def get_responsers_for_notificate(was_notificate):
        """Найти данные по отвечающим, которых ещё не пинговали по очередям"""
        responsers = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        if was_notificate == 1:
            sql = f"SELECT DISTINCT ud.user_id " \
                  f"  , case when cs.start_date is null then 0 " \
                  f"      else 1 end as shift_state " \
                  f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                  f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
                  f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
                  f"LEFT JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
                  f"  AND getdate() between cs.start_date and cs.end_date " \
                  f"WHERE ud.was_notification = {was_notificate} " \
                  f"  AND uop.direction = 'response' " \
                  f"  AND c.fired = 0 " \
                  f"  AND c.role not in (5,6,10)"
        else:
            sql = f"SELECT DISTINCT ud.user_id " \
                  f"  , 1 as shift_state " \
                  f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                  f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
                  f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
                  f"JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
                  f"  AND getdate() between cs.start_date and cs.end_date " \
                  f"WHERE ud.notification_alert_state = 1 " \
                  f"  AND ud.was_notification = {was_notificate} " \
                  f"  AND uop.direction = 'response' " \
                  f"  AND c.fired = 0 " \
                  f"  AND c.role not in (5,6,10)"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) > 0:

            for responser in result:
                if Spectator.is_spectator(responser[0]):
                    target_responser = Spectator(responser[0])
                else:
                    target_responser = Responser(responser[0])
                responsers.append((target_responser, responser[1]))
        return responsers

    @staticmethod
    def get_product_pings_count_for_notificate():
        """Получить данные по продуктам, которые накопили очередь"""
        products = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT pp.product_id, pp.product_name, isnull(t.cnt, 0) " \
              f"FROM UKSTGBot.dbo.Products as pp with(nolock) " \
              f"LEFT JOIN ( " \
              f"  SELECT product_id, count(*) as cnt " \
              f"  FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"  WHERE comment <> '' " \
              f"    and in_work = 0 " \
              f"    and datediff(ss, date_created, getdate()) > 120 " \
              f"  GROUP BY product_id ) as t ON t.product_id = pp.product_id"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) > 0:
            for product in result:
                products.append([product[0], product[1], product[2]])
        return products

    @staticmethod
    def get_product_pings_count_for_denotificate():
        """Получить данные по продуктам, которые накопили очередь"""
        products = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT pp.product_id, pp.product_name, isnull(t.cnt, 0) " \
              f"FROM UKSTGBot.dbo.Products as pp with(nolock) " \
              f"LEFT JOIN ( " \
              f"  SELECT product_id, count(*) as cnt " \
              f"  FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"  WHERE comment <> '' " \
              f"    and in_work = 0 " \
              f"  GROUP BY product_id ) as t ON t.product_id = pp.product_id"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) > 0:
            for product in result:
                products.append([product[0], product[1], product[2]])
        return products

    @staticmethod
    def get_not_route_users_pings_for_notificate():
        """Получить данные по продуктам, которые накопили очередь"""
        products = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT pp.product_id, pp.product_name, isnull(t.cnt, 0) " \
              f"FROM UKSTGBot.dbo.Products as pp with(nolock) " \
              f"LEFT JOIN ( " \
              f"  SELECT ap.product_id, p.product_name, count(*) as cnt " \
              f"  FROM UKSTGBot.dbo.ActivePings as ap with(nolock) " \
              f"  JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = ap.product_id " \
              f"  WHERE ap.comment <> '' " \
              f"    AND ap.in_work = 0 " \
              f"    AND getdate() > dateadd(ss, 120, ap.date_created) " \
              f"    AND ap.requester_id in ( SELECT user_id FROM UKSTGBot.dbo.NotRouteUsers ) " \
              f"  GROUP BY ap.product_id, p.product_name ) as t ON t.product_id = pp.product_id"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) > 0:
            for product in result:
                products.append([product[0], product[1], product[2]])
        return products

    @staticmethod
    def update_notification_flag(responser_id, product_id):
        """Обновить статус информирования об очереди"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.UserOptionalProducts " \
              f"SET was_notification = case when was_notification = 0 then 1 else 0 end " \
              f"WHERE user_id = {responser_id} and product_id = {product_id} and direction = 'response'"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    @staticmethod
    def update_notification_user_flag(responser_id, new_was_notification_state):
        """Обновить статус получения уведомлений об очереди у отвечающего"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.Users " \
              f"SET was_notification = {new_was_notification_state} " \
              f"WHERE user_id = {responser_id}"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    @staticmethod
    def get_active_products_id():
        """Получить список продуктов по которым есть активные пинги. Возвращает []"""
        products_id = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = "SELECT DISTINCT product_id " \
              "FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              "WHERE comment <> '' and in_work = 0"

        products_id_raw = sqlserver_cursor.execute(sql).fetchall()
        if len(products_id_raw) != 0:
            for product_id in products_id_raw:
                products_id.append(product_id[0])
        return products_id

    @staticmethod
    def get_random_ping_from_queue(responser_id):
        """Получить рандомный пинг по продукту, который есть у отвечающего"""
        local_queue = []
        if Helper.ping_in_queue() != 0:
            for product_id in Helper.get_active_products_id():
                ping = Helper.get_min_ping_by_product_id(product_id, responser_id)
                if ping is not None:
                    local_queue.append(ping)

            for ping in sorted(local_queue, key=lambda ping: ping.ping_id):
                responser = Responser(responser_id)

                # если отвечающий = помогатор, то проверить что пинг не от помогатора
                if ping.from_helper == 1 and Helper.is_cons(responser.user_id):
                    return None

                requester = Requester(ping.requester_id)
                if Helper.not_route_user(ping.requester_id):
                    if requester.department == responser.department:
                        if ping.product_id in responser.products.keys():
                            return ping
                else:
                    if ping.product_id in responser.products.keys():
                        if ping.product_id != 0:
                            return ping
                        else:
                            if responser.department in Helper.get_departments_by_requester(requester.department):
                                return ping
            return None

    @staticmethod
    def get_additional_ping(bot, responser_id):
        """Взять дополнительный пинг"""
        Helper.write_log(responser_id, -1, f"Попытка взять пинг по кнопке \"Взять еще пинг\"")
        ping = Helper.get_random_ping_from_queue(responser_id)
        if ping is not None:
            ping.update_ping_state(2, responser_id)
            Helper.switch_responser_state(responser_id, 0)
            if Spectator.is_spectator(responser_id):
                responser = Spectator(responser_id)
            else:
                responser = Responser(responser_id)
            bot.send_message(chat_id=responser_id
                             , text="Статус изменен на \"Красный\"."
                             , reply_markup=responser.create_keyboard(change_responser_state=1))
            requseter = Requester(ping.requester_id)
            try:
                bot.send_message(chat_id=responser_id
                                 , parse_mode="markdown"
                                 , text=f"Пинг #s{ping.ping_id}\n{ping.section_name} по {ping.product_name}"
                                        f"\nПингующий [{ping.requester_fullname}](tg://user?id={ping.requester_id}) "
                                        f"из отдела {requseter.department}"
                                 , reply_markup=ping.answer_keyboard(ping.ping_id))
            except:
                pass
            Helper.write_log(responser.user_id, -1, f"Взят пинг №{ping.ping_id} по кнопке \"Взять еще пинг\"")
            return True
        return False

    @staticmethod
    def get_active_pings():
        """Получить пинг по продукту"""
        pings = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT ping_id " \
              f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"WHERE in_work = 0 " \
              f"  AND comment <> '' " \
              f"ORDER BY ping_id"
        result = sqlserver_cursor.execute(sql).fetchall()
        if len(result) > 0:
            for ping_id in result:
                ping = Ping()
                ping.fill_active_ping(ping_id[0])
                pings.append(ping)
        return pings

    @staticmethod
    def get_last_active_ping_by_user_id(user_id):
        """Получить пинг по продукту"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT ping_id " \
              f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"WHERE in_work = 0 " \
              f"  AND comment <> '' " \
              f"  AND requester_id = {user_id} " \
              f"ORDER BY date_created DESC"
        result = sqlserver_cursor.execute(sql).fetchone()
        if result:
            return result[0]
        return None

    @staticmethod
    def get_min_ping_by_product_id(product_id, responser_id):
        """Получить пинг по продукту"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT min(ping_id) " \
              f"FROM UKSTGBot.dbo.ActivePings ap with(nolock) " \
              f"WHERE ap.product_id = {product_id} " \
              f"  AND ap.in_work = 0 " \
              f"  AND ap.comment <> '' " \
              f"  AND ap.responser_id = 0 "
        result = sqlserver_cursor.execute(sql).fetchone()[0]
        ping = None
        if result is not None:
            ping = Ping()
            ping.fill_active_ping(result)
        return ping

    @staticmethod
    def get_product_id_by_name(product_name):
        """Вернуть id продукта по названию"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT product_id " \
              f"FROM UKSTGBot.dbo.Products with(nolock) " \
              f"WHERE product_name = '{product_name}'"
        return sqlserver_cursor.execute(sql).fetchone()[0]

    @staticmethod
    def get_active_mentors(product_id, requester_id):
        """Найти отвечающего с наименьшим количеством ответов по продукту"""
        mentors = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT ud.user_id, uop.priority " \
              f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
              f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
              f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
              f"JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
              f"  AND getdate() between cs.start_date and cs.end_date " \
              f"WHERE uop.product_id = {product_id} " \
              f"  AND uop.direction = 'response' " \
              f"  AND ud.responser_state_id = 1 " \
              f"  AND ud.can_response = 1 " \
              f"  AND ud.is_block = 0 " \
              f"  AND c.role = 4 " \
              f"  AND c.fired = 0 " \
              f"  AND ud.user_id not in ( SELECT responser_id " \
              f"                          FROM UKSTGBot.dbo.AvoidList with(nolock) " \
              f"                          WHERE requester_id = {requester_id} ) " \
              f"ORDER BY uop.priority"
        result = sqlserver_cursor.execute(sql).fetchall()
        for mentor_data in result:
            mentors.append([mentor_data[0], mentor_data[1]])
        return mentors

    @staticmethod
    def get_active_responsers(product_id, requester_id):
        """Найти отвечающего с наименьшим количеством ответов по продукту"""
        responsers = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT ud.user_id, uop.priority " \
              f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
              f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
              f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
              f"JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
              f"  AND getdate() between cs.start_date and cs.end_date " \
              f"WHERE uop.product_id = {product_id} " \
              f"  AND uop.direction = 'response' " \
              f"  AND ud.responser_state_id = 1 " \
              f"  AND ((c.role = 3 and ud.can_response = 1) or (c.role in (1,2) and ud.get_pings_state = 1 and ud.can_response = 1)) " \
              f"  AND ud.is_block = 0 " \
              f"  AND c.fired = 0 " \
              f"  AND c.role in (1,2,3) " \
              f"  AND ud.user_id not in ( SELECT responser_id " \
              f"                          FROM UKSTGBot.dbo.AvoidList with(nolock) " \
              f"                          WHERE requester_id = {requester_id} ) "
        result = sqlserver_cursor.execute(sql).fetchall()
        for responser_id in result:
            responsers.append([responser_id[0], responser_id[1]])
        return responsers

    @staticmethod
    def get_active_helpers(product_id, requester_id):
        helpers = []
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT DISTINCT ud.user_id, uop.priority " \
              f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
              f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id  " \
              f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
              f"JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
              f"  AND getdate() between cs.start_date and cs.end_date " \
              f"WHERE uop.product_id = {product_id} " \
              f"  AND uop.direction = 'response' " \
              f"  AND ud.responser_state_id = 1 " \
              f"  AND ud.can_response = 1 " \
              f"  AND ud.is_block = 0 " \
              f"  AND c.fired = 0 " \
              f"  AND c.role = 7 " \
              f"  AND ud.user_id not in ( SELECT responser_id " \
              f"                          FROM UKSTGBot.dbo.AvoidList " \
              f"                          WHERE requester_id = {requester_id} ) "
        result = sqlserver_cursor.execute(sql).fetchall()
        for helper_id in result:
            helpers.append([helper_id[0], helper_id[1]])
        return helpers

    @staticmethod
    def get_responsers_by_product_id(product_id):
        """Найти всех активных отвечающих"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT DISTINCT ud.user_id " \
              f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
              f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id=ud.user_id " \
              f"WHERE uop.product_id={product_id} " \
              f"  AND uop.direction='response' "
        return sqlserver_cursor.execute(sql).fetchall()

    @staticmethod
    def get_last_ping_id_by_user_id(user_id):
        """Найти ping_id последнего активного пинга от пользователя"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT TOP 1 ping_id " \
              f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"WHERE requester_id = {user_id} " \
              f"  AND comment = '' " \
              f"ORDER BY ping_id "
        return sqlserver_cursor.execute(sql).fetchone()[0]

    @staticmethod
    def get_products_by_department_id(department_id):
        """Получить все продукты, которые были закреплены за отделом"""
        products = {}
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT p.product_id, p.product_name " \
              f"FROM UKSTGBot.dbo.Products as p with(nolock) " \
              f"JOIN UKSTGBot.dbo.DepartmentProducts as dp with(nolock) ON dp.product_id=p.product_id " \
              f"WHERE dp.department={department_id}"
        for product in sqlserver_cursor.execute(sql).fetchall():
            products.setdefault(product[0], product[1])
        return products

    @staticmethod
    def get_staff_by_user_id(user_id):
        """Получить список сотрудников одного отдела с вызвавшим команду /list"""
        users = ""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT ud.user_id, cc.profession, cc.fullname " \
              f"FROM UKSTGBot.dbo.Callider as cc with(nolock) " \
              f"JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.userlogin = cc.userlogin " \
              f"JOIN ( " \
              f"  SELECT department " \
              f"  FROM UKSTGBot.dbo.Callider as c with(nolock) " \
              f"  JOIN UKSTGBot.dbo.Users as ud with(nolock) ON ud.userlogin = c.userlogin " \
              f"  WHERE ud.user_id = {user_id}) as dep ON dep.department = cc.department " \
              f"WHERE cc.fired = 0 " \
              f"ORDER BY cc.fullname"
        for user in sqlserver_cursor.execute(sql).fetchall():
            users += f"{user[0]} | {user[1]} | {user[2]}\n"
        return users

    @staticmethod
    def get_all_products():
        """Показать список всех продуктов с их ID"""
        products = "ID | Название\n"
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT product_id, product_name " \
              f"FROM UKSTGBot.dbo.Products with(nolock) " \
              f"ORDER BY product_name"
        for product in sqlserver_cursor.execute(sql).fetchall():
            products += f"{product[0]:5<0} | {product[1]}\n"
        return products

    @staticmethod
    def get_all_departments():
        """Вывести список всех отделов c их ID"""
        departments = "ID | Название \n"
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT department_id, department_name " \
              f"FROM UKSTGBot.dbo.Departments with(nolock) " \
              f"WHERE department_id is not null " \
              f"ORDER BY department_name"
        for department in sqlserver_cursor.execute(sql).fetchall():
            departments += f"{department[0]:2>} | {department[1]}\n"
        return departments

    @staticmethod
    def get_departments_ids(user_id):
        """Получить список всех отделов c их ID"""
        kbrd = types.InlineKeyboardMarkup()
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT department_id, department_name " \
              f"FROM UKSTGBot.dbo.Departments with(nolock) " \
              f"WHERE department_id is not null " \
              f"ORDER BY department_name"
        for department in sqlserver_cursor.execute(sql).fetchall():
            kbrd.row(types.InlineKeyboardButton(text=f"{department[1]}", callback_data=f"set_dept;{user_id};{department[0]}"))
        kbrd.row(types.InlineKeyboardButton(text=f"Закрыть", callback_data=f"close_menu"))
        return kbrd

    @staticmethod
    def get_all_professions(user_id):
        """Получить список профессий"""
        kbrd = types.InlineKeyboardMarkup()
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT role_id, role_name " \
              f"FROM UKSTGBot.dbo.UserRoles with(nolock) " \
              f"WHERE role_id <> 0 " \
              f"ORDER BY role_name"
        for role in sqlserver_cursor.execute(sql).fetchall():
            kbrd.row(types.InlineKeyboardButton(text=f"{role[1]}", callback_data=f"set_role;{user_id};{role[0]}"))
        kbrd.row(types.InlineKeyboardButton(text=f"Закрыть", callback_data=f"close_menu"))
        return kbrd

    @staticmethod
    def set_new_role_to_user(user_id, role_id, bot):
        """Установить новую роль"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        if role_id in [1, 2]:
            sql2 = f"UPDATE UKSTGBot.dbo.Users " \
                   f"SET is_spectator = 1 " \
                   f"WHERE user_id = {user_id} "
        elif role_id in [3, 4, 7]:
            sql2 = f"UPDATE UKSTGBot.dbo.Users " \
                   f"SET is_spectator = 0 , can_response = 1 " \
                   f"WHERE user_id = {user_id} "
        elif role_id in [5, 6]:
            sql2 = f"UPDATE UKSTGBot.dbo.Users " \
                   f"SET is_spectator = 0 , can_response = 0 , responser_state_id = 0 " \
                   f"WHERE user_id = {user_id} "
        elif role_id == 10:
            sql2 = f"UPDATE UKSTGBot.dbo.Users " \
                   f"SET is_spectator = 0 , can_response = 0 , responser_state_id = 0 " \
                   f"WHERE user_id = {user_id} "

        sql = f"UPDATE UKSTGBot.dbo.Callider " \
              f"SET role = {role_id} " \
              f"WHERE userlogin = (SELECT userlogin " \
              f"                   FROM UKSTGBot.dbo.Users with(nolock) " \
              f"                   WHERE user_id = {user_id}) "
        sqlserver_cursor.execute(sql)
        sqlserver_cursor.execute(sql2)
        sqlserver_db.commit()
        sql = f"SELECT user_id, can_response, is_spectator " \
              f"FROM UKSTGBot.dbo.Users with(nolock) " \
              f"WHERE user_id = {user_id}"
        user, can_response, is_spectator = sqlserver_cursor.execute(sql).fetchone()
        if is_spectator == 1:
            kbrd = Spectator(user_id).create_keyboard(0)
        elif can_response == 1:
            kbrd = Responser(user_id).create_keyboard(0)
        else:
            kbrd = Requester(user_id).create_keyboard()
        bot.send_message(chat_id=user_id,
                         text="У тебя изменилась роль в боте. Нажми \"Обо мне\", чтобы увидеть новую роль.",
                         reply_markup=kbrd)

    @staticmethod
    def switch_user_role(user_id, new_user_state, new_role):
        """Сменить роль с отвечающего на пингующего и наоборот"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.Users " \
              f"SET can_response = {new_user_state}" \
              f"  , change_state_last_date = getdate()" \
              f"  , responser_state_id = 0 " \
              f"WHERE user_id = {user_id}"
        sqlserver_cursor.execute(sql)
        sql2 = f"UPDATE UKSTGBot.dbo.Callider " \
               f"SET role = {new_role}" \
               f"WHERE userlogin = (select userlogin " \
               f"                   from ukstgbot.dbo.users" \
               f"                   where user_id = {user_id})"
        sqlserver_cursor.execute(sql2)
        sqlserver_db.commit()

    @staticmethod
    def switch_helper_role(user_id, new_user_state, new_role):
        """Сменить роль с отвечающего на пингующего и наоборот"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.Users " \
              f"SET can_response = {new_user_state}" \
              f"  , change_state_last_date = getdate()" \
              f"  , responser_state_id = 0 " \
              f"WHERE user_id = {user_id}"
        sqlserver_cursor.execute(sql)
        sql = f"UPDATE UKSTGBot.dbo.Callider " \
              f"SET role = {new_role}" \
              f"WHERE userlogin = (SELECT userlogin " \
              f"                   FROM UKSTGBot.dbo.Users with(nolock) " \
              f"                   WHERE user_id = {user_id})"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    @staticmethod
    def switch_responser_state(responser_id, state_id):
        """Поменять статус у отвечающего"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.Users " \
              f"SET responser_state_id = {state_id}" \
              f"  , change_state_last_date = getdate() " \
              f"WHERE user_id = {responser_id}"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()
