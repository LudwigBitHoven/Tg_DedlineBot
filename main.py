import telebot
import gspread
import json
import validators
import pandas as pd
from datetime import datetime, timedelta

bot = telebot.TeleBot('5256096678:AAEhgJPBAaGVk07IUjd4YBfocxt9Qul6wKg')


def convert_date(date: str = "01/01/2000"):
    """ Конвертируем дату из строки в datetime """
    dt = datetime.strptime(date, "%d/%m/%y") + timedelta(days=1)
    today = datetime.today()
    delta = dt - today
    if dt >= today and delta.days <= 7:
        return True
    else:
        return False


def connect_table(message):
    """ Подключаемся к Google-таблице """
    url = message.text
    idsheet = url.split('/')[-2]  # Нужно извлечь id страницы из ссылки на Google-таблицу
    try:
        with open("tables.json") as json_file:
            tables = json.load(json_file)
        title = len(tables) + 1
        tables[title] = {"url": url, "id": idsheet}
    except FileNotFoundError:
        tables = {0: {"url": url, "id": idsheet}}
    with open('tables.json', 'w') as json_file:
        json.dump(tables, json_file)
    bot.send_message(message.chat.id, "Произошло соединение 😎")


def extract_grades():
    pass


def save():
    pass


def access_current_sheet():
    """ Обращаемся к Google-таблице """
    with open("tables.json") as json_file:
        tables = json.load(json_file)

    idsheet = tables[max(tables)]["id"]
    gc = gspread.service_account(filename="credentials.json")
    sh = gc.open_by_key(idsheet)
    worksheet = sh.sheet1
    # Преобразуем Google-таблицу в таблицу pandas
    # df = pd.DataFrame(worksheet.get_all_records())
    return worksheet


def choose_action(message):
    """ Обрабатываем действия верхнего уровня """
    while True:
        if message.text == "Подключить Google-таблицу":
            msg = bot.reply_to(message, "А можно ссылочку 👉🏻👈🏻")
            bot.register_next_step_handler(msg, connect_table)
            break
        elif message.text == "Редактор предметов":
            subject_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            subject_markup.row("Добавить предмет")
            subject_markup.row("Изменить предмет")
            subject_markup.row("Удалить предмет")
            subject_markup.row("Удалить всё")
            info = bot.send_message(message.chat.id, "Что будем делать с предметами?", reply_markup=subject_markup)
            bot.register_next_step_handler(info, choose_subject_action)
            break
        elif message.text == "Редактор дедлайнов":
            worksheet = access_current_sheet()
            values_list = worksheet.col_values(1)[1:]
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for i in values_list:
                markup.row(str(i))
            info = bot.send_message(message.chat.id, "Выбери редактируемый предмет", reply_markup=markup)
            bot.register_next_step_handler(info, requesting_lab_number)
            break
        elif message.text == "Вывести дедлайн на неделю":
            worksheet = access_current_sheet()
            values_list = worksheet.col_values(1)[1:]
            text = ''
            for title in values_list:
                row_id = worksheet.find(title).row
                line = worksheet.row_values(row_id)[2:]
                line = list(filter(None, line))
                close_deadlines = []
                for date in line:
                    if convert_date(date):
                        close_deadlines.append(date)
                if len(close_deadlines) > 0:
                    text += title + " " + ", ".join(close_deadlines) + '\n'
            if text == '':
                info = bot.send_message(message.chat.id, "Дедлайнов нет\nОтдыхай")
            else:
                bot.send_message(message.chat.id, text)
                info = bot.send_message(message.chat.id, "Показаны все дедлайны на ближайшие 7 дней")
            bot.register_next_step_handler(info, choose_action)
            break
        elif message.text == "Редактор расписания":
            subject_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            subject_markup.row("Составить новое расписание")
            subject_markup.row("Изменить расписание")
            subject_markup.row("Вывести расписание")
            info = bot.send_message(message.chat.id, "Что будем делать с расписанием?", reply_markup=subject_markup)
            bot.register_next_step_handler(info, choose_timetable_action)
            break

        info = bot.send_message(message.chat.id, "Ты по-моему перепутал")
        bot.send_photo(message.chat.id, "https://i.ytimg.com/vi/EI3lfljIZxE/maxresdefault.jpg")
        bot.register_next_step_handler(info, choose_action)
        break


def choose_timetable_action(message):
    while True:
        if message.text == "Составить новое расписание":
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.row("Составить")
            choice = bot.send_message(message.chat.id, "Ты уверен в своих действиях?", reply_markup=markup)
            bot.register_next_step_handler(choice, create_timetable)
            break
        if message.text == "Изменить расписание":
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.row("Составить")
            choice = bot.send_message(message.chat.id, "Какой день менять?", reply_markup=markup)
            bot.register_next_step_handler(choice, change_timetable)
            break
        if message.text == "Вывести расписание":
            break
        info = bot.send_message(message.chat.id, "Ты по-моему перепутал")
        bot.send_photo(message.chat.id, "https://i.ytimg.com/vi/EI3lfljIZxE/maxresdefault.jpg")
        bot.register_next_step_handler(info, choose_timetable_action)
        break


def create_timetable(message):
    worksheet = access_current_sheet()
    for i in range(1, 8):
        worksheet.batch_clear([f"H{i}:O{i}"])
    lst = ["понедельник", "вторник", "среда", "четверг", "пятница"]
    for i in range(len(lst)):
        for j in range(1, 9):
            global coords
            coords = i, j
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.row("Ввести предмет")
            markup.row("Окно")
            markup.row("Пар больше нет")
            choice = bot.reply_to(message, f"{j} пара, {lst[i]}, у нас?", reply_markup=markup)
            bot.register_next_step_handler(choice, timetable_action)
            if coords == "конец":
                break
            if coords == "окно":
                continue
        if coords == "конец":
            continue
            # worksheet.update_cell(i, j - 1, message.text)


def timetable_action(message):
    worksheet = access_current_sheet()
    while True:
        global coords
        if message.text == "Ввести предмет":
            msg = bot.reply_to(message, "Ну так вводи его")
            worksheet.update_cell(coords[0], coords[1], msg.text)
            break
        if message.text == "Окно":
            coords = "окно"
            break
        if message.text == "Сегодня пар больше нет":
            coords = "конец"
            break


def choose_subject_action(message):
    """ Выбираем действие в разделе Редактор предметов """
    while True:
        if message.text == "Добавить предмет":
            msg = bot.reply_to(message, "Введи имя предмета")
            bot.register_next_step_handler(msg, add_new_subject)
            break
        elif message.text == "Изменить предмет":
            worksheet = access_current_sheet()
            values_list = worksheet.col_values(1)[1:]
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for i in values_list:
                markup.row(str(i))
            updating = bot.send_message(message.chat.id, "Выбери предмет", reply_markup=markup)
            bot.register_next_step_handler(updating, update_subject)
            break
        elif message.text == "Удалить предмет":
            worksheet = access_current_sheet()
            values_list = worksheet.col_values(1)[1:]
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for i in values_list:
                markup.row(str(i))
            deleting = bot.send_message(message.chat.id, "Выбери предмет", reply_markup=markup)
            bot.register_next_step_handler(deleting, delete_subject)
            break
        elif message.text == "Удалить всё":
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.row("Удалить")
            choice = bot.send_message(message.chat.id, "Ты уверен в своих действиях?", reply_markup=markup)
            bot.register_next_step_handler(choice, clear_subject_list)
            break

        info = bot.send_message(message.chat.id, "Ты по-моему перепутал")
        bot.send_photo(message.chat.id, "https://i.ytimg.com/vi/EI3lfljIZxE/maxresdefault.jpg")
        bot.register_next_step_handler(info, choose_subject_action)
        break


def requesting_lab_number(message):
    """ Обновляем дедлайн """
    while True:
        try:
            worksheet = access_current_sheet()
            global cell
            cell = worksheet.find(message.text)
            coords = cell.row, cell.col
            msg = bot.reply_to(message, 'Укажи номер работы от 1 до 5')
            bot.register_next_step_handler(msg, requesting_deadline_date)
            break
        except:
            pass

        info = bot.send_message(message.chat.id, "Выбери предмет из списка")
        bot.register_next_step_handler(info, requesting_lab_number)
        break


def requesting_deadline_date(message):
    """ Обновляем дедлайн """
    while True:
        try:
            if 1 <= int(message.text) <= 5:
                global coords
                coords = cell.row, int(message.text) + 2
                msg = bot.reply_to(message, 'Предоставь дату в формате 01/01/01')
                bot.register_next_step_handler(msg, setting_deadline)
                break
            else:
                pass
        except ValueError:
            pass

        info = bot.send_message(message.chat.id, "Ты по-моему перепутал")
        bot.send_photo(message.chat.id, "https://i.ytimg.com/vi/EI3lfljIZxE/maxresdefault.jpg")
        bot.register_next_step_handler(info, requesting_deadline_date)
        break

def setting_deadline(message):
    """ Обновляем дедлайн """
    worksheet = access_current_sheet()
    row, col = coords
    while True:
        try:
            datetime.strptime(message.text, '%d/%m/%y')
            dt = datetime.strptime(message.text, "%d/%m/%y")
            if dt + timedelta(days = 1) < datetime.today():
                info = bot.send_message(message.chat.id, "А зачем прошедшие даты-то указывать?"
                                                         "\nУкажи дату в формате 01/01/01")
                bot.register_next_step_handler(info, setting_deadline)
                break
            else:
                worksheet.update_cell(row, col, message.text)
                worksheet.update_cell(row, col, message.text)
                bot.send_message(message.chat.id, "Дедлайн добавлен 😎")
                start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                start_markup.row("Вывести дедлайн на неделю")
                start_markup.row("Редактор дедлайнов")
                start_markup.row("Редактор предметов")
                info = bot.send_message(message.chat.id, "Что делать будем?", reply_markup=start_markup)
                bot.register_next_step_handler(info, choose_action)
                break
        except ValueError:
            pass
        info = bot.send_message(message.chat.id, "Ты по-моему перепутал"
                                                 "\nУкажи дату в формате 01/01/00")
        bot.send_photo(message.chat.id, "https://i.ytimg.com/vi/EI3lfljIZxE/maxresdefault.jpg")
        bot.register_next_step_handler(info, setting_deadline)
        break


def add_new_subject(message):
    """ Вносим новое название предмета в Google-таблицу """
    global title
    title = ''
    title = message.text
    msg = bot.reply_to(message, 'Укажи ссылку на предмет')
    bot.register_next_step_handler(msg, add_new_subject_url)


def add_new_subject_url(message):
    """ Вносим новую ссылку на таблицу предмета в Google-таблицу """
    while True:
        url = message.text
        if validators.url(url):
            worksheet = access_current_sheet()
            worksheet.append_row([title, url])
            bot.send_message(message.chat.id, "Добавлены предмет и указанная ссылка 😎")
            start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            start_markup.row("Вывести дедлайн на неделю")
            start_markup.row("Редактор дедлайнов")
            start_markup.row("Редактор предметов")
            info = bot.send_message(message.chat.id, "Что будем делать?", reply_markup=start_markup)
            bot.register_next_step_handler(info, choose_action)
            break
        else:
            pass

        info = bot.send_message(message.chat.id, "Ссылка кривая, укажи нормальную ссылку")
        bot.register_next_step_handler(info, add_new_subject_url)
        break


def update_subject(message):
    """ Обновляем информацию о предмете в Google-таблице """
    while True:
        try:
            worksheet = access_current_sheet()
            global cell, coords
            cell = worksheet.find(message.text)
            coords = cell.row, cell.col
            msg = bot.reply_to(message, 'Укажи новое название предмета и ссылку дай')
            bot.register_next_step_handler(msg, subject_new_name)
            break
        except:
            pass

        info = bot.send_message(message.chat.id, "Выбери предмет из списка")
        bot.register_next_step_handler(info, update_subject)
        break


def subject_new_name(message):
    """ Вносим новое название предмета в Google-таблицу """
    while True:
        try:
            title, url = message.text.split()
            if validators.url(url):
                worksheet = access_current_sheet()
                row, col = coords
                worksheet.update_cell(row, col, title)
                worksheet.update_cell(row, col + 1, url)
                bot.send_message(message.chat.id, 'Предмет обновлен 😎')
                start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                start_markup.row("Вывести дедлайн на неделю")
                start_markup.row("Редактор дедлайнов")
                start_markup.row("Редактор предметов")
                info = bot.send_message(message.chat.id, "Что будем делать?", reply_markup=start_markup)
                bot.register_next_step_handler(info, choose_action)
                break
            else:
                pass

            info = bot.send_message(message.chat.id, "Кривая ссылка какая-то, укажи нормально через пробел ")
            bot.register_next_step_handler(info, subject_new_name)
            break
        except:
            info = bot.send_message(message.chat.id, "Ты по-моему перепутал, укажи предмет и ссылку через пробел")
            bot.send_photo(message.chat.id, "https://i.ytimg.com/vi/EI3lfljIZxE/maxresdefault.jpg")
            bot.register_next_step_handler(info, subject_new_name)
            break


def delete_subject(message):
    """ Удаляем предмет в Google-таблице """
    while True:
        try:
            global cell
            worksheet = access_current_sheet()
            cell = worksheet.find(message.text)
            worksheet.delete_row(cell.row)
            bot.send_message(message.chat.id, 'Предмет удалён!')
            start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            start_markup.row("Вывести дедлайн на неделю")
            start_markup.row("Редактор дедлайнов")
            start_markup.row("Редактор предметов")
            info = bot.send_message(message.chat.id, "Что будем делать?", reply_markup=start_markup)
            bot.register_next_step_handler(info, choose_action)
            break
        except:
            pass

        info = bot.send_message(message.chat.id, "Выбери предмет из списка")
        bot.register_next_step_handler(info, delete_subject)
        break


def clear_subject_list(message):
    """ Удаляем все из Google-таблицы """
    while True:
        if message.text == "Удалить":
            worksheet = access_current_sheet()
            values_list = worksheet.col_values(1)[1:]
            for i in values_list:
                worksheet.delete_row(2)
            bot.send_message(message.chat.id, 'Таблица уничтожена ⚰')
            start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            start_markup.row("Вывести дедлайн на неделю")
            start_markup.row("Редактор дедлайнов")
            start_markup.row("Редактор предметов")
            info = bot.send_message(message.chat.id, "Что будем делать?", reply_markup=start_markup)
            bot.register_next_step_handler(info, choose_action)
            break
        else:
            pass

        info = bot.send_message(message.chat.id, "Для очистки таблицы введи слово 'Удалить'")
        bot.register_next_step_handler(info, clear_subject_list)
        break


@bot.message_handler(commands=["start"])
def start(message):
    try:
        with open("tables.json") as json_file:
            start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            start_markup.row("Вывести дедлайн на неделю")
            start_markup.row("Редактор дедлайнов")
            start_markup.row("Редактор предметов")
            start_markup.row("Редактор расписания")

            worksheet = access_current_sheet()
            values_list = worksheet.col_values(1)[1:]
            link_values_list = worksheet.col_values(2)[1:]
            text = ''
            for i in range(len(values_list)):
                link = link_values_list[i]
                text += "[" + str(values_list[i]) + "](" + link + ")" + '\n'
            if text != '':
                bot.send_message(message.chat.id, text, parse_mode='MarkdownV2', disable_web_page_preview=True)

            info = bot.send_message(message.chat.id, "Что будем делать?", reply_markup=start_markup)
            bot.register_next_step_handler(info, choose_action)

    except FileNotFoundError:
        start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        start_markup.row("Подключить Google-таблицу")
        start_markup.row("Вывести дедлайн на неделю")
        start_markup.row("Редактор дедлайнов")
        start_markup.row("Редактор предметов")
        start_markup.row("Редактор расписания")
        info = bot.send_message(message.chat.id, "Что будем делать?", reply_markup=start_markup)
        bot.register_next_step_handler(info, choose_action)

        worksheet = access_current_sheet()
        values_list = worksheet.col_values(1)[1:]
        link_values_list = worksheet.col_values(2)[1:]
        for i in range(len(values_list)):
            link = link_values_list[i]
            bot.send_message(message.chat.id, "[" + str(values_list[i]) + "](" + link + ")",
                             parse_mode='MarkdownV2')


bot.infinity_polling()