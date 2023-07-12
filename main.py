from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List
from enum import Enum
import datetime
import telebot
import os


load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = telebot.TeleBot(token=TOKEN)

class MessageText(Enum):
    start_message = ('{name}, я помогу вам фиксировать вашу работу или разного рода занятия.\n'
                    'Для этого можете использовать команды ниже:\n'
                    '/all_tasks - все мои задачи\n'
                    '/new_task - создает новую задачу\n')
    all_tasks_message = 'Вот все ваши задачи, нажава на них, вы сможете посмотреть информацию'
    new_task_message = 'Давайте придумаем название вашей новой задаче'
    end_task_message = 'Отлично, вы завершили задачу. Теперь укажите, что она вам принесла'
    start_work_message = 'Отлично, вы начали работу'
    end_work_message = 'Отлично, вы завершили работу'
data_task = {}


@dataclass
class Work:
    time_start: datetime.datetime = None
    time_end: datetime.datetime = None


@dataclass
class Task:
    name: str = None
    profit: str = None
    date_start: datetime.datetime = None
    date_end: datetime.datetime = None
    works: List[Work] = None
    spent_seconds: int = 0


def create_task(message):
    global data_task
    id = message.from_user.id
    date_start = datetime.datetime.fromtimestamp(message.date).date()
    text = message.text

    user_tasks = data_task.get(id)
    if not user_tasks is None:
        for el in user_tasks:
            if el.name == text:
                bot.send_message(
                    text='Простите, но задача с таким названием уже существует',
                    chat_id=id
                )
                return
    if user_tasks is None:
        data_task[id] = [Task(name=text, date_start=date_start)]
        bot.send_message(
            text=('Поздравляю, вы создали свою первую задачу.\n'
                  'Все задачи можете посмотреть тут /all_tasks'),
            chat_id=id
        )
    else:
        data_task[id].append(Task(name=text, date_start=date_start))
        bot.send_message(
            text=('Поздравляю, вы создали новую задачу.\n'
                  'Все задачи можете посмотреть тут /all_tasks'),
            chat_id=id
        )


def stop_task(message, index):
    global data_task
    id = message.chat.id
    date_end = datetime.datetime.fromtimestamp(message.date).date()
    profit = message.text
    task = data_task[id][index]
    task.date_end = date_end
    task.profit = profit
    bot.send_message(
        text=f'Супер, теперь вы сможете увидеть информацию по этой задаче',
        chat_id=id
    )

    task = data_task.get(id)[index]
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        text=f'Начало: {task.date_start}',
        callback_data='gtrrtggtr'
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        text=f'Конец: {task.date_end}',
        callback_data='gtrrtggtr'
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        text=f'Потраченное время: {int(task.spent_seconds//60//60)}ч {int(task.spent_seconds//60%60)}мин',
        callback_data='gtrrtggtr'
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        text=f'Профит: {task.profit}',
        callback_data='gtrrtggtr'
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        text='Назад',
        callback_data=f'back'
    ))
    markup.add(telebot.types.InlineKeyboardButton(
        text='Закрыть',
        callback_data='close'
    ))
    bot.send_message(
        text=f'Задача - {task.name}',
        chat_id=id,
        reply_markup=markup
    )

@bot.message_handler(commands=['start'])
def start(message):
    id, name = message.from_user.id, message.from_user.first_name
    bot.clear_step_handler_by_chat_id(chat_id=id)
    if name is None or name == '':
        name = message.from_user.username
    bot.send_message(
        text=MessageText.start_message.value.format(name=name),
        chat_id=id
    )


@bot.message_handler(commands=['all_tasks'])
def all_tasks(message):
    id = message.from_user.id
    bot.clear_step_handler_by_chat_id(chat_id=id)
    user_tasks = data_task.get(id)
    if user_tasks is None:
        bot.send_message(
            text='Пока у вас нет ни одной задачи, давайте же создадим их /new_task',
            chat_id=id
        )
        return

    markup = telebot.types.InlineKeyboardMarkup()
    for index in range(len(user_tasks)-1, -1, -1):
        task = user_tasks[index]
        name = task.name
        date_end = task.date_end
        if not date_end is None:
            markup.add(telebot.types.InlineKeyboardButton(
                    text=name,
                    callback_data=f'success_{index}'
            ))
        else:
            markup.add(telebot.types.InlineKeyboardButton(
                    text=name,
                    callback_data=f'current_{index}'
            ))
    markup.add(telebot.types.InlineKeyboardButton(
        text='Закрыть',
        callback_data='close'
    ))
    
    bot.send_message(
        text=MessageText.all_tasks_message.value,
        chat_id=id,
        reply_markup=markup
    )


@bot.message_handler(commands=['new_task'])
def new_task(message):
    id = message.from_user.id
    bot.clear_step_handler_by_chat_id(chat_id=id)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(
        text='Закрыть',
        callback_data='close'
    ))
    bot.send_message(
        text=MessageText.new_task_message.value,
        chat_id=id,
        reply_markup=markup
    )
    bot.register_next_step_handler(message, create_task)


@bot.callback_query_handler(func=lambda _: True)
def query_handler(call):
    id = call.message.chat.id
    if call.data == 'close':
        bot.delete_message(
            chat_id=id,
            message_id=call.message.message_id
        )
        bot.clear_step_handler_by_chat_id(chat_id=id)
    elif call.data == 'back':
        bot.delete_message(
            chat_id=id,
            message_id=call.message.message_id
        )
        bot.clear_step_handler_by_chat_id(chat_id=id)
        user_tasks = data_task.get(id)
        markup = telebot.types.InlineKeyboardMarkup()
        for index in range(len(user_tasks)-1, -1, -1):
            task = user_tasks[index]
            name = task.name
            date_end = task.date_end
            if not date_end is None:
                markup.add(telebot.types.InlineKeyboardButton(
                        text=name,
                        callback_data=f'success_{index}'
                ))
            else:
                markup.add(telebot.types.InlineKeyboardButton(
                        text=name,
                        callback_data=f'current_{index}'
            ))
        markup.add(telebot.types.InlineKeyboardButton(
            text='Закрыть',
            callback_data='close'
        ))
        bot.send_message(
            text=MessageText.all_tasks_message.value,
            chat_id=id,
            reply_markup=markup
        )
    elif call.data.startswith('success_'):
        bot.delete_message(
            chat_id=id,
            message_id=call.message.message_id
        )
        index = int(call.data.replace('success_', ''))
        task = data_task.get(id)[index]
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Начало: {task.date_start}',
            callback_data='gtrrtggtr'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Конец: {task.date_end}',
            callback_data='gtrrtggtr'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Потраченное время: {int(task.spent_seconds//60//60)}ч {int(task.spent_seconds//60%60)}мин',
            callback_data='gtrrtggtr'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Профит: {task.profit}',
            callback_data='gtrrtggtr'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text='Назад',
            callback_data=f'back'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text='Закрыть',
            callback_data='close'
        ))
        bot.send_message(
            text=f'Задача - {task.name}',
            chat_id=id,
            reply_markup=markup
        )
    elif call.data.startswith('current_'):
        bot.delete_message(
            chat_id=id,
            message_id=call.message.message_id
        )
        index = int(call.data.replace('current_', ''))
        task = data_task.get(id)[index]
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Начать работу',
            callback_data=f'start_work_{index}'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Закончить работу',
            callback_data=f'end_work_{index}'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Завершить задачу',
            callback_data=f'end_task_{index}'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text='Назад',
            callback_data=f'back'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text='Закрыть',
            callback_data='close'
        ))
        bot.send_message(
            text=f'Задача - {task.name}, {int(task.spent_seconds//60//60)}ч {int(task.spent_seconds//60%60)}мин',
            chat_id=id,
            reply_markup=markup
        )
    elif call.data.startswith('start_work_'):
        bot.delete_message(
            chat_id=id,
            message_id=call.message.message_id
        )
        index = int(call.data.replace('start_work_', ''))
        task = data_task.get(id)[index]
        time_start = datetime.datetime.now()
        if task.works is None:
            task.works = [Work(time_start=time_start)]
            bot.send_message(
                text=MessageText.start_work_message.value,
                chat_id=id
            )
        else:
            last_work = task.works[-1]
            if last_work.time_end is None:
                bot.send_message(
                    text='Простите, но у вас есть незавершенная работа. Сначала вам надо завершить ее.',
                    chat_id=id
                )
            else:
                task.works.append(Work(time_start=time_start))
                bot.send_message(
                    text=MessageText.start_work_message.value,
                    chat_id=id
                )
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Начать работу',
            callback_data=f'start_work_{index}'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Закончить работу',
            callback_data=f'end_work_{index}'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Завершить задачу',
            callback_data=f'end_task_{index}'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text='Назад',
            callback_data=f'back'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text='Закрыть',
            callback_data='close'
        ))
        bot.send_message(
            text=f'Задача - {task.name}, {int(task.spent_seconds//60//60)}ч {int(task.spent_seconds//60%60)}мин',
            chat_id=id,
            reply_markup=markup
        )
    elif call.data.startswith('end_work_'):
        bot.delete_message(
            chat_id=id,
            message_id=call.message.message_id
        )
        index = int(call.data.replace('end_work_', ''))
        time_end = datetime.datetime.now()
        task = data_task.get(id)[index]
        if task.works is None:
            bot.send_message(
                text='Простите, но у вас нет начатых работ. Сначала вам надо начать новую',
                chat_id=id
            )
        else:
            last_work = task.works[-1]
            if not last_work.time_end is None:
                bot.send_message(
                    text='Простите, но у вас нет начатых работ. Сначала вам надо начать новую',
                    chat_id=id
                )
            else:
                task.works[-1].time_end = time_end
                bot.send_message(
                    text=MessageText.end_work_message.value,
                    chat_id=id
                )
                print(task.works[-1].time_end, task.works[-1].time_start)
                delta = task.works[-1].time_end - task.works[-1].time_start
                delta = int(delta.total_seconds())
                task.spent_seconds += delta
                print(delta, task.spent_seconds)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Начать работу',
            callback_data=f'start_work_{index}'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Закончить работу',
            callback_data=f'end_work_{index}'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text=f'Завершить задачу',
            callback_data=f'end_task_{index}'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text='Назад',
            callback_data=f'back'
        ))
        markup.add(telebot.types.InlineKeyboardButton(
            text='Закрыть',
            callback_data='close'
        ))
        bot.send_message(
            text=f'Задача - {task.name}, {int(task.spent_seconds//60//60)}ч {int(task.spent_seconds//60%60)}мин',
            chat_id=id,
            reply_markup=markup
        )
    elif call.data.startswith('end_task_'):
        index = int(call.data.replace('end_task_', ''))
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(
            text='Закрыть',
            callback_data='close'
        ))
        bot.delete_message(
            chat_id=id,
            message_id=call.message.message_id
        )
        bot.send_message(
            text=MessageText.end_task_message.value,
            chat_id=id,
            reply_markup=markup
        )
        bot.register_next_step_handler(call.message, stop_task, index)


bot.infinity_polling(timeout=600)
