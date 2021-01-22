import pyodbc

from telebot import types

from Settings import CONNECTION_STRING


class Requester(object):
    """Класс, который будет описывать пингующего и его поведение.
    Аннотация @staticmethod указывает на то, что метод можно вызвать только через класс.
    Если перед функцией(методом) ничего не стоит, то такой метод вызывается только у объекта"""
    user_id = None
    fullname = ""
    department = 0
    department_id = 0
    time_zone = 0
    products = dict()

    @staticmethod
    def is_requester(user_id):
        """Проверка на причастность к пингующим"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT u.user_id " \
              f"FROM UKSTGBot.dbo.Users u with(nolock) " \
              f"JOIN UKSTGBot.dbo.Callider c with(nolock) on c.userlogin = u.userlogin " \
              f"WHERE u.user_id = {user_id} " \
              f"  AND u.can_response = 0 " \
              f"  AND u.is_block = 0 " \
              f"  AND u.is_spectator = 0 " \
              f"  AND c.fired = 0 " \
              f"  AND c.role in (5,6)"
        return sqlserver_cursor.execute(sql).fetchone() is not None

    @staticmethod
    def get_products_by_action(user_id, action):
        """Получить клавиатуру со списком доп. продуктов для удаления, которые есть у пингующего"""
        products = []
        kbrd = types.InlineKeyboardMarkup()
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        if action == "add_product":
            call_action = "add_prod"
            sqlserver_sql = f"SELECT p.product_id, p.product_name " \
                            f"FROM UKSTGBot.dbo.Products as p with(nolock) " \
                            f"WHERE p.product_id not in ( " \
                            f"  SELECT product_id " \
                            f"  FROM UKSTGBot.dbo.UserOptionalProducts with(nolock) " \
                            f"  WHERE user_id = {user_id} " \
                            f"    AND direction = 'request' " \
                            f"  UNION " \
                            f"  SELECT dp.product_id " \
                            f"  FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                            f"  JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
                            f"  JOIN UKSTGBot.dbo.Departments as d with(nolock) ON d.department_name = c.department " \
                            f"  JOIN UKSTGBot.dbo.DepartmentProducts as dp with(nolock) ON dp.department_id = d.department_id " \
                            f"  WHERE ud.user_id={user_id} " \
                            f"  UNION " \
                            f"  SELECT 0)"
        else:
            call_action = "rem_prod"
            sqlserver_sql = f"SELECT p.product_id, p.product_name " \
                            f"FROM UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) " \
                            f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = uop.product_id " \
                            f"WHERE uop.user_id = {user_id} " \
                            f"  AND uop.direction = 'request'"
        result = sqlserver_cursor.execute(sqlserver_sql).fetchall()
        if len(result) > 0:
            for product in sorted(result, key=lambda res: res[1]):
                products.append(types.InlineKeyboardButton(text=f"{product[1]}", callback_data=f"{call_action};{user_id};{product[0]};request"))
            while len(products) > 0:
                if len(products) / 2 >= 1:
                    kbrd.row(products.pop(0), products.pop(0))
                else:
                    kbrd.row(products.pop(0))
        kbrd.row(types.InlineKeyboardButton(text="Закрыть", callback_data="close_menu"))
        return kbrd

    def __init__(self, user_id):
        """Констурктор"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT DISTINCT ud.user_id" \
              f"  , c.fullname" \
              f"  , c.department" \
              f"  , d.time_zone" \
              f"  , p.product_id" \
              f"  , p.product_name" \
              f"  , d.department_id " \
              f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
              f"JOIN UKSTGBot.dbo.callider as c with(nolock) ON c.userlogin = ud.userlogin " \
              f"JOIN UKSTGBot.dbo.Departments as d with(nolock) ON d.department_name = c.department " \
              f"LEFT JOIN UKSTGBot.dbo.DepartmentProducts as dp with(nolock) ON dp.department_id = d.department_id " \
              f"LEFT JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = dp.product_id " \
              f"WHERE ud.user_id = {user_id} " \
              f"  AND p.is_active = 1 " \
              f"UNION " \
              f"SELECT DISTINCT ud.user_id" \
              f"  , ''" \
              f"  , ''" \
              f"  , ''" \
              f"  , p.product_id" \
              f"  , p.product_name" \
              f"  , 0 " \
              f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
              f"LEFT JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id " \
              f"LEFT JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = uop.product_id " \
              f"WHERE ud.user_id = {user_id} " \
              f"  AND uop.direction = 'request'" \
              f"ORDER BY fullname DESC"
        result = sqlserver_cursor.execute(sql).fetchall()
        self.user_id = result[0][0]
        self.fullname = result[0][1]
        self.department = result[0][2]
        self.time_zone = result[0][3]
        self.products = dict()
        self.department_id = result[0][6]
        for data in result:
            if data[4] is not None:
                self.products.setdefault(data[4], data[5])

    def to_str(self):
        """Вывод данных о пользователе"""
        products_info = ""
        for product in self.products.values():
            products_info += f"{product} , "
        return f"ID : {self.user_id}\nФИО : {self.fullname}\nОтдел : {self.department}\n" \
               f"Продукты : {products_info[:-2]}"

    def has_active_ping_with_no_comment(self):
        """Проверка на то, что есть хотя бы 1 активный пинг без комментария"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT count(*) " \
              f"FROM UKSTGBot.dbo.ActivePings with(nolock) " \
              f"WHERE requester_id = {self.user_id} " \
              f"  AND comment = ''"
        if sqlserver_cursor.execute(sql).fetchone()[0] > 0:
            return True
        return False

    def has_started_ping(self, flag):
        """Указать, что есть начатай пинг и нельзя отправить еще один, пока не завершишь заполнение предыдущего"""
        if flag == True:
            new_state = 1
        else:
            new_state = 0
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"UPDATE UKSTGBot.dbo.Users " \
              f"SET has_started_ping = {new_state} " \
              f"WHERE user_id = {self.user_id}"
        sqlserver_cursor.execute(sql)
        sqlserver_db.commit()
        return True

    def check_has_started_ping(self):
        """Проверить, что етсь начатай пинг и нельзя отправить еще один, пока не завершишь заполнение предыдущего"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        sql = f"SELECT has_started_ping " \
              f"FROM UKSTGBot.dbo.Users with(nolock) " \
              f"WHERE user_id = {self.user_id}"
        if sqlserver_cursor.execute(sql).fetchone()[0] == 1:
            return True
        return False

    def create_keyboard(self):
        """Создание клавиатуры для пингующего"""
        kbrd = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if self.department_id == 8:
            kbrd.row(types.KeyboardButton(text="Пинг Эксперту"), types.KeyboardButton(text="Пинг Ментору"))
        else:
            kbrd.row(types.KeyboardButton(text="Пинг"))
        kbrd.row(types.KeyboardButton(text="Очередь"))
        kbrd.row(types.KeyboardButton(text="Обо мне"))
        return kbrd

    def create_pings_keyboard(self, section_id=1):
        """Создать клавиатуру с продуктами-пингами для экспертов"""
        kbrd = types.InlineKeyboardMarkup()
        product_btns = []
        if len(self.products.values()) != 0:
            for product_id, product_name in sorted(self.products.items(), key=lambda item: item[1]):
                if product_id not in [700,701,702,703,704,705]:
                    if (section_id in [2, 3, 4, 5, 6] and product_id not in [1, 79976, 3, 4, 5, 22494]) or section_id == 1:
                        if product_id not in [609,610,617,619,620,621,624,625,626,627,628,629,630,631,632]:
                            product_btns.append(types.InlineKeyboardButton(text=product_name
                                                                           , callback_data=f"ping;{section_id};{product_id}"))
                    if section_id == 7 and product_id in [609,610,617,619,620,621,624,625,626,627,628,629,630,631,632]:
                        product_btns.append(types.InlineKeyboardButton(text=product_name
                                                                       , callback_data=f"ping;{section_id};{product_id}"))
            while len(product_btns) > 0:
                if len(product_btns) // 2 > 0:
                    kbrd.row(product_btns.pop(0), product_btns.pop(0))
                elif len(product_btns) == 1:
                    kbrd.row(product_btns.pop(0))
        kbrd.row(types.InlineKeyboardButton(text="Закрыть", callback_data=f"close_menu"))
        return kbrd

    def create_mentor_pings_keyboard(self):
        """Создать клавиатуру с продуктами-пингами для пингов менторов"""
        kbrd = types.InlineKeyboardMarkup()
        product_btns = []
        if len(self.products.values()) != 0:
            for product_id, product_name in sorted(self.products.items(), key=lambda item: item[1]):
                if product_id in range(700, 706):
                    product_btns.append(types.InlineKeyboardButton(text=product_name
                                                                   , callback_data=f"ping;8;{product_id}"))
            while len(product_btns) > 0:
                if len(product_btns) // 2 > 0:
                    kbrd.row(product_btns.pop(0), product_btns.pop(0))
                elif len(product_btns) == 1:
                    kbrd.row(product_btns.pop(0))
        kbrd.row(types.InlineKeyboardButton(text="Закрыть", callback_data=f"close_menu"))
        return kbrd

    def show_pings_in_queue(self):
        """Показывает пинги по продуктам"""
        sqlserver_db = pyodbc.connect(CONNECTION_STRING)
        sqlserver_cursor = sqlserver_db.cursor()
        res_info_sql = f"SELECT p.product_name " \
                       f"  , sum(case when ud.responser_state_id = 1 and cs.start_date is not null then 1 else 0 end) as green " \
                       f"  , sum(case when cs.start_date is not null then 1 else 0 end) as cnt " \
                       f"  , case when for_mentor = 1 then 'К менторам' " \
                       f"    when for_expert = 1 then 'К экспертам' " \
                       f"    else '' end " \
                       f"FROM UKSTGBot.dbo.Users as ud with(nolock) " \
                       f"JOIN UKSTGBot.dbo.UserOptionalProducts as uop with(nolock) ON uop.user_id = ud.user_id" \
                       f"  AND direction = 'response' " \
                       f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = uop.product_id " \
                       f"JOIN UKSTGBot.dbo.Callider as c with(nolock) ON c.userlogin = ud.userlogin " \
                       f"LEFT JOIN UKSTGBot.dbo.CalliderShifts as cs with(nolock) ON cs.callider_id = c.callider_id " \
                       f"  AND getdate() between cs.start_date and cs.end_date " \
                       f"WHERE uop.product_id in (SELECT DISTINCT dp.product_id " \
                       f"                         FROM UKSTGBot.dbo.DepartmentProducts as dp " \
                       f"                         JOIN UKSTGBot.dbo.Departments as d on d.department_id = dp.department_id " \
                       f"                         JOIN UKSTGBot.dbo.Callider as c on c.department = d.department_name " \
                       f"                         JOIN UKSTGBot.dbo.Users as u on u.userlogin = c.userlogin " \
                       f"                         WHERE u.user_id = {self.user_id} " \
                       f"                         UNION" \
                       f"                         SELECT DISTINCT uop.product_id " \
                       f"                         FROM UKSTGBot.dbo.UserOptionalProducts as uop " \
                       f"                         WHERE uop.user_id = {self.user_id} " \
                       f"                           AND uop.direction = 'request') " \
                       f"  AND ud.can_response = 1 " \
                       f"  AND uop.product_id not in (3,4,5,79976,22494,600) " \
                       f"  AND c.role in (2,3,4,7) " \
                       f"GROUP BY p.product_name " \
                       f"  , case when for_mentor = 1 then 'К менторам' " \
                       f"    when for_expert = 1 then 'К экспертам' " \
                       f"    else '' end " \
                       f"ORDER BY case when for_mentor = 1 then 'К менторам' " \
                       f"    when for_expert = 1 then 'К экспертам' " \
                       f"    else '' end " \
                       f"  , p.product_name "
        res_result = sqlserver_cursor.execute(res_info_sql).fetchall()

        req_sql = f"SELECT p.product_name " \
                  f"  , ap.ping_id " \
                  f"  , q_n.cnt  " \
                  f"  , case when for_mentor = 1 then 'К менторам' " \
                  f"    when for_expert = 1 then 'К экспертам' " \
                  f"    else '' end " \
                  f"FROM UKSTGBot.dbo.ActivePings as ap with(nolock) " \
                  f"JOIN UKSTGBot.dbo.Products as p with(nolock) ON p.product_id = ap.product_id " \
                  f"CROSS APPLY (SELECT count(*) as cnt " \
                  f"             FROM UKSTGBot.dbo.ActivePings as app with(nolock) " \
                  f"             WHERE app.ping_id <= ap.ping_id " \
                  f"               AND app.product_id = ap.product_id " \
                  f"               AND app.comment <> '' " \
                  f"               AND app.date_answered IS NULL) as q_n " \
                  f"WHERE ap.requester_id = {self.user_id} " \
                  f"  AND ap.date_answered IS NULL " \
                  f"  AND ap.comment <> '' " \
                  f"ORDER BY case when for_mentor = 1 then 'К менторам' " \
                  f"    when for_expert = 1 then 'К экспертам' " \
                  f"    else '' end " \
                  f"  , p.product_name " \
                  f"  , ap.ping_id "
        req_result = sqlserver_cursor.execute(req_sql).fetchall()

        ttl_pings_sql = f"SELECT p.product_name, isnull(cnt.cnt, 0) " \
                        f"FROM UKSTGBot.dbo.Products as p with(nolock) " \
                        f"LEFT JOIN ( SELECT product_id, count(*) as cnt " \
                        f"            FROM UKSTGBot.dbo.ActivePings with(nolock) " \
                        f"            WHERE date_answered IS NULL " \
                        f"              AND comment <> '' " \
                        f"            GROUP BY product_id ) as cnt ON cnt.product_id = p.product_id"
        ttl_pings_result = sqlserver_cursor.execute(ttl_pings_sql).fetchall()

        if len(ttl_pings_result) > 0:
            ttl_pings = dict()
            for product in ttl_pings_result:
                ttl_pings.setdefault(product[0], product[1])
        if len(req_result) > 0:
            current_role_section = req_result[0][3]
            info = f"---{current_role_section}---\n"
            for product in res_result:
                pings_order = []
                for req in req_result:
                    if req[3] != current_role_section:
                        current_role_section = req[3]
                        info += f"\n---{current_role_section}---\n"
                    if product[0] == req[0]:
                        pings_order.append(str(req[2]))
                if len(pings_order) > 1:
                    print(pings_order)
                    info += f"{product[0]} | {product[1]:<2}🟢 из {product[2]:<2} | " \
                            f"Твои пинги {', '.join(pings_order)} из {ttl_pings[product[0]]:<3}\n"
                elif len(pings_order) == 1:
                    info += f"{product[0]} | {product[1]:<2}🟢 из {product[2]:<2} | " \
                            f"Твой пинг {pings_order[0]} из {ttl_pings[product[0]]:<3}\n"
                pings_order.clear()

        else:
            current_role_section = res_result[0][3]
            info = f"---{current_role_section}---\n"
            for product in res_result:
                if product[3] != current_role_section:
                    current_role_section = product[3]
                    info += f"\n---{current_role_section}---\n"

                info += f"В очереди {ttl_pings[product[0]]:<3} | {product[1]:<2}🟢 из {product[2]:<2} | {product[0]}\n"

        return info
