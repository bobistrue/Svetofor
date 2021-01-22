from datetime import datetime
import pyodbc

from telebot import types

from Settings import CONNECTION_STRING


class Ping(object):
    """Определяем сущность пинга"""
    ping_id = -1
    product_id = 0
    product_name = ""
    comment = ""
    from_helper = 0
    section_id = 4
    section_name = ''
    requester_id = 0
    requester_fullname = ""
    responser_id = 0
    responser_fullname = ""
    ping_state_id = 0
    date_created = ""
    date_sent = ""
    date_answered = ""
    date_closed = ""
    in_work = 0
    message_id = 0

    @staticmethod
    def is_active(ping_id):
        """Проверяем активен ли пинг"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sqlserver_sql = f"SELECT count(*) " \
                        f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
                        f"WHERE ping_id = {ping_id}"
        if sqlserver_cursor.execute(sqlserver_sql).fetchone()[0] > 0:
            return True
        return False

    def to_str(self):
        """Метод для отображения полей пинга исходя из его статуса"""
        ping_data = f"Пинг {self.ping_id}\nРаздел {self.section_name} по продукту {self.product_name}" \
                    f"\nКоментарий {self.comment}\nОтправитель {self.requester_fullname}" \
                    f"\nДата создания {self.date_created}\n"
        if self.ping_state_id == 2:
            ping_data += f"Дата отправки {self.date_sent}\n"
        elif self.ping_state_id == 3:
            ping_data += f"Отвечающий {self.responser_fullname}\n" \
                         f"\nДата ответа {self.date_answered}\n"
        elif self.ping_state_id == 4:
            ping_data += f"Отвечающий {self.responser_fullname}" \
                         f"\nДата закрытия {self.date_closed}\n"
        elif self.ping_state_id == 5:
            ping_data += f"Отвечающий {self.responser_fullname}" \
                         f"\nДата отмены {self.date_closed}\n"
        elif self.ping_state_id == 6:
            ping_data += f"Отвечающий {self.responser_fullname}" \
                         f"\nДата возврата в очередь {self.date_answered}\n"
        elif self.ping_state_id == 7:
            ping_data += f"Отвечающий {self.responser_fullname}" \
                         f"\nДата возврата в очередь {self.date_answered}\n"
        return ping_data

    def add_to_queue(self, sender_id, product_id, message_id, section_id, from_helper=0):
        """Добавление пинга в очередь"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql_counter = "SELECT ping_counter " \
                      "FROM UKSTGBot.dbo.Settings with(nolock)"
        sql_product_name = f"SELECT product_name " \
                           f"FROM UKSTGBot.dbo.Products with(nolock) " \
                           f"WHERE product_id={product_id}"
        sql_fullname = f"SELECT c.fullname " \
                       f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                       f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
                       f"WHERE ud.user_id={sender_id}"
        sql_section_name = f"SELECT section_name " \
                           f"FROM UKSTGBot.dbo.Sections with(nolock) " \
                           f"WHERE section_id={section_id}"
        ping_counter = sqlserver_cursor.execute(sql_counter).fetchone()[0]
        product_name = sqlserver_cursor.execute(sql_product_name).fetchone()[0]
        requester_fullname = sqlserver_cursor.execute(sql_fullname).fetchone()[0]
        section_name = sqlserver_cursor.execute(sql_section_name).fetchone()[0]

        self.ping_id = ping_counter
        self.product_id = product_id
        self.product_name = product_name
        self.section_id = section_id
        self.section_name = section_name
        self.requester_id = sender_id
        self.requester_fullname = requester_fullname
        self.ping_state_id = 1
        self.date_created = datetime.now()
        self.from_helper = from_helper

        sql = f"INSERT INTO UKSTGBot.dbo.ActivePings " \
              f"(ping_id, section_id, product_id, comment, requester_id, responser_id, ping_state_id" \
              f", date_created, date_sent, date_answered, date_closed, message_id, from_helper) " \
              f"VALUES " \
              f"({self.ping_id}, {self.section_id}, {self.product_id}, '', {self.requester_id}, 0" \
              f", 1, getdate(), null, null, null, {message_id}, {from_helper})"
        sqlserver_cursor.execute(sql)

        sql_update_counter = "UPDATE UKSTGBot.dbo.Settings " \
                             "SET ping_counter = ping_counter + 1"
        sqlserver_cursor.execute(sql_update_counter)
        sqlserver_db.commit()

    def add_comment(self, text):
        """Добавить комментарий от отправившего"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        text = text.replace("*", " ").replace("_", " ").replace("[", " ").replace("]", " ").replace("(", " ").replace(")", " ").replace("`", " ").replace("'", " ")
        sql = f"UPDATE UKSTGBot.dbo.ActivePings " \
              f"SET comment = '{text}' " \
              f"WHERE ping_id = {self.ping_id} "
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()

    def answer_keyboard(self, ping_id):
        """Создание клавиатуры для ответа"""
        kbrd = types.InlineKeyboardMarkup()
        kbrd.row(types.InlineKeyboardButton(text="Ответить", callback_data=f"answ;{ping_id}")
                 , types.InlineKeyboardButton(text="Вернуть в очередь", callback_data=f"transmit;{ping_id}"))
        return kbrd

    def fill_active_ping(self, ping_id):
        """Получить пинг по его ID"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT pa.ping_id" \
              f"  , s.section_id" \
              f"  , s.section_name" \
              f"  , pa.product_id" \
              f"  , p.product_name" \
              f"  , pa.comment" \
              f"  , pa.requester_id" \
              f"  , req.fullname" \
              f"  , pa.responser_id" \
              f"  , res.fullname" \
              f"  , pa.ping_state_id" \
              f"  , pa.date_created" \
              f"  , pa.date_sent" \
              f"  , pa.date_answered" \
              f"  , pa.date_closed" \
              f"  , pa.from_helper" \
              f"  , pa.message_id " \
              f"FROM UKSTGBot.dbo.ActivePings as pa with(nolock) " \
              f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = pa.product_id " \
              f"JOIN UKSTGBot.dbo.Users as requd with(nolock) ON requd.user_id = pa.requester_id " \
              f"JOIN UKSTGBot.dbo.Callider as req with(nolock) ON req.userlogin = requd.userlogin " \
              f"JOIN UKSTGBot.dbo.Sections as s with(nolock) ON s.section_id = pa.section_id " \
              f"LEFT JOIN UKSTGBot.dbo.Users as resud with(nolock) ON resud.user_id = pa.responser_id " \
              f"LEFT JOIN UKSTGBot.dbo.Callider as res with(nolock) ON res.userlogin = resud.userlogin " \
              f"WHERE pa.ping_id = {ping_id}"
        self.fill_ping(sqlserver_cursor.execute(sql).fetchone(), True)

    def fill_archive_ping(self, ping_id):
        """Получить пинг по его ID"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT pa.ping_id" \
              f"  , s.section_id" \
              f"  , s.section_name" \
              f"  , pa.product_id" \
              f"  , p.product_name" \
              f"  , pa.comment" \
              f"  , pa.requester_id" \
              f"  , req.fullname" \
              f"  , pa.responser_id" \
              f"  , res.fullname" \
              f"  , pa.ping_state_id" \
              f"  , pa.date_created" \
              f"  , pa.date_sent" \
              f"  , pa.date_answered" \
              f"  , pa.date_closed" \
              f"  , pa.from_helper " \
              f"FROM UKSTGBot.dbo.ArchivePings as pa with(nolock) " \
              f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = pa.product_id " \
              f"JOIN UKSTGBot.dbo.Users as requd with(nolock) ON requd.user_id = pa.requester_id " \
              f"JOIN UKSTGBot.dbo.Callider as req with(nolock) ON req.userlogin = requd.userlogin " \
              f"JOIN UKSTGBot.dbo.Sections as s with(nolock) ON s.section_id = pa.section_id " \
              f"LEFT JOIN UKSTGBot.dbo.Users as resud with(nolock) ON resud.user_id = pa.responser_id " \
              f"LEFT JOIN UKSTGBot.dbo.Callider as res with(nolock) ON res.userlogin = resud.userlogin " \
              f"WHERE pa.ping_id = {ping_id}"
        self.fill_ping(sqlserver_cursor.execute(sql).fetchone(), False)

    def fill_ping(self, data, is_active):
        """Заполнить пинг данными из массива"""
        if is_active:
            self.ping_id, self.section_id, self.section_name, self.product_id, self.product_name, self.comment, \
            self.requester_id, self.requester_fullname, self.responser_id, self.responser_fullname, self.ping_state_id, \
            self.date_created, self.date_sent, self.date_answered, self.date_closed, self.from_helper, self.message_id = data
        else:
            self.ping_id, self.section_id, self.section_name, self.product_id, self.product_name, self.comment, \
            self.requester_id, self.requester_fullname, self.responser_id, self.responser_fullname, self.ping_state_id, \
            self.date_created, self.date_sent, self.date_answered, self.date_closed, self.from_helper = data

    def update_ping_state(self, new_state_id=0, responser_id=0, message_id=0):
        """Обновляем статус пинга на новый"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        if new_state_id == 0:
            sqlserver_sql = f"UPDATE UKSTGBot.dbo.ActivePings " \
                            f"SET message_id = {message_id} " \
                            f"WHERE ping_id = {self.ping_id}"
        elif new_state_id == 2:
            sqlserver_sql = f"UPDATE UKSTGBot.dbo.ActivePings " \
                            f"SET ping_state_id = 2" \
                            f"  , date_sent = getdate()" \
                            f"  , date_answered = null" \
                            f"  , responser_id = {responser_id}" \
                            f"  , in_work = 1" \
                            f"  , notification_datetime = getdate() " \
                            f"WHERE ping_id = {self.ping_id}"
            self.ping_state_id = 2
            self.responser_id = responser_id
            self.date_sent = datetime.now()
        elif new_state_id == 3:
            sqlserver_sql = f"UPDATE UKSTGBot.dbo.ActivePings " \
                            f"SET ping_state_id = 3" \
                            f"  , date_answered = getdate()" \
                            f"  , date_closed = null " \
                            f"WHERE ping_id = {self.ping_id}"
            self.ping_state_id = 3
            self.responser_id = responser_id
            self.date_answered = datetime.now()
        elif new_state_id in [4, 8, 9, 10, 11]:
            sqlserver_sql = f"UPDATE UKSTGBot.dbo.ActivePings " \
                            f"SET ping_state_id = {new_state_id}" \
                            f"  , date_closed = getdate() " \
                            f"WHERE ping_id = {self.ping_id}"
            self.ping_state_id = new_state_id
            self.date_closed = datetime.now()
        elif new_state_id == 5:
            sqlserver_sql = f"UPDATE UKSTGBot.dbo.ActivePings " \
                            f"SET ping_state_id = {new_state_id} " \
                            f"  , date_closed = getdate() " \
                            f"WHERE ping_id = {self.ping_id}"
            self.ping_state_id = new_state_id
            self.date_closed = datetime.now()
        elif new_state_id in [6, 7]:
            sqlserver_sql = f"UPDATE UKSTGBot.dbo.ActivePings " \
                            f"SET ping_state_id = {new_state_id}" \
                            f"  , date_answered = getdate()" \
                            f"  , notification_datetime = null " \
                            f"WHERE ping_id = {self.ping_id}"
            self.ping_state_id = new_state_id
            self.date_answered = datetime.now()
        sqlserver_cursor.execute(sqlserver_sql)
        sqlserver_db.commit()
        return True

    def return_to_queue(self):
        """Вернуть пинг в очередь"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sqlserver_insert = f"INSERT INTO UKSTGBot.dbo.ArchivePings " \
                           f"(ping_id, section_id, product_id, comment, requester_id, responser_id, ping_state_id" \
                           f", date_created, date_sent, date_answered, date_closed, from_helper) " \
                           f"VALUES " \
                           f"({self.ping_id}, {self.section_id}, {self.product_id}, '{self.comment}', {self.requester_id}, " \
                           f"{self.responser_id}, {self.ping_state_id}" \
                           f", '{self.date_created}'" \
                           f", iif('{self.date_sent}' = 'None', null, '{self.date_sent}')" \
                           f", iif('{self.date_answered}' = 'None', null, '{self.date_answered}')" \
                           f", iif('{self.date_closed}' = 'None', null, '{self.date_closed}')" \
                           f", {self.from_helper})"
        sqlserver_cursor.execute(sqlserver_insert)

        sql_update = f"UPDATE UKSTGBot.dbo.ActivePings " \
                     f"SET responser_id = 0" \
                     f"  , ping_state_id = 1" \
                     f"  , date_sent = null" \
                     f"  , date_answered = null" \
                     f"  , in_work = 0 " \
                     f"WHERE ping_id = {self.ping_id}"
        sqlserver_cursor.execute(sql_update)
        sqlserver_db.commit()

    def close(self):
        """Закрыть и поместить пинг в архив"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sqlserver_insert = f"INSERT INTO UKSTGBot.dbo.ArchivePings " \
                           f"(ping_id, section_id, product_id, comment, requester_id, responser_id, ping_state_id" \
                           f", date_created, date_sent, date_answered, date_closed, from_helper) " \
                           f"VALUES " \
                           f"({self.ping_id} " \
                           f", {self.section_id} " \
                           f", {self.product_id} " \
                           f", '{self.comment}' " \
                           f", {self.requester_id} " \
                           f", {self.responser_id} " \
                           f", {self.ping_state_id} " \
                           f", convert(datetime2(0), '{self.date_created}') " \
                           f", iif('{self.date_sent}' = 'None', null, '{self.date_sent}') " \
                           f", iif('{self.date_answered}' = 'None', null, '{self.date_answered}') " \
                           f", '{self.date_closed}' " \
                           f", {self.from_helper})"
        sqlserver_cursor.execute(sqlserver_insert)

        sqlserver_delete = f"DELETE FROM UKSTGBot.dbo.ActivePings " \
                           f"WHERE ping_id = {self.ping_id}"
        sqlserver_cursor.execute(sqlserver_delete)
        sqlserver_db.commit()
