import threading
import re

import telebot
from telebot import types

from Helper import Helper
from Responser import Responser
from Requester import Requester
from Spectator import Spectator
from WFM import WFM
from Ping import Ping
from Settings import TOKEN
from test_tinyurl import make_tiny


def main(bot):

    @bot.message_handler(commands=["start"])
    def start_handler(msg):
        """Обработчик команды /start"""
        if not Helper.auth(msg.from_user.id):
            bot.send_message(chat_id=msg.from_user.id
                             , text=f"Я тебя не знаю\n"
                                    f"Твой ID - {msg.from_user.id}\n" \
                                    f"Пройди регистрацию нажав -> /addmeplease")
        else:
            if Requester.is_requester(msg.from_user.id):
                try:
                    requester = Requester(msg.from_user.id)
                except:
                    bot.send_message(chat_id=msg.from_user.id
                                     , text="Что-то пошло не так. Пиши @bobistry , будем разбираться =(")
                    return
                bot.send_message(chat_id=msg.from_user.id
                                 , text="Привет, проверь свои продукты и, если все нормально, то можешь начать пинговать."
                                 , reply_markup=requester.create_keyboard())
                return
            elif Spectator.is_spectator(msg.from_user.id):
                spectator = Spectator(msg.from_user.id)
                kbrd = spectator.create_keyboard(change_responser_state=0)
            elif WFM.is_wfm(msg.from_user.id):
                wfm = WFM(msg.from_user.id)
                kbrd = wfm.create_keyboard()
            else:
                responser = Responser(msg.from_user.id)
                kbrd = responser.create_keyboard(change_responser_state=0)
            bot.send_message(chat_id=msg.from_user.id
                             , text="Привет, проверь свои продукты и, если все нормально, переходи в \"Зеленый\", "
                                    "чтобы начать отвечать на пинги."
                             , reply_markup=kbrd)

    @bot.message_handler(commands=["addmeplease"])
    def addmeplease_handler(msg):
        """Обработчик команды /addmeplease"""
        if not Helper.auth(msg.from_user.id):
            bot.send_message(chat_id=msg.from_user.id
                             , text="Введи свой рабочий LOGIN (обычно он как почта, только без @xxx.ru)")

    @bot.message_handler(commands=["products"])
    def list_handler(msg):
        """Обработчик команды /products"""
        if Helper.auth(msg.from_user.id):
            bot.send_message(chat_id=msg.from_user.id
                             , text=Helper.get_all_products())

    @bot.message_handler(commands=["departments"])
    def departments_handler(msg):
        """Обработчик команды /departments"""
        if Helper.auth(msg.from_user.id):
            bot.send_message(chat_id=msg.from_user.id
                             , text=Helper.get_all_departments())

    @bot.message_handler(commands=["srr"])
    def switchrole_handler(msg):
        """Обработчик команды /switchrole , которая нужна для супервизоров чтобы переходить из пингующих в отвечающие"""
        if Helper.auth(msg.from_user.id):
            if Responser.is_responser(msg.from_user.id):
                requester = Requester(msg.from_user.id)
                Helper.switch_user_role(msg.from_user.id, 0, 5)
                bot.send_message(chat_id=msg.from_user.id
                                 , text="Теперь твоя роль - пингующий"
                                 , reply_markup=requester.create_keyboard())
                Helper.write_log(msg.from_user.id, -1, "Команда /sr (перешел к пингующим)")
            else:
                if Spectator.is_spectator(msg.from_user.id):
                    spectator = Spectator(msg.from_user.id)
                    kbrd = spectator.create_keyboard(change_responser_state=0)
                    new_role = 1
                else:
                    responser = Responser(msg.from_user.id)
                    kbrd = responser.create_keyboard(change_responser_state=0)
                    new_role = 3
                Helper.switch_user_role(msg.from_user.id, 1, new_role)
                bot.send_message(chat_id=msg.from_user.id
                                 , text="Теперь твоя роль - отвечающий"
                                 , reply_markup=kbrd)
                Helper.write_log(msg.from_user.id, -1, "Команда /sr (перешел к отвечающим)")

    @bot.message_handler(commands=["switchrole", "sr"])
    def switchrole_handler(msg):
        """Обработчик команды /switchrole , которая нужна для супервизоров чтобы переходить из пингующих в отвечающие"""
        if Helper.auth(msg.from_user.id) and not Helper.is_cons(msg.from_user.id):
            if Responser.is_responser(msg.from_user.id):
                requester = Requester(msg.from_user.id)
                Helper.switch_user_role(msg.from_user.id, 0, 5)
                bot.send_message(chat_id=msg.from_user.id
                                 , text="Теперь твоя роль - пингующий"
                                 , reply_markup=requester.create_keyboard())
                Helper.write_log(msg.from_user.id, -1, "Команда /sr (перешел к пингующим)")
            else:
                if Spectator.is_spectator(msg.from_user.id):
                    spectator = Spectator(msg.from_user.id)
                    kbrd = spectator.create_keyboard(change_responser_state=0)
                    new_role = 1
                else:
                    responser = Responser(msg.from_user.id)
                    kbrd = responser.create_keyboard(change_responser_state=0)
                    new_role = 3
                Helper.switch_user_role(msg.from_user.id, 1, new_role)
                bot.send_message(chat_id=msg.from_user.id
                                 , text="Теперь твоя роль - отвечающий"
                                 , reply_markup=kbrd)
                Helper.write_log(msg.from_user.id, -1, "Команда /sr (перешел к отвечающим)")

    @bot.message_handler(commands=["exptp", "argos"])
    def switchrole_special_cons_handler(msg):
        """Обработчик команды /exptp и /argos , которые нужны некоторым сотрудникам,
        чтобы переходить из пингующих в отвечающие"""
        if Responser.is_responser(msg.from_user.id):
            requester = Requester(msg.from_user.id)
            Helper.switch_helper_role(msg.from_user.id, 0, 5)
            bot.send_message(chat_id=msg.from_user.id
                             , text="Теперь твоя роль - пингующий"
                             , reply_markup=requester.create_keyboard())
        else:
            responser = Responser(msg.from_user.id)
            Helper.switch_helper_role(msg.from_user.id, 1, 7)
            bot.send_message(chat_id=msg.from_user.id
                             , text="Теперь твоя роль - отвечающий"
                             , reply_markup=responser.create_keyboard(change_responser_state=0))

    @bot.message_handler(content_types=["photo"])
    def pics_handler(msg):
        """Обработчик для пингующих с активным пингом и изображением"""
        if Helper.is_cons(msg.from_user.id):
            requester = Requester(msg.from_user.id)
            if requester.has_active_ping_with_no_comment():
                bot.send_message(chat_id=msg.from_user.id
                                 , text="Отправь комментарий текстом. Изображения не принимаются.")

    @bot.message_handler(content_types=["text"])
    def text_handler(msg):
        """Обработчик сообщений от пользователя"""
        text = msg.text
        user_id = msg.from_user.id

        if msg.text.startswith("Стас слово молвит") and msg.from_user.id in [1350082329, 204943232, 241685834]:
            if msg.text.startswith("Стас слово молвит пингующим"):
                # тут можно проверять на is_spectator чтобы отправялть еще сообщения "Смотрящим"
                for target_user_id in Helper.get_all_users_id(can_response=0):
                    try:
                        bot.send_message(chat_id=target_user_id
                                         , text=f"{msg.text[28:]}")
                    except Exception as e:
                        print(f"{target_user_id} - {e}")
            elif msg.text.startswith("Стас слово молвит отвечающим"):
                for target_user_id in Helper.get_all_users_id(can_response=1):
                    try:
                        bot.send_message(chat_id=target_user_id
                                         , text=f"{msg.text[29:]}")
                    except Exception as e:
                        print(f"{target_user_id} - {e}")
            return

        if msg.chat.type == "private":
            if not Helper.auth(user_id):
                if Helper.is_exist_login(text):
                    Helper.write_log(user_id, -1, f'Поптыка регистрации под логином {text}')
                    Helper.add_new_user(user_id, text)
                    Helper.write_log(user_id, -1, f'Успешная регистрация под логином {text}')
                    bot.send_message(chat_id=user_id
                                     , text="Теперь ты в банде! Нажмин на -> /start .")
                    return
                else:
                    bot.send_message(chat_id=user_id
                                     , text="Учетная запись с таким логином уже есть либо логин введен неправильно."
                                            "\nВозможно была введена электронная почта, тогда нужно ввести часть почты до \"@\""
                                            "\n\n Например\nвместо ivanov.ii@skbkontur нужно только ivanov.ii ")
                    return

            elif Helper.auth(user_id):
# ---------------------------------------------
# СЕКЦИЯ КОМАНД НАБЛЮДАЮЩИХ
# ---------------------------------------------
                if Spectator.is_spectator(user_id):
                    spectator = Spectator(user_id)
                    if text == "Вкл уведомления":
                        spectator.switch_notification_alert_state()
                        bot.send_message(chat_id=spectator.user_id
                                         , text="Теперь тебе будут приходить уведомления об очереди"
                                         , reply_markup=spectator.create_keyboard())
                        return

                    elif text == "Выкл уведомления":
                        spectator.switch_notification_alert_state()
                        bot.send_message(chat_id=spectator.user_id
                                         , text="Теперь тебе не будут приходить уведомления об очереди"
                                         , reply_markup=spectator.create_keyboard())
                        return

                    elif text == "Получать пинги":
                        spectator.switch_get_pings_state()
                        bot.send_message(chat_id=spectator.user_id
                                         , text="Теперь тебе будут приходить пинги"
                                         , reply_markup=spectator.create_keyboard())
                        return

                    elif text == "Не получать пинги":
                        spectator.switch_get_pings_state()
                        bot.send_message(chat_id=spectator.user_id
                                         , text="Теперь тебе не будут приходить пинги"
                                         , reply_markup=spectator.create_keyboard())
                        return
                    elif text == "Очередь":
                        bot.send_message(chat_id=spectator.user_id
                                         , text=spectator.show_pings_in_queue())
                        return

                    elif text == "Обо мне":
                        bot.send_message(chat_id=spectator.user_id
                                         , text=spectator.to_str())
                        return

                    elif text == "Отвечающие":
                        bot.send_message(chat_id=spectator.user_id
                                         , text=Helper.get_responsers_who_answered(msg.from_user.id, 'spectator'))
                        return

                    elif text == "Взять еще пинг":
                        if not Helper.get_additional_ping(bot, spectator.user_id):
                            answer = "Пока новых пингов нет..."
                            bot.send_message(chat_id=spectator.user_id
                                             , text=answer)
                        return

                    elif text.startswith("Сменить статус"):
                        spectator.switch_state()
                        bot.send_message(chat_id=spectator.user_id
                                         , text=f"Теперь статус: {spectator.check_responser_state()}"
                                         , reply_markup=spectator.create_keyboard())
                        Helper.write_log(spectator.user_id, -1, f"Вручную изменён статус на {spectator.check_responser_state()}")
                        return

                    elif text.startswith("Администрирование"):
                        bot.send_message(chat_id=spectator.user_id
                                         , text="Выбери нужную команду:"
                                         , reply_markup=spectator.create_commands_keyboard())
                        return

                    elif text.lower().startswith("найти") and not Helper.is_cons(msg.from_user.id):
                        try:
                            _, last_name, first_name = text.split(" ")
                            bot.send_message(chat_id=msg.from_user.id
                                             , text="Выбери нужного сотрудника"
                                             , reply_markup=Helper.get_users_by_fullname(last_name, first_name))
                            return
                        except Exception as e:
                            bot.send_message(chat_id=1350082329
                                             , text=f"Произошла ошибка у {spectator.fullname} при нажатии на Отвечающие. Ошибка:\n\n{e}")

                    # ----------------------------- поиск данных по номеру инцидента
                    elif text.isdigit() and len(text) == 8:
                        results = Helper.get_pings_by_incident(text)
                        for result in results:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text=result)
                        return

                    # ---------------------------- поиск пинга по номер (вид #sXXXXX)
                    elif text.startswith("#s"):
                        ping_id = text[2:].strip()
                        results = Helper.get_pings_by_ping_id(ping_id)
                        for result in results:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text=result)
                        return

                    # ---------------------------- поиск пингов по ФИО пингующего
                    else:
                        results = Helper.get_pings_by_requester_fullname(text)
                        for result in results:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text=result)
                        return
                    return
# ---------------------------------------------
# СЕКЦИЯ КОМАНД WFM
# ---------------------------------------------
                if WFM.is_wfm(user_id):
                    wfm = WFM(user_id)
                    if text == "Очередь":
                        bot.send_message(chat_id=wfm.user_id
                                         , text=wfm.show_pings_in_queue())
                        return

                    elif text == "Обо мне":
                        bot.send_message(chat_id=wfm.user_id
                                         , text=wfm.to_str())
                        return

                    # ----------------------------- поиск данных по номеру инцидента
                    elif text.isdigit() and len(text) == 8:
                        results = Helper.get_pings_by_incident(text)
                        for result in results:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text=result)
                        return

                    # ---------------------------- поиск пингов по ФИО пингующего
                    else:
                        results = Helper.get_pings_by_requester_fullname(text)
                        for result in results:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text=result)
                        return
                    return
# ---------------------------------------------
# СЕКЦИЯ КОМАНД ОТВЕЧАЮЩИХ И НАБЛЮДАЮЩИХ
# ---------------------------------------------
                if Responser.is_responser(user_id):
                    responser = Responser(user_id)
                    if text == "Очередь":
                        bot.send_message(chat_id=responser.user_id
                                         , text=responser.show_pings_in_queue())
                        return

                    elif text == "Обо мне":
                        bot.send_message(chat_id=responser.user_id
                                         , text=responser.to_str())
                        return

                    elif text == "Отвечающие":
                        bot.send_message(chat_id=responser.user_id
                                         , text=Helper.get_responsers_who_answered(msg.from_user.id, 'responser'))
                        return

                    elif text == "Взять еще пинг":
                        if not Helper.get_additional_ping(bot, responser.user_id):
                            answer = "Пока новых пингов нет..."
                            bot.send_message(chat_id=responser.user_id
                                             , text=answer)
                        return

                    elif text.startswith("Сменить статус"):
                        responser.switch_state()
                        bot.send_message(chat_id=responser.user_id
                                         , text=f"Теперь статус: {responser.check_responser_state()}"
                                         , reply_markup=responser.create_keyboard(change_responser_state=0))
                        Helper.write_log(responser.user_id, -1, f"Вручную изменён статус на {responser.check_responser_state()}")
                        return

                    elif text.startswith("Администрирование"):
                        if not Helper.is_cons(msg.from_user.id):
                            bot.send_message(chat_id=responser.user_id
                                             , text="Выбери нужную команду:"
                                             , reply_markup=responser.create_commands_keyboard())
                        else:
                            bot.send_message(chat_id=responser.user_id
                                             , text="Для тебя команды недоступны")
                        return

                    elif text.lower().startswith("найти") and not Helper.is_cons(msg.from_user.id):
                        try:
                            _, last_name, first_name = text.split(" ")
                            bot.send_message(chat_id=msg.from_user.id
                                             , text="Выбери нужного сотрудника"
                                             , reply_markup=Helper.get_users_by_fullname(last_name, first_name))
                            return
                        except Exception as e:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text="Введи команду в формате 'найти Фамилия Имя'")

                    # ----------------------------- поиск данных по номеру инцидента
                    elif text.isdigit() and len(text) == 8:
                        try:
                            results = Helper.get_pings_by_incident(text)
                            for result in results:
                                bot.send_message(chat_id=msg.from_user.id
                                                 , text=result)
                        except:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text=f"Не найдены пинги по инциденту {text}")
                        return

                    # ---------------------------- поиск пинга по номер (вид #sXXXXX)
                    elif text.startswith("#s"):
                        try:
                            ping_id = text[2:].strip()
                            results = Helper.get_pings_by_ping_id(ping_id)
                            for result in results:
                                bot.send_message(chat_id=msg.from_user.id
                                                 , text=result)
                        except:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text=f"Не найден пинг {text}")
                        return

                    # ---------------------------- поиск пингов по ФИО пингующего
                    else:
                        try:
                            results = Helper.get_pings_by_requester_fullname(text)
                            for result in results:
                                bot.send_message(chat_id=msg.from_user.id
                                                 , text=result)
                        except Exception as e:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text=f"Не найдены пинги от {text}")
                            bot.send_message(chat_id=1350082329
                                             , text=f"{e}")
                        return
                    return
# ---------------------------------------------
# СЕКЦИЯ КОМАНД ПИНГУЮЩИХ
# ---------------------------------------------
                if Requester.is_requester(user_id):
                    try:
                        requester = Requester(user_id)
                    except:
                        bot.send_message(chat_id=msg.from_user.id
                                         , text="Что-то пошло не так. Напиши @bobistry , будем разбираться =(")
                        return
                    if text == "Очередь":
                        try:
                            bot.send_message(chat_id=user_id
                                             , text=requester.show_pings_in_queue())
                        except Exception as e:
                            bot.send_message(chat_id=user_id
                                             , text="Произошла ошибка. Ответственные уже в курсе.")
                            bot.send_message(chat_id=1350082329
                                             , text=f"{requester.fullname} из {requester.department} не может посмотреть на пинги в очереди\n\n{e}")
                        return

                    if text == "Обо мне":
                        bot.send_message(chat_id=requester.user_id
                                         , text=requester.to_str())
                        return

                    if text in ["Пинг Эксперту", "Пинг"]:
                        if not requester.check_has_started_ping():
                            bot.send_message(chat_id=user_id
                                             , text="Выбери тип пинга"
                                             , reply_markup=requester.create_pings_keyboard())
                        else:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text="У тебя пинг без комментария. Возможно произошла ошибка и твой коментарий не прикрепился... "
                                                    "Тебе нужно написать \"неактуально\" и попробовать пингануть ещё раз или попросить эксперта или ментора спасти тебя")
                        return

                    if text == "Пинг Ментору":
                        if not requester.check_has_started_ping():
                            bot.send_message(chat_id=user_id
                                             , text="Выбери тип пинга для ментора"
                                             , reply_markup=requester.create_mentor_pings_keyboard())
                        else:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text="У тебя пинг без комментария. Возможно произошла ошибка и твой коментарий не прикрепился... "
                                                    "Тебе нужно написать \"неактуально\" и попробовать пингануть ещё раз или попросить эксперта или ментора спасти тебя")
                        return

                    if requester.has_active_ping_with_no_comment() and text.lower() != 'пинг':
                        ping = Ping()
                        ping.fill_active_ping(Helper.get_last_ping_id_by_user_id(user_id))
                        try:
                            ping.add_comment(text)
                        except Exception as e:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text="Не удалось добавить комментарий. Напиши @bobistry и будем решать вопрос.")
                            return

                        kbrd = types.InlineKeyboardMarkup()
                        kbrd.row(types.InlineKeyboardButton(text="Отменить", callback_data=f"cancel;{ping.ping_id}"))

                        try:
                            bot.edit_message_text(chat_id=user_id
                                                  , message_id=ping.message_id
                                                  , text=f"Продукт {ping.product_name}\nПингу присвоен номер #s{ping.ping_id}\n"
                                                         f"Пингов в очереди: {Helper.get_product_queue(ping.product_id) } шт.\n"
                                                         f"Поместил пинг в очередь.\n\nНажми \"Отменить\", чтобы отменить пинг. "
                                                  , reply_markup=kbrd)
                        except:
                            bot.send_message(chat_id=msg.from_user.id
                                             , text="Что-то пошло неправильно. Напиши @bobistry, спасибо.")
                        ping.update_ping_state(message_id=ping.message_id)
                        requester.has_started_ping(False)
                        Helper.write_log(requester.user_id, -1, f"Добавлен комментарий к пингу №{ping.ping_id}")
                        return
# ---------------------------------------------
# НАЧАЛО СЕКЦИИ С КОНТУР.ШКОЛОЙ для УЦ
# ---------------------------------------------
                    if text.find("@") != -1:
                        school = types.InlineKeyboardMarkup()
                        zayavki_button = types.InlineKeyboardButton(
                            text="Заявки",
                            url=f"https://cms-school.kontur.ru/Default.aspx?Module=Order&f-0=Email-And-Contains"
                                f"-{text[:text.index('@')]}%40{text[text.index('@') + 1:]}")
                        anketa_button = types.InlineKeyboardButton(
                            text="Анкета",
                            url=f"https://cms-school.kontur.ru/Default.aspx?Module=CourseListener&f-0=MembershipId-And-Contains-{text[:text.index('@')]}%40{text[text.index('@') + 1:]}")
                        user_button = types.InlineKeyboardButton(
                            text="Пользователь",
                            url=f"https://cms-school.kontur.ru/Default.aspx?Module=Membership&f-0=Email-And-Contains-{text[:text.index('@')]}%40{text[text.index('@') + 1:]}")
                        test_button = types.InlineKeyboardButton(
                            text="Тесты",
                            url=f"https://cms-school.kontur.ru/Default.aspx?Module=SelfTestAttempt&f-0=MembershipId-And-Contains-{text[:text.index('@')]}%40{text[text.index('@') + 1:]}")
                        school.row(user_button)
                        school.row(anketa_button)
                        school.row(zayavki_button)
                        school.row(test_button)
                        bot.send_message(chat_id=msg.from_user.id
                                         , text="Твои ссылки на ученика К.Школы"
                                         , reply_markup=school)

                        # ПОИСК ПО ИНН
                    elif re.findall(r'^\d{10,12}$', text):
                        school = types.InlineKeyboardMarkup()
                        zayavki_button = types.InlineKeyboardButton(
                            text="Заявки",
                            url=f'https://cms-school.kontur.ru/Default.aspx?Module=Order&f-0=Inn-And-Contains-{text[:]}')
                        user_button = types.InlineKeyboardButton(
                            text="Пользователь",
                            url=f'https://cms-school.kontur.ru/Default.aspx?Module=Membership&f-0=Inn-And-Contains-{text[:]}')
                        school.row(zayavki_button, user_button)
                        bot.send_message(chat_id=msg.from_user.id
                                         , text="Твои ссылки на ученика К.Школы"
                                         , reply_markup=school)

                        # ПОИСК ПО СЧЕТУ
                    elif text.startswith("УЦ"):
                        school = types.InlineKeyboardMarkup()
                        school.row(types.InlineKeyboardButton(text="Заявки"
                                                              , url=f'https://cms-school.kontur.ru/Default.aspx?Module=Order&f-0=AccountNumber-And-Contains-%D0%A3%D0%A6{text[2:]}'))
                        bot.send_message(chat_id=msg.from_user.id
                                         , text="Ссылка на заявку К.Школы"
                                         , reply_markup=school)
# ---------------------------------------------
# КОНЕЦ СЕКЦИИ С КОНТУР.ШКОЛОЙ для УЦ
# ---------------------------------------------
                else:
                    bot.send_message(chat_id=user_id
                                     , text="Если тебе надо работать с ботом, но ты видишь это сообщение, то подойди к супервизору.")


    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        """Обработич inline кнопок"""
# ---------------------------------------------
# НАЧАЛО СЕКЦИИ ОБРАБОТКИ ПИНГОВ
# ---------------------------------------------
        # 1. Создание пинга = поместить пинг в "очередь" без комментария
        if call.data.startswith("ping"):
            _, section_id, product_id = call.data.split(";")

            if not Helper.check_active_responser_by_products(product_id, call.from_user.id):
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text=f"Сейчас отвечающие не работают, попробуй пингануть позже...")
                return

            if product_id == "4":
                requester = Requester(call.from_user.id)
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text="Выбери продукт по Вопросам подключения :"
                                      , reply_markup=requester.create_pings_keyboard(section_id=2))
            elif product_id == "5":
                requester = Requester(call.from_user.id)
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text="Выбери продукт по Общей консультации :"
                                      , reply_markup=requester.create_pings_keyboard(section_id=3))
            elif product_id == "3":
                requester = Requester(call.from_user.id)
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text="Выбери продукт по Жалобам и Пожеланиям :"
                                      , reply_markup=requester.create_pings_keyboard(section_id=4))
            elif product_id == "79976":
                requester = Requester(call.from_user.id)
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text="Выбери продукт по Установке :"
                                      , reply_markup=requester.create_pings_keyboard(section_id=5))
            elif product_id == "22494":
                requester = Requester(call.from_user.id)
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text="Выбери продукт по Сертификатам КЭП :"
                                      , reply_markup=requester.create_pings_keyboard(section_id=6))
            elif product_id == "600":
                requester = Requester(call.from_user.id)
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text="Выбери продукт по Редким вопросам :"
                                      , reply_markup=requester.create_pings_keyboard(section_id=7))
            else:
                ping = Ping()
                ping.add_to_queue(call.from_user.id, product_id, call.message.message_id, section_id)
                requester = Requester(ping.requester_id)
                requester.has_started_ping(True)
                kbrd = types.InlineKeyboardMarkup()
                kbrd.row(types.InlineKeyboardButton(text="Нет комментария", callback_data=f"no_comment;{ping.ping_id}"))
                kbrd.row(types.InlineKeyboardButton(text="Отменить пинг", callback_data=f"cancel;{ping.ping_id}"))
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text="Теперь отправь информацию по вопросу клиента. Напиши текстом в одном сообщении "
                                             "номер обращения и, при желании, свой вопрос.\n\nНапример \"23232323 не могу скопировать сертификат...\""
                                             "\n\n(!) Если в течение 4 минут ты не добавишь комментарий, то пинг автоматически закроется."
                                             "\n\nЕсли нечего передать, жми на кнопку \"Нет комментария\".\n\n"
                                      , reply_markup=kbrd)

                Helper.write_log(requester.user_id, -1, f"Создан пинг №{ping.ping_id}")
            return

    # 2. Если консультант решил не указывать комментарий к пингу

        if call.data.startswith("no_comment"):
            _, ping_id = call.data.split(";")

            ping = Ping()
            ping.fill_active_ping(ping_id)
            ping.add_comment("Нет комментария")

            kbrd = types.InlineKeyboardMarkup()
            kbrd.row(types.InlineKeyboardButton(text="Отменить", callback_data=f"cancel;{ping.ping_id}"))

            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text=f"Продукт {ping.product_name}.\nПингу присвоен номер #s{ping.ping_id}.\n"
                                         f"Пингов в очереди: {Helper.get_product_queue(ping.product_id) } шт.\n"
                                         f"Поместил пинг в очередь.\n\nНажми \"Отменить\", чтобы отменить пинг."
                                  , reply_markup=kbrd)

            ping.update_ping_state(message_id=call.message.message_id)
            requester = Requester(ping.requester_id)
            requester.has_started_ping(False)
            Helper.write_log(requester.user_id, -1, f"Добавлен комментарий \"Нет комментария\" к пингу №{ping.ping_id}")
            return

    # 3. Обработка пинга после нажатия на кнопку "Ответить"

        if call.data.startswith("answ"):
            _, ping_id = call.data.split(";")

            Helper.write_log(call.from_user.id, -1, f"Попытка ответить по кнопке \"Ответить\" у пинга №{ping_id}")

            ping = Ping()

            if not Ping.is_active(ping_id):
                ping.fill_archive_ping(ping_id)
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , parse_mode="markdown"
                                      , text=f"Пинг #s{ping.ping_id} был отменен [{ping.requester_fullname}](tg://user?id={ping.requester_id})")
                return

            ping.fill_active_ping(ping_id)
            if ping.responser_id != call.from_user.id:
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text=f"Пинг #s{ping.ping_id} был возвращен в очередь")
                return

            requester = Requester(ping.requester_id)
            if Spectator.is_spectator(ping.responser_id):
                responser = Spectator(ping.responser_id)
            else:
                responser = Responser(ping.responser_id)
            ping.update_ping_state(3, call.from_user.id)

            try:
                bot.delete_message(chat_id=ping.requester_id, message_id=ping.message_id)
            except Exception as e:
                print(f'\n\nНе удалось удалить сообщение о пинге у консультанта {ping.requester_fullname}\n{e}\n')

            bot.send_message(chat_id=ping.requester_id
                             , parse_mode="markdown"
                             , text=f"[{responser.fullname}](tg://user?id={responser.user_id}) начал(а) решать твой вопрос "
                                    f"#s{ping.ping_id} по {responser.products[ping.product_id]}.")

            # специальная обработка ответа для АРГОСа
            if ping.product_id == 6:
                kbrd = types.InlineKeyboardMarkup()
                kbrd.row(types.InlineKeyboardButton(text="Поставлен инцидент 🟢", callback_data=f"argosIncGreen;{ping_id}")
                        ,types.InlineKeyboardButton(text="Отчеты перенесены 🟢", callback_data=f"argosDoneGreen;{ping_id}"))
                kbrd.row(types.InlineKeyboardButton(text="Поставлен инцидент 🔴", callback_data=f"argosIncRed;{ping_id}")
                        ,types.InlineKeyboardButton(text="Отчеты перенесены 🔴", callback_data=f"argosDoneRed;{ping_id}"))
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , parse_mode="markdown"
                                      , text=f"Как закончишь работу над пингом #s{ping.ping_id}, нажми на нужную кнопку"
                                             f"\n\nПинговал(а) [{requester.fullname}](tg://user?id={requester.user_id})"
                                             f"\n\nКоментарий из пинга:\n{ping.comment}."
                                      , reply_markup=kbrd)
                return

            kbrd = types.InlineKeyboardMarkup()
            kbrd.row(types.InlineKeyboardButton(text="Закрыть пинг", callback_data=f"close;{ping_id}"))
            kbrd.row(types.InlineKeyboardButton(text="Закрыть и перейти в \"Зеленый\"", callback_data=f"closeToGreen;{ping_id}"))
            if Helper.is_helper(responser.user_id):
                kbrd.row(types.InlineKeyboardButton(text="Вопрос эксперту", callback_data=f"askParent;{ping_id};1"))

            try:
                ping.comment = ping.comment.lstrip()
                if len(ping.comment) > 8 and ping.comment[:8].isdigit() and not ping.comment[:9].isdigit():
                    url = make_tiny(f"qwic://incident/{ping.comment[:8]}")
                    comment = f"{ping.comment[:8]} [|перейти в QWIC|]({url})\n{ping.comment[8:]}"
                elif len(ping.comment) == 8 and ping.comment[:8].isdigit():
                    url = make_tiny(f"qwic://incident/{ping.comment[:8]}")
                    comment = f"{ping.comment[:8]} [|перейти в QWIC|]({url})\n{ping.comment[8:]}"
                else:
                    comment = ping.comment
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , parse_mode="markdown"
                                      , text=f"Ответ по пингу #s{ping.ping_id} отправлен. Нажми \"Закрыть пинг\", когда решишь вопрос ."
                                             f"\n\nПинговал(а) [{requester.fullname}](tg://user?id={requester.user_id})"
                                             f"\n\nКоментарий из пинга:\n{comment}."
                                      , reply_markup=kbrd)
            except Exception as e:
                bot.send_message(chat_id=1350082329
                                 , text=f'Произошла ошибка, когда {responser.fullname} '
                                        f'отвечал на пинг #s{ping.ping_id} от {requester.fullname}\n\n{e}')

            Helper.write_log(responser.user_id, -1, f"Ответ на пинг №{ping_id}")

            print(f"Ответ на пинг:\n{ping.to_str()}\n")
            return
# ---------------------------------------------
# НАЧАЛО СЕКЦИИ АРГОСа
# ---------------------------------------------
        if call.data.startswith("argosInc"):
            _, ping_id = call.data.split(";")

            Helper.write_log(call.from_user.id, -1, f"Попытка закрыть пинг №{ping_id} по АРГОСу (поставлен инцидент)")

            if not Ping.is_active(ping_id):
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text=f'Пинг #s{ping_id} был автоматически закрыт, когда ты перешел в Зеленый.')
                return

            ping = Ping()
            ping.fill_active_ping(ping_id)

            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , parse_mode="markdown"
                                  , text=f"Пинг #s{ping.ping_id} от [{ping.requester_fullname}](tg://user?id={ping.requester_id}) закрыт.\n\n"
                                         f"Решение: поставлен инцидент\n\n"
                                         f"Не забудь сменить статус на \"Зеленый\", если хочешь дальше отвечать на пинги.")

            ping.update_ping_state(9, call.from_user.id)
            ping.close()
            if Spectator.is_spectator(ping.responser_id):
                responser = Spectator(ping.responser_id)
            else:
                responser = Responser(ping.responser_id)
            responser.update_answer_last_date()

            bot.send_message(chat_id=ping.requester_id
                             , parse_mode="markdown"
                             , text=f"Пинг #s{ping.ping_id} закрыт [{responser.fullname}](tg://user?id={responser.user_id})"
                                    f"\nРешение: поставлен инцидент.")

            Helper.write_log(call.from_user.id, -1, f"Закрыт пинг №{ping_id} по АРГОСу (поставлен инцидент)")

            if call.data.startswith("argosIncGreen"):
                responser.switch_state()
                print(f"Закрытие пинга с выходом в Зеленый :\n{ping.to_str()}\n")
                return

            print(f"Закрытие пинга с выходом в Красный :\n{ping.to_str()}\n")
            return

        if call.data.startswith("argosDone"):
            _, ping_id = call.data.split(";")

            Helper.write_log(call.from_user.id, -1, f"Попытка закрыть пинг №{ping_id} по АРГОСу (отчеты перенесены)")

            if not Ping.is_active(ping_id):
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text=f'Пинг #s{ping_id} был автоматически закрыт, когда ты перешел в Зеленый.')
                return

            ping = Ping()
            ping.fill_active_ping(ping_id)

            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , parse_mode="markdown"
                                  , text=f"Пинг #s{ping.ping_id} от [{ping.requester_fullname}](tg://user?id={ping.requester_id}) закрыт.\n\n"
                                         f"Решенеие: отчеты перенесены\n\n"
                                         f"Не забудь сменить статус на \"Зеленый\", если хочешь дальше отвечать на пинги.")

            ping.update_ping_state(8, call.from_user.id)
            ping.close()
            if Spectator.is_spectator(ping.responser_id):
                responser = Spectator(ping.responser_id)
            else:
                responser = Responser(ping.responser_id)
            responser.update_answer_last_date()

            bot.send_message(chat_id=ping.requester_id
                             , parse_mode="markdown"
                             , text=f"Пинг #s{ping.ping_id} закрыт [{responser.fullname}](tg://user?id={responser.user_id})"
                                    f"\nРешение: отчеты перенесены.")

            Helper.write_log(call.from_user.id, -1, f"Закрыт пинг №{ping_id} по АРГОСу (отчеты перенесены)")

            if call.data.startswith("argosDoneGreen"):
                responser.switch_state()
                print(f"Закрытие пинга с выходом в Зеленый :\n{ping.to_str()}\n")
                return

            print(f"Закрытие пинга с выходом в Красный :\n{ping.to_str()}\n")
            return
# ---------------------------------------------
# КОНЕЦ СЕКЦИИ АРГОСа
# ---------------------------------------------
    # 4. Обработка для проброса пинга от помогатора/наставника к эксперту/супервизору
        # Создание дополнительного сообщения с вопросом точно нужно отправить пинг от помогатора
        if call.data.startswith("askParent"):
            _, ping_id, from_flag = call.data.split(";")
            ping = Ping()
            try:
                ping.fill_active_ping(ping_id)
            except Exception as e:
                bot.send_message(chat_id=1350082329
                                 , text=f'Произошла ошибка, когда пытались пробросить пинг #s{ping.ping_id} '
                                        f'к супервизорам\n\n{call.data}\n{e}')
                return
            kbrd = types.InlineKeyboardMarkup()
            kbrd.row(types.InlineKeyboardButton(text="Отправить", callback_data=f"send_helper_ping;{ping_id};{from_flag}")
                     , types.InlineKeyboardButton(text="Отменить", callback_data="close_menu"))
            bot.send_message(chat_id=call.from_user.id
                             , text="Нажми \"Отправить\", чтобы отправить пинг экспертам/супервизорам"
                             , reply_markup=kbrd)
            return

        # отправка пинга от помогатора
        if call.data.startswith("send_helper_ping"):
            _, ping_id, from_flag = call.data.split(";")
            ping = Ping()
            try:
                ping.fill_active_ping(ping_id)
            except Exception as e:
                responser = Responser(ping.responser_id)
                bot.send_message(chat_id=1350082329
                                 , text=f'Произошла ошибка, когда {responser.fullname} из {responser.department} '
                                        f'пытался(ась) пробросить пинг #s{ping.ping_id} к экспертам\n\n{e}')
            ping.add_to_queue(call.from_user.id, ping.product_id, call.message.message_id, ping.section_id, from_flag)
            ping.add_comment(ping.comment)
            new_ping = Ping()
            new_ping.fill_active_ping(Helper.get_last_active_ping_by_user_id(call.from_user.id))
            kbrd = types.InlineKeyboardMarkup()
            kbrd.row(types.InlineKeyboardButton(text="Отменить", callback_data=f"cancel;{new_ping.ping_id}"))
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text=f"Отправил запрос о помощи по пингу #s{ping.ping_id} к экспертам и супервизорам"
                                  , reply_markup=kbrd)

            Helper.write_log(call.from_user.id, -1, f"Проброшен пинг №{ping.ping_id} {Helper.get_from_flag_name(from_flag)} "
                                                    f"к экспертам (новый пинг №{new_ping.ping_id})")

            return

        if call.data.startswith("transmit"):
            _, ping_id = call.data.split(";")

            Helper.write_log(call.from_user.id, -1, f"Попытка вернуть пинг №{ping_id} в очередь.")

            ping = Ping()
            if not Ping.is_active(ping_id):
                ping.fill_archive_ping(ping_id)
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , parse_mode="markdown"
                                      , text=f"Пинг #s{ping_id} был отменен [{ping.requester_fullname}](tg://user?id={ping.requester_id})")
                return

            ping.fill_active_ping(ping_id)
            if ping.responser_id != call.from_user.id:
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text=f"Пинг #s{ping_id} был возвращен в очередь. Возможно он снова придет тебе.")
                return

            ping.update_ping_state(6)
            ping.return_to_queue()
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text=f"Пинг #s{ping.ping_id} возвращен в очередь.\n\nНе забудь сменить статус на \"Зеленый\", "
                                         f"если хочешь дальше отвечать на пинги.")

            Helper.write_log(call.from_user.id, -1, f"Возврат пинга №{ping_id} в очередь.")

            print(f"Возврат пинга в очередь :\n{ping.to_str()}\n")

    # 5. Обработка "красивого" закрытия контекстного меню

        if call.data == "close_menu":
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Меню закрыто")
            return

    # 6. Обработка кнопок "Закрыть пинг" и "Закрыть и перейти в Зеленый"

        if call.data.startswith("close"):
            _, ping_id = call.data.split(";")

            Helper.write_log(call.from_user.id, -1, f"Попытка закрыть пинг №{ping_id}.")

            if not Ping.is_active(ping_id):
                try:
                    ping = Ping()
                    ping.fill_archive_ping(ping_id)

                    if len(ping.comment) > 8 and ping.comment[:8].isdigit() and not ping.comment[:9].isdigit():
                        url = make_tiny(f"qwic://incident/{ping.comment[:8]}")
                        comment = f"{ping.comment[:8]} [|перейти в QWIC|]({url})\n{ping.comment[8:]}"
                    elif len(ping.comment) == 8 and ping.comment[:8].isdigit():
                        url = make_tiny(f"qwic://incident/{ping.comment[:8]}")
                        comment = f"{ping.comment[:8]} [|перейти в QWIC|]({url})\n{ping.comment[8:]}"
                    else:
                        comment = ping.comment

                    bot.edit_message_text(chat_id=call.from_user.id
                                          , parse_mode='markdown'
                                          , message_id=call.message.message_id
                                          , text=f"Пинг #s{ping.ping_id} ({ping.section_name} по {ping.product_name}) от "
                                                 f"[{ping.requester_fullname}](tg://user?id={ping.requester_id}) был "
                                                 f"автоматически закрыт, когда ты перешел в Зеленый.\n\nКомментарий:\n{comment}")
                except Exception as e:
                    bot.edit_message_text(chat_id=call.from_user.id
                                          , message_id=call.message.message_id
                                          , text=f"Пинг #s{ping_id} автоматически закрыт, когда ты перешел в Зеленый.")
                    print(e)
                return

            ping = Ping()
            ping.fill_active_ping(ping_id)
            ping.comment = ping.comment.lstrip()
            if len(ping.comment) > 8 and ping.comment[:8].isdigit() and not ping.comment[:9].isdigit():
                url = make_tiny(f"qwic://incident/{ping.comment[:8]}")
                comment = f"{ping.comment[:8]} [|перейти в QWIC|]({url})\n{ping.comment[8:]}"
            elif len(ping.comment) == 8 and ping.comment[:8].isdigit():
                url = make_tiny(f"qwic://incident/{ping.comment[:8]}")
                comment = f"{ping.comment[:8]} [|перейти в QWIC|]({url})\n{ping.comment[8:]}"
            else:
                comment = ping.comment
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , parse_mode="markdown"
                                  , text=f"Пинг #s{ping.ping_id} ({ping.section_name} по {ping.product_name}) от "
                                         f"[{ping.requester_fullname}](tg://user?id={ping.requester_id}) закрыт.\n\n"
                                         f"Комментарий:\n{comment}"
                                         f"\n\nНе забудь сменить статус на \"Зеленый\", "
                                         f"если хочешь дальше отвечать на пинги.")

            ping.update_ping_state(4, call.from_user.id)
            ping.close()
            if Spectator.is_spectator(ping.responser_id):
                responser = Spectator(ping.responser_id)
            else:
                responser = Responser(ping.responser_id)
            responser.update_answer_last_date()

            if call.data.startswith("closeToGreen"):
                responser.switch_state()
                bot.send_message(chat_id=ping.responser_id
                               , text="Сменил статус на \"Зеленый\""
                               , reply_markup=responser.create_keyboard(change_responser_state=0))

                Helper.write_log(call.from_user.id, -1, f"Закрытие пинга №{ping_id} с выходом в \"Зеленый\".")

                print(f"Закрытие пинга с выходом в Зеленый :\n{ping.to_str()}\n")
                return

            Helper.write_log(call.from_user.id, -1, f"Закрытие пинга №{ping_id} с выходом в \"Красный\".")

            print(f"Закрытие пинга с выходом в Красный :\n{ping.to_str()}\n")
            return

    # 7. Обработка кнопки "Отмена" у пинга

        if call.data.startswith("cancel"):
            _, ping_id = call.data.split(";")
            ping = Ping()

            Helper.write_log(call.from_user.id, -1, f"Попытка отменить пинг №{ping_id}")

            try:
                ping.fill_active_ping(ping_id)
            except Exception as e:
                print(f"----ERROR IN CALLBACK CANCEL----\n{e}")
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text=f"Пинг #s{ping_id} удален")
                requester = Requester(call.from_user.id)
                requester.has_started_ping(False)
                Helper.write_log(call.from_user.id, -1, f"Отмена пинга №{ping_id} с ошибкой")
                return

            ping.update_ping_state(5)
            ping.close()
            requester = Requester(ping.requester_id)
            requester.has_started_ping(False)

            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text=f"Пинг #s{ping_id} отменен")

            Helper.write_log(call.from_user.id, -1, f"Отмена пинга №{ping_id}")

            print(f"Отмена пинга :\n{ping.to_str()}\n")
            return

# ---------------------------------------------
# КОНЕЦ СЕКЦИИ ОБРАБОТКИ ПИНГОВ
# ---------------------------------------------
# НАЧАЛО СЕКЦИИ С КОМАНДАМИ ИЗ "АДМИНИСТРИРОВАНИЯ"
# ---------------------------------------------
    # НАЧАЛО СЕКЦИИ ДЛЯ РАБОТЫ С ПРОДУКТАМИ
# ---------------------------------------------
        if call.data == "products":
            kbrd = types.InlineKeyboardMarkup()
            kbrd.row(types.InlineKeyboardButton(text="Добавить продукт себе", callback_data=f"add_prod"))
            kbrd.row(types.InlineKeyboardButton(text="Удалить продукт у себя", callback_data=f"rem_prod"))
            kbrd.row(types.InlineKeyboardButton(text="Изменить приоритет продукта у себя", callback_data=f"change_prior_1;{call.from_user.id}"))
            kbrd.row(types.InlineKeyboardButton(text="Добавить продукт помогатору", callback_data=f"add_prod_to_helper"))
            kbrd.row(types.InlineKeyboardButton(text="Удалить продукт у помогатора", callback_data=f"remove_prod_from_helper"))
            kbrd.row(types.InlineKeyboardButton(text="Изменить приоритет продукта у сотрудника", callback_data=f"chng_prod_prior_other"))
            kbrd.row(types.InlineKeyboardButton(text="Закрыть", callback_data=f"close_menu"))
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Что нужно сделать:"
                                  , reply_markup=kbrd)
            return

        if call.data == "add_prod_to_user":
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Кому нужно добавить продукт для пинга?"
                                  , reply_markup=responser.get_staff_by_action("add_product"))
            return

        if call.data == "add_prod_to_helper":
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Кому нужно добавить продукт для ответа?"
                                  , reply_markup=responser.get_staff_by_action("helper_add_product"))
            return

        if call.data == "remove_prod_from_user":
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="У кого нужно удалить продукт для пинга?"
                                  , reply_markup=responser.get_staff_by_action("remove_product"))
            return

        if call.data == "remove_prod_from_helper":
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="У кого нужно удалить продукт для ответа?"
                                  , reply_markup=responser.get_staff_by_action("helper_remove_product"))
            return

        if call.data.startswith("user_to_"):
            action, user_id = call.data.split(";")

            if action == "user_to_add_prod":
                text = "Какой продукт нужно добавить?"
                kbrd = Requester.get_products_by_action(user_id, "add_product")
            elif action == "user_to_rem_prod":
                text = "Какой продукт нужно удалить?"
                kbrd = Requester.get_products_by_action(user_id, "remove_product")

            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text=text
                                  , reply_markup=kbrd)
            return

        if call.data.startswith("hlpr_to_"):
            action, user_id = call.data.split(";")
            responser = Responser(user_id)

            if action == "hlpr_to_add_prod":
                text = "Какой продукт нужно добавить?"
                kbrd = responser.get_products_by_action("add_product", user_id)
            elif action == "hlpr_to_rem_prod":
                text = "Какой продукт нужно удалить?"
                kbrd = responser.get_products_by_action("remove_product", user_id)

            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text=text
                                  , reply_markup=kbrd)
            return

        if call.data == "add_prod":
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Какой продукт нужно добавить?"
                                  , reply_markup=responser.get_products_by_action("add_product", responser.user_id))
            return

        if call.data.startswith("add_prod"):
            _, user_id, product_id, direction = call.data.split(";")
            is_responser = False
            if Responser.is_responser(user_id):
                responser = Responser(user_id)
                is_responser = True

            Helper.add_product_to_user(user_id, product_id, direction)
            Helper.update_product_moving_log(who=call.from_user.id, whom=user_id, product_id=product_id
                                             , action="add", direction=direction)

            Helper.write_log(call.from_user.id, user_id, f"Добавление продукта {product_id}, direction=\"{direction}\"")


            if is_responser:
                kbrd = responser.get_products_by_action("add_product", responser.user_id)
            else:
                kbrd = Requester.get_products_by_action(user_id, "add_product")
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Какой продукт ещё добавить?"
                                  , reply_markup=kbrd)
            return

        if call.data == "rem_prod":
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Какой продукт нужно удалить?"
                                  , reply_markup=responser.get_products_by_action("remove_product", responser.user_id))
            return

        if call.data.startswith("rem_prod"):
            _, user_id, product_id, direction = call.data.split(";")
            is_responser = False
            if Responser.is_responser(user_id):
                responser = Responser(user_id)
                is_responser = True

            Helper.remove_product_from_user(user_id, product_id, direction)
            Helper.update_product_moving_log(who=call.from_user.id, whom=user_id, product_id=product_id
                                             , action="remove", direction=direction)

            Helper.write_log(call.from_user.id, user_id, f"Удаление продукта {product_id}, direction=\"{direction}\"")

            if is_responser:
                kbrd = responser.get_products_by_action("remove_product", responser.user_id)
            else:
                kbrd = Requester.get_products_by_action(user_id, "remove_product")
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Какой продукт ещё удалить?"
                                  , reply_markup=kbrd)
            return
# ---------------------------------------------
    # НАЧАЛО СЕКЦИИ С ПРИОРИТЕТАМИ ДЛЯ ПРОДУКТОВ У ОТВЕЧАЮЩИХ
# ---------------------------------------------

        if call.data.startswith("chng_prod_prior_other"):
            """поменять приоритет у продукта"""
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="У кого поменять приоритет?"
                                  , reply_markup=responser.get_staff_by_action("chng_prod_prior"))
            return

        if call.data.startswith("change_prior_1"):
            _, user_id = call.data.split(";")
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="У какого продукта нужно поменять приоритеты:"
                                  , reply_markup=responser.get_products_by_action("chng_prod_prior", user_id))
            return

        if call.data.startswith("ch_pr_pr"):
            _, user_id, product_id, _ = call.data.split(";")
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text=f"Сейчас приоритет = {Helper.get_product_priority(user_id, product_id)}"
                                         f"\nКакой приоритет установить?"
                                  , reply_markup=Helper.create_priority_keyboard(user_id, product_id))
            return

        if call.data.startswith("set_new_pr"):
            _, new_priority, user_id, product_id = call.data.split(";")
            Helper.set_product_priority(new_priority, user_id, product_id)
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text=f"Приоритет изменен. У какого продукта еще поменять приоритет?"
                                  , reply_markup=responser.get_products_by_action("chng_prod_prior", user_id))
            Helper.update_product_moving_log(who=call.from_user.id, whom=user_id, product_id=product_id
                                             , action="change_priority", direction=f"set {new_priority}")
            return
# ---------------------------------------------
    # КОНЕЦ СЕКЦИИ С ПРИОРИТЕТАМИ ПРОДУКТОВ У ОТВЕЧАЮЩИХ
# ---------------------------------------------
    # КОНЕЦ СЕКЦИИ ДЛЯ РАБОТЫ С ПРОДУКТАМИ
# ---------------------------------------------
    # НАЧАЛО СЕКЦИИ ДЛЯ РАБОТЫ С НАЙДЕНЫМИ СОТРУДНИКАМИ
# ---------------------------------------------
        if call.data.startswith("find_user"):
            _, user_id = call.data.split(";")
            kbrd = types.InlineKeyboardMarkup()
            kbrd.row(types.InlineKeyboardButton(text=f"Перевести в другой отдел", callback_data=f"ch_dept;{user_id}"))
            kbrd.row(types.InlineKeyboardButton(text=f"Изменить должность", callback_data=f"ch_role;{user_id}"))
            kbrd.row(types.InlineKeyboardButton(text=f"Спасти", callback_data=f"rescue;{user_id}"))
            kbrd.row(types.InlineKeyboardButton(text=f"Закрыть", callback_data=f"close_menu"))
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Что нужно сделать?"
                                  , reply_markup=kbrd)
            return

        if call.data.startswith("ch_dept"):
            _, user_id = call.data.split(";")
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="В какой отдел нужно перевести?"
                                  , reply_markup=Helper.get_departments_ids(user_id))
            return

        if call.data.startswith("set_dept"):
            _, user_id, department_id = call.data.split(";")
            try:
                Helper.set_new_department_to_user(user_id, department_id)
            except:
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text="Данный пользователь не зарегистрирован в боте")
                return
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Отдел изменен")
            return

        if call.data.startswith("ch_role"):
            _, user_id = call.data.split(";")
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Какую роль нужно указать?"
                                  , reply_markup=Helper.get_all_professions(user_id))
            return

        if call.data.startswith("set_role"):
            _, user_id, role_id = call.data.split(";")
            Helper.set_new_role_to_user(user_id, int(role_id), bot)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Роль изменена")
            return

        if call.data == "rescuers":
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Кого нужно спасти:"
                                  , reply_markup=responser.get_staff_by_action("rescue"))
            return

        if call.data.startswith("rescue"):
            _, user_id = call.data.split(";")
            Helper.rescue_user(user_id)
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text=f"Пользователь спасен(а).\n\nКого нужно спасти еще:"
                                  , reply_markup=responser.get_staff_by_action("rescue"))

            Helper.write_log(call.from_user.id, user_id, f"Спасение пользователя")
            return

# ---------------------------------------------
    # КОНЕЦ СЕКЦИИ ДЛЯ РАБОТЫ С НАЙДЕНЫМИ СОТРУДНИКАМИ
# ---------------------------------------------
    # НАЧАЛО СЕКЦИИ ДЛЯ РАБОТЫ С ПОМОГАТОРАМИ
# ---------------------------------------------
        if call.data == "helpers":
            kbrd = types.InlineKeyboardMarkup()
            kbrd.row(types.InlineKeyboardButton(text="Призвать помогатора", callback_data=f"call_helper"))
            kbrd.row(types.InlineKeyboardButton(text="Отозвать помогатора", callback_data=f"recall_helper"))
            kbrd.row(types.InlineKeyboardButton(text="Закрыть", callback_data=f"close_menu"))
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Что нужно сделать:"
                                  , reply_markup=kbrd)
            return

        if call.data == "call_helper":
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Кого нужно призвать помогатором:"
                                  , reply_markup=responser.get_staff_by_action("call_helper"))
            return

        if call.data.startswith("call_helper"):
            _, user_id = call.data.split(";")

            Helper.write_log(call.from_user.id, user_id, f"Попытка призвать помогатора")

            if user_id == 0:
                responser = Responser(call.from_user.id)
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text=f"{call.message.text} не зарегистрирован(а) в боте. "
                                             f"Если нужно призвать другого помогатора, то выбери из списка:"
                                      , reply_markup=responser.get_staff_by_action("call_helper"))

                Helper.write_log(call.from_user.id, user_id, f"Помогатор не зарегистрирован")

                return
            else:
                Helper.switch_helper_role(user_id, 1, 7)
                Helper.add_products_to_helper(user_id)
                responser = Responser(user_id)
                try:
                    bot.send_message(chat_id=user_id
                                     , text="Сейчас ты можешь только отвечать на пинги."
                                     , reply_markup=responser.create_keyboard(change_responser_state=0))
                except:
                    bot.edit_message_text(chat_id=call.from_user.id
                                          , message_id=call.message.message_id
                                          , text=f"Не удалось призвать {responser.fullname} . Пиши в ФакАпы ")
                    return
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text="Кого еще нужно призвать помогатором:"
                                      , reply_markup=responser.get_staff_by_action("call_helper"))

                Helper.write_log(call.from_user.id, user_id, f"Помогатор призван(а)")

                return

        if call.data == "recall_helper":
            responser = Responser(call.from_user.id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Какого помогатора нужно отозвать:"
                                  , reply_markup=responser.get_staff_by_action("recall_helper"))
            return

        if call.data.startswith("recall_helper"):
            _, user_id = call.data.split(";")

            Helper.write_log(call.from_user.id, user_id, f"Попытка отозвать помогатора")

            Helper.switch_helper_role(user_id, 0, 5)
            Helper.remove_products_to_helper(user_id)
            responser = Responser(call.from_user.id)
            requester = Requester(user_id)
            try:
                bot.send_message(chat_id=user_id
                                 , text="Сейчас ты можешь только пинговать."
                                 , reply_markup=requester.create_keyboard())
            except:
                bot.edit_message_text(chat_id=call.from_user.id
                                      , message_id=call.message.message_id
                                      , text=f"Не удалось отозвать {responser.fullname}. Пиши в ФакАпы")
                return
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Кого еще нужно отозвать помогатором:"
                                  , reply_markup=responser.get_staff_by_action("recall_helper"))

            Helper.write_log(call.from_user.id, user_id, f"Помогатор отозван(а)")

            return
# ---------------------------------------------
    # КОНЕЦ СЕКЦИИ ДЛЯ РАБОТЫ С ПОМОГАТОРАМИ
# ---------------------------------------------
    # НАЧАЛО СЕКЦИИ ДЛЯ РАБОТЫ СО СТАЖЕРАМИ И НАСТАВНИКАМИ
# ---------------------------------------------

# ---------------------------------------------
    # КОНЕЦ СЕКЦИИ ДЛЯ РАБОТЫ СО СТАЖЕРАМИ И НАСТАВНИКАМИ
# ---------------------------------------------
        if call.data == "change_department":
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="В какой отдел ты хочешь перейти?"
                                  , reply_markup=Helper.create_departments_keyboard())
            return

        if call.data.startswith("new_dep"):
            _, department_id = call.data.split(";")
            Helper.set_new_department_to_user(call.from_user.id, department_id)
            bot.edit_message_text(chat_id=call.from_user.id
                                  , message_id=call.message.message_id
                                  , text="Ты переведен(а) в выбранный отдел")

            Helper.write_log(call.from_user.id, -1, f"Смена отдела на отдел №{department_id}")

            return
# ---------------------------------------------
# КОНЕЦ СЕКЦИИ С "АДМИНИСТРИРОВАНИЕМ"
# ---------------------------------------------

    bot.polling(none_stop=True)
    # telebot.apihelper.proxy = {'https': 'https://8.12.22.252:8080'}


if __name__ == "__main__":
    while True:
        try:
            bot = telebot.TeleBot(TOKEN)
            sender_thread = threading.Thread(name="SenderThread", target=Helper.send_ping, args=(bot,)).start()
            checker_thread = threading.Thread(name="CheckerThread", target=Helper.check_no_answer, args=(bot,)).start()
            notififcation_thread = threading.Thread(name="NotificationThread", target=Helper.send_notification, args=(bot,)).start()
            auto_close_thread = threading.Thread(name="NotificationThread", target=Helper.auto_close_pings, args=(bot,)).start()

            main(bot)
        except Exception as e:
            print(f"Svetofor сбоит.\n\n{e}\n\nИдет перезапуск бота.")
            del bot
