import pyodbc

from telebot import types

from Settings import CONNECTION_STRING
import Responser


class Spectator(Responser.Responser):
    """Класс, который отвечает за наблюдающие роли (рук-ль и т.п.)"""

    user_id = None
    department = ""
    fullname = ""
    role = ""
    products = {}
    notification_alert_state = None
    get_pings_state = None
    notification_alert_state_name = None
    get_pings_state_name = None
    shift = ""

    @staticmethod
    def is_spectator(user_id):
        """Проверить является ли пользователь наблюдающим"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT u.user_id " \
              f"FROM UKSTGBot.dbo.Users u with(nolock) " \
              f"JOIN UKSTGBot.dbo.Callider c with(nolock) on c.userlogin = u.userlogin " \
              f"WHERE u.user_id = {user_id} " \
              f"  AND u.is_block = 0 " \
              f"  AND u.is_spectator = 1 " \
              f"  AND c.fired = 0 " \
              f"  AND c.role in (1,2)"
        return sqlserver_cursor.execute(sql).fetchone() is not None

    def __init__(self, spectator_id):
        """Ининциализация руководителя / продуктового эксперта"""
        super().__init__(spectator_id)
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT u.user_id " \
              f"  , case when u.notification_alert_state = 0 then 'Нет' else 'Да' end " \
              f"  , case when u.get_pings_state = 0 then 'Нет' else 'Да' end " \
              f"  , c.fullname " \
              f"  , c.department " \
              f"  , ur.role_name " \
              f"  , p.product_id " \
              f"  , p.product_name " \
              f"  , concat(convert(time(0), cs.start_date), ' - ', convert(time(0), cs.end_date)) " \
              f"  , u.notification_alert_state " \
              f"  , u.get_pings_state " \
              f"FROM UKSTGBot.dbo.Users as u with(nolock) " \
              f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = u.userlogin " \
              f"JOIN UKSTGBot.dbo.UserRoles as ur with(nolock) ON ur.role_id = c.role " \
              f"LEFT JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = u.user_id " \
              f"  AND uop.direction = 'response' " \
              f"LEFT JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = uop.product_id " \
              f"LEFT JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
              f"WHERE u.user_id = {spectator_id} " \
              f"  AND u.is_block = 0 " \
              f"  AND u.is_spectator = 1 " \
              f"ORDER BY p.product_name"
        data = sqlserver_cursor.execute(sql).fetchall()
        self.user_id = data[0][0]
        self.fullname = data[0][3]
        self.department = data[0][4]
        self.role = data[0][5]
        self.notification_alert_state_name = data[0][1]
        self.get_pings_state_name = data[0][2]
        self.shift = data[0][8]
        self.notification_alert_state = data[0][9]
        self.get_pings_state = data[0][10]
        for row in data:
            self.products.setdefault(row[6], row[7])
        sqlserver_db.close()

    def to_str(self):
        """Вывести информацию по наблюдающему"""
        info = ""
        for product in self.products.values():
            info += f"{product} , "
        return super().to_str() + f"\nПолучаешь уведомления об очереди : {self.notification_alert_state}\n" \
               f"Получешь пинги : {self.get_pings_state}"

    def create_keyboard(self, change_responser_state=0):
        """Создание клавиатуры после смены статуса"""
        notification_on = types.InlineKeyboardButton(text="Вкл уведомления", callback_data="notification_on")
        notification_off = types.InlineKeyboardButton(text="Выкл уведомления", callback_data="notification_off")
        get_pings = types.InlineKeyboardButton(text="Получать пинги", callback_data="get_pings")
        not_get_pings = types.InlineKeyboardButton(text="Не получать пинги", callback_data="not_get_pings")
        green_state_btn = types.KeyboardButton(text="Сменить статус 🟢")
        red_state_btn = types.KeyboardButton(text="Сменить статус 🔴")

        kbrd = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kbrd.row(types.KeyboardButton(text="Очередь"), types.KeyboardButton(text="Отвечающие"))
        if self.get_pings_state == 1:
            if change_responser_state == 1:
                kbrd.row(red_state_btn, types.KeyboardButton(text="Взять еще пинг"))
            elif self.check_responser_state() == "Зеленый":
                kbrd.row(green_state_btn, types.KeyboardButton(text="Взять еще пинг"))
            else:
                kbrd.row(red_state_btn, types.KeyboardButton(text="Взять еще пинг"))
        kbrd.row(notification_on if self.notification_alert_state == 0 else notification_off
                , get_pings if self.get_pings_state == 0 else not_get_pings)
        kbrd.row(types.KeyboardButton(text="Администрирование")
                , types.KeyboardButton(text="Обо мне"))
        return kbrd

    def switch_notification_alert_state(self):
        """Включить / выключить получение уведомлений об очереди"""
        if self.notification_alert_state == 0:
            new_state = 1
        else:
            new_state = 0

        self.notification_alert_state = new_state

        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.Users " \
              f"SET notification_alert_state = {new_state} " \
              f"WHERE user_id = {self.user_id}"
        sqlserver_cursor.execute(sql).commit()
        sqlserver_db.close()
        return

    def switch_get_pings_state(self):
        """Получить возможность получать / не получать пинги"""
        if self.get_pings_state == 0:
            new_state = 1
        else:
            new_state = 0

        self.get_pings_state = new_state

        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.Users " \
              f"SET get_pings_state = {new_state} " \
              f"  , can_response = {new_state} " \
              f"  , responser_state_id = 0" \
              f"WHERE user_id = {self.user_id}"
        sqlserver_cursor.execute(sql).commit()
        sqlserver_db.close()
        return
