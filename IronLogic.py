import sys
import ctypes
import os
import aiohttp
from aiohttp import web
import asyncio
from ConverterInstance import ConverterInstance
from IronLogicApiDll import IronLogicControllerApi
import json
import threading
import queue


class ModeController:
    NORMAL = 0
    BLOCK = 1
    FREE_PASS = 2
    WAIT_FREE_PASS = 3
    ACTIVE = 1
    OFF = 0
    ONLINE = 1
    OFFLINE = 0

# Корневые объекты


# Абстракция один конвертер множество контролеров
global_converter = None

# Web - часть
appController = web.Application()
# Web - часть
appSender = web.Application()
# Web - часть
app = web.Application()


BASE_URL = 'http://192.168.0.129:8000'

#####################################################################################


async def get_http_response(urls, events) -> dict:
    '''
        Отправка данных на удалённый сервер
    '''
    tasks = []
    events = json.dumps(events)
    async with aiohttp.ClientSession() as session:
        task = asyncio.ensure_future(
            session.post(url=urls, data=events, timeout=3))  # Создай
        tasks.append(task)  # Добавь в массив заданий
        await asyncio.gather(*tasks)  # Запусти все задание
#####################################################################################


def send_post(urls, events):
    '''
        Отправка данных на удалённый сервер
    '''
    try:
        print("Отправка данных на удалённый сервер => ", events)
        asyncio.run(get_http_response(
            urls=urls, events=events))
    except Exception as e:
        print("Что то пошло не по плану SendPost", e)
#####################################################################################

#####################################################################################


def init_middleware():
    '''
        Инициализируем внутренее состояние
    '''
    global global_converter
    # Абстракция один конвертер множество контролеров
    global_converter = ConverterInstance(os.path.dirname(
        __file__)+"\\ControllerIronLogic.dll", "COM3")
    ################################################################
    # Создание первого контролера
    ################################################################
    # global_converter.add_new_controller(1, 4232, "Z5R Net 8000", 1)
    # global_converter.add_new_controller(2, 4225, "Z5R Net 8000", 1)
    global_converter.add_new_controller(2, 4779, "Z5R Net 8000", 1)
    global_converter.add_new_controller(3, 37441, "Z5R Net 2000", 1)
    global_converter.add_new_controller(4, 44624, "Z5R Net 2000", 1)
    ################################################################
    # Подготовка контролеров
    ################################################################
    # Пробегаем по каждому инициализируем внутренне состояния (dll-кишков)
    # а также смотрим какой последний был индекс события
    for controller in global_converter.arr_controllers:
        controller.EventsIterator = global_converter.controller_api.do_ctr_events_menu(
            controller.address_number, -1)
        global_converter.controller_api.update_bank_key(controller.banks)
        controller.keys_in_controller = global_converter.controller_api.get_all_key_in_controller_json()

        ################################################################
        # Собираем информацию по удалённым ключам в контролере
        index_delete_key = global_converter.controller_api.get_delete_index_key_in_controller_json()
        arr_cards = index_delete_key["cards"]
        arr_cards_index = []
        for index in arr_cards:
            arr_cards_index.append(index["pos"])
        controller.key_index_in_controller = arr_cards_index
        ################################################################

        send_post(urls=BASE_URL, events=controller.power_on())


##########################################
def send_message(message_queue, message):
    '''
    Функция для отправки сообщений в очередь
    '''
    message_queue.put(message)
##########################################


##########################################
def run_processing_message(message, serial_number):
    '''
        Функция для обработки сообщений в очередь
    '''
    # Проверяем наличие данных в очереди
    # if not message.empty():
    #     print("Сообщений нет, контролер = >", serial_number)

    while not message.empty():
        items = message.get()
        if items is None:
            print("Сообщения закончились, контролер = >", serial_number)
            break
        for item in items["messages"]:
            # print("\n\n\nПерехватил и отправил на обработку сообщение: ", items)
            response_body = global_converter.run_response(items["sn"], item)
            # print("ТО что отправлен серверу", response_body)
            # SendPost(urls=BASE_URL, Events=response_body)
##########################################


def main_middleware():
    '''
        Функция для обхода по контролерам
    '''
    # ConverterIronLogic является глобальной
    # переменой для класса используется для синхронизации данных между потоков
    global global_converter

    while (True):
        try:
            # Пробегаем по каждому контролеру если контролер
            # на данный момент активен переключаем контекст
            # обработки и опрашиваем на новые события
            for _index, controller in enumerate(global_converter.arr_controllers):

                if (controller.active == ModeController.ACTIVE):
                    # print("_Controller.serial_number= ",_Controller.serial_number,
                    #   "_Controller.Active= ",_Controller.Active,
                    #   "not _Controller.Selected= ",not _Controller.Selected)
                    # Если контролер не выбран выбираем
                    # if (not _Controller.Selected):

                    global_converter.controller_api.change_context_controller(
                        controller.address_number)
                    global_converter.selected_controller_for_operation(
                        _index)

                    run_processing_message(
                        controller.message_queue_in, controller.serial_number)

                    # Проверка на новые события
                    # (проходим по индексам текущий индекс
                    # минус старый индекс равно кол новых событий)
                    old_events_iterator = controller.EventsIterator
                    controller.EventsIterator = global_converter.controller_api.do_show_new_events(
                        controller.EventsIterator)

                    # Если новый индекс совпадает со старым значит новых событий нет
                    if old_events_iterator == controller.EventsIterator:
                        continue

                    # Вызываем гетер и берем все событие которые скопились
                    events = global_converter.controller_api.get_controller_events_json()

                    if controller.logic_mode == ModeController.OFFLINE:
                        for messages in events["messages"]:
                            # Если у нас массив сообщений не пустой тогда отправим эти данные
                            if messages["events"] != []:
                                send_post(
                                    urls=BASE_URL, events=events)
                                # ##print("Send =>  ", Events)
                        # Уже отработали в режиме автономки идем к след контролеру в цикле
                        continue

                    # Работа через двух факторный режим блокируем и потом открываем дверь
                    if (controller.logic_mode == ModeController.ONLINE):
                        # print(
                        #     "Работа через двух факторный режим блокируем и потом открываем дверь| sn = ", controller.serial_number)
                        for messages in events["messages"]:
                            if messages["events"] != []:
                                check_access = {
                                    "type": events["type"],
                                    "sn": controller.serial_number,
                                    "messages": [
                                        {
                                            "id": 1,
                                            "operation": "check_access",
                                            "card": messages["events"][0]["card"].upper(),
                                            "reader": messages["events"][0]["direct"]
                                        }
                                    ]
                                }
                                controller.ReaderSide = messages["events"][0]["direct"]
                                # print(
                                #     "Отправляю на удалённый сервер информацию = ", check_access)
                                send_post(urls=BASE_URL,
                                          events=check_access)
        except queue.Empty:
            continue


def run_response(body: any):
    '''
        Запускаем обработчик для обработки и совершение действий с контролерами
        Принимаем json и на основе поля 'operation' совершаем какие либо действие
        над контролерами
    '''
    # ConverterIronLogic является глобальной переменой
    # для класса используется для синхронизации данных между потоков
    global global_converter

    response_body = {
        "id": 123456789,
        "success ": len(body["messages"])
    }

    for message in body["messages"]:
        ################################################################
        # Если серийник с таким то номером то совершаем некоторые действия
        for controller in global_converter.arr_controllers:
            # Если серийник не совпадает с адресом который был в запросе то пропускаем итерацию
            if (body["sn"] != controller.serial_number):
                continue

            # Активация контролера
            if (message['operation'] == "set_active"):
                controller.active = message["active"]
                controller.logic_mode = message["online"]
                response_body = {
                    "id": 123456789,
                    "success ": 1
                }
                return response_body
            # Установка режима контролера(перепроверить возможно что то сломано)
            if (message['operation'] == "set_mode"):
                controller.logic_mode = message["mode"]
                response_body = {
                    "id": 123456789,
                    "success ": 1
                }
                return response_body

            # Формируем пакет сообщений
            send_message(controller.message_queue_in, body)
            send_message(controller.message_queue_in, None)
            # Заканчиваем (ставим разделитель)на пакет сообщений

            if message['operation'] == "read_cards":
                # while not controller.message_queue_out.empty():

                while True:
                    if not controller.message_queue_out.empty():
                        # print("Жду")
                        # print("controller.message_queue_out=> ",
                        #       controller.message_queue_out)
                        items = controller.message_queue_out.get()
                        if items is None:
                            print(
                                "Сообщения закончились, контролер => интернет = >", controller.serial_number)
                            break
                        else:
                            response_body = {
                                "type": controller.name_controller,
                                "sn": controller.serial_number,
                                "messages": [items]}

    return response_body


def start_service():
    '''
        Точка входа в программу запуск сервиса обработки
    '''
    ################## Обработчик входящих подключений ##################################
    async def mock(request):
        #########################################
        # Обработчик входящих подключений
        body = await request.json()

        print("Принял сообщение=>", body)

        # пустое сообщение обрабатываем
        if len(body['messages']) == 0:
            return web.json_response({"Ответ": "сообщения нет, нечего обрабатывать"})
        #########################################
        # Обработка включение контролера от упр сервера
        response_body = run_response(body)
        #########################################
        return web.json_response(response_body)
    #####################################################################################

    def run_controller_thread():
        # Инициализация контролеров
        init_middleware()
        # Обработчик действий с контролера
        appController.cleanup_ctx.append(main_middleware())

    def run_app_thread():
        app.add_routes([web.get('/', mock)])
        web.run_app(host="127.0.0.1", port=8080, app=app)

    threads = (
        threading.Thread(target=run_controller_thread),
        threading.Thread(target=run_app_thread)
    )

    for tread in threads:
        tread.start()

#####################################################################################


if __name__ == '__main__':
    # win32api.SetDllDirectory(sys._MEIPASS)
    # ctypes.windll.kernel32.SetDllDirectoryW(None)
    start_service()
