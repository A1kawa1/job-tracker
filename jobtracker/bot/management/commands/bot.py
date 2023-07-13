from django.core.management.base import BaseCommand
from django.utils import timezone
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List
from enum import Enum
import datetime
import telebot
import os

from models.models import User, Task, Work


class Command(BaseCommand):
    help = 'Запуск тг бота'
    def handle(self, *args, **options):
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
        # data_task = {}


        # @dataclass
        # class Work:
        #     time_start: datetime.datetime = None
        #     time_end: datetime.datetime = None


        # @dataclass
        # class Task:
        #     name: str = None
        #     profit: str = None
        #     date_start: datetime.datetime = None
        #     date_end: datetime.datetime = None
        #     works: List[Work] = None
        #     spent_seconds: int = 0


        def create_task(message):
            id = message.from_user.id
            date_start = datetime.datetime.fromtimestamp(message.date).date()
            text = message.text

            user = User.objects.get(pk=id)
            user_tasks = user.tasks.all()
            if not user_tasks is None or len(user_tasks) != 0:
                for el in user_tasks:
                    if el.name == text:
                        bot.send_message(
                            text='Простите, но задача с таким названием уже существует',
                            chat_id=id
                        )
                        return
            if len(text) > 100:
                bot.send_message(
                    text='Укажите пожалуйста название длинной меньше 100 символов',
                    chat_id=id
                )
                return

            if user_tasks is None or len(user_tasks) == 0:
                bot.send_message(
                    text=('Поздравляю, вы создали свою первую задачу.\n'
                        'Все задачи можете посмотреть тут /all_tasks'),
                    chat_id=id
                )
            else:
                bot.send_message(
                    text=('Поздравляю, вы создали новую задачу.\n'
                        'Все задачи можете посмотреть тут /all_tasks'),
                    chat_id=id
                )
            Task.objects.create(
                user=user,
                name=text,
                date_start=date_start
            )


        def stop_task(message, index):
            id = message.chat.id
            date_end = datetime.datetime.fromtimestamp(message.date).date()
            profit = message.text
            if len(profit) > 100:
                bot.send_message(
                    text='Укажите пожалуйста пользу длинной меньше 100 символов',
                    chat_id=id
                )
                return
            task = Task.objects.get(pk=index)
            task.date_end = date_end
            task.profit = profit
            task.save()
            bot.send_message(
                text=f'Супер, теперь вы сможете увидеть информацию по этой задаче',
                chat_id=id
            )

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
            bot.clear_step_handler_by_chat_id(chat_id=message.from_user.id)
            user, _ = User.objects.get_or_create(
                id=message.from_user.id,
            )
            user.first_name = message.from_user.first_name
            user.last_name = message.from_user.last_name
            user.username = message.from_user.username
            user.save()
            name = user.first_name
            if name is None or name == '':
                name = user.username
            bot.send_message(
                text=MessageText.start_message.value.format(name=name),
                chat_id=message.from_user.id
            )


        @bot.message_handler(commands=['all_tasks'])
        def all_tasks(message):
            id = message.from_user.id
            bot.clear_step_handler_by_chat_id(chat_id=id)
            user = User.objects.get(pk=id)
            user_tasks = list(Task.objects.filter(user=user))[::-1]
            if user_tasks is None or len(user_tasks) == 0:
                bot.send_message(
                    text='Пока у вас нет ни одной задачи, давайте же создадим их /new_task',
                    chat_id=id
                )
                return

            markup = telebot.types.InlineKeyboardMarkup()
            for task in user_tasks:
                name = task.name
                date_end = task.date_end
                if not date_end is None:
                    markup.add(telebot.types.InlineKeyboardButton(
                        text=name,
                        callback_data=f'success_{task.pk}'
                    ))
                else:
                    markup.add(telebot.types.InlineKeyboardButton(
                        text=name,
                        callback_data=f'current_{task.pk}'
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
                user = User.objects.get(pk=id)
                user_tasks = list(Task.objects.filter(user=user))[::-1]

                markup = telebot.types.InlineKeyboardMarkup()
                for task in user_tasks:
                    name = task.name
                    date_end = task.date_end
                    if not date_end is None:
                        markup.add(telebot.types.InlineKeyboardButton(
                            text=name,
                            callback_data=f'success_{task.pk}'
                        ))
                    else:
                        markup.add(telebot.types.InlineKeyboardButton(
                            text=name,
                            callback_data=f'current_{task.pk}'
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
                task = Task.objects.get(pk=index)
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
                task = Task.objects.get(pk=index)
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
                task = Task.objects.get(pk=index)
                works = Work.objects.filter(task=task)
                time_start = timezone.now()
                if works is None or len(works) == 0:
                    Work.objects.create(
                        task=task,
                        time_start=time_start
                    )
                    bot.send_message(
                        text=MessageText.start_work_message.value,
                        chat_id=id
                    )
                else:
                    last_work = works.last()
                    if last_work.time_end is None:
                        bot.send_message(
                            text='Простите, но у вас есть незавершенная работа. Сначала вам надо завершить ее.',
                            chat_id=id
                        )
                    else:
                        Work.objects.create(
                            task=task,
                            time_start=time_start
                        )
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
                time_end = timezone.now()
                task = Task.objects.get(pk=index)
                works = Work.objects.filter(task=task)
                if works is None or len(works) == 0:
                    bot.send_message(
                        text='Простите, но у вас нет начатой работы. Сначала вам надо начать новую',
                        chat_id=id
                    )
                else:
                    last_work = works.last()
                    if not last_work.time_end is None:
                        bot.send_message(
                            text='Простите, но у вас нет начатой работы. Сначала вам надо начать новую',
                            chat_id=id
                        )
                    else:
                        last_work.time_end = time_end
                        last_work.save()
                        bot.send_message(
                            text=MessageText.end_work_message.value,
                            chat_id=id
                        )
                        print(last_work.time_start, last_work.time_end)
                        delta = last_work.time_end - last_work.time_start
                        delta = int(delta.total_seconds())
                        task.spent_seconds += delta
                        task.save()
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