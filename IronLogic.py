from contextlib import suppress
import aiohttp
from aiohttp import web
import asyncio
from ControllerInstance import ControllerInstance
from ConverterInstance import ConverterInstance
from IronLogicApiDll import IronLogicControllerApi
from datetime import datetime
import time
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
global_сonverter = ConverterInstance('./ControllerIronLogic.dll')

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

    ################################################################
    # Создание первого контролера
    ################################################################
    global_сonverter.add_new_controller(1, 4232, "Z5R Net 8000", 1)
    global_сonverter.add_new_controller(2, 4225, "Z5R Net 8000", 1)
    ################################################################
    # Подготовка контролеров
    ################################################################
    # Пробегаем по каждому инициализируем внутренне состояния (dll-кишков)
    # а также смотрим какой последний был индекс события
    for controller in global_сonverter.arr_controllers:
        controller.EventsIterator = global_сonverter.controller_api.do_ctr_events_menu(
            controller.AddressNumber, -1)
        global_сonverter.controller_api.update_bank_key(controller.Banks)
        controller.KeysInController = global_сonverter.controller_api.get_all_key_in_controller_json()

        ################################################################
        # Собираем информацию по удалённым ключам в контролере
        index_delete_key = global_сonverter.controller_api.get_delete_index_key_in_controller_json()
        arr_cards = index_delete_key["cards"]
        arr_cards_index = []
        for index in arr_cards:
            arr_cards_index.append(index["pos"])
        controller.KeyIndexInController = arr_cards_index
        ################################################################

        send_post(urls=BASE_URL, events=controller.POWER_ON())


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
    if not message.empty():
        print("Сообщений нет, контролер = >", serial_number)

    while not message.empty():
        items = message.get()
        if items is None:
            print("Сообщения закончились, контролер = >", serial_number)
            break
        for item in items["messages"]:
            print("\n\n\nПерехватил и отправил на обработку сообщение: ", items)
            response_body = global_сonverter.run_response(items["sn"], item)
            print("ТО что отправлен серверу", response_body)
            # SendPost(urls=BASE_URL, Events=response_body)
##########################################


def main_middleware():
    '''
        Функция для обхода по контролерам
    '''
    # ConverterIronLogic является глобальной
    # переменой для класса используется для синхронизации данных между потоков
    global global_сonverter

    while (True):
        try:
            # Пробегаем по каждому контролеру если контролер
            # на данный момент активен переключаем контекст
            # обработки и опрашиваем на новые события
            for _index, controller in enumerate(global_сonverter.arr_controllers):

                if (controller.Active == ModeController.ACTIVE):
                    # print("_Controller.SerialNumber= ",_Controller.SerialNumber,
                    #   "_Controller.Active= ",_Controller.Active,
                    #   "not _Controller.Selected= ",not _Controller.Selected)
                    # Если контролер не выбран выбираем
                    # if (not _Controller.Selected):
                    global_сonverter.controller_api.change_context_controller(
                        controller.AddressNumber)
                    global_сonverter.selected_controller_for_operation(
                        _index)

                    run_processing_message(
                        controller.message_queue_in, controller.SerialNumber)

                    # Проверка на новые события
                    # (проходим по индексам текущий индекс
                    # минус старый индекс равно кол новых событий)
                    old_events_iterator = controller.EventsIterator
                    controller.EventsIterator = global_сonverter.controller_api.do_show_new_events(
                        controller.EventsIterator)

                    # Если новый индекс совпадает со старым значит новых событий нет
                    if old_events_iterator == controller.EventsIterator:
                        continue

                    # Вызываем гетер и берем все событие которые скопились
                    events = global_сonverter.controller_api.get_controller_events_json()

                    if controller.LogicMode == ModeController.OFFLINE:
                        for messages in events["messages"]:
                            # Если у нас массив сообщений не пустой тогда отправим эти данные
                            if messages["events"] != []:
                                send_post(
                                    urls=BASE_URL, events=events)
                                # ##print("Send =>  ", Events)
                        # Уже отработали в режиме автономки идем к след контролеру в цикле
                        continue

                    # Работа через двух факторный режим блокируем и потом открываем дверь
                    if (controller.LogicMode == ModeController.ONLINE):
                        for messages in events["messages"]:
                            if messages["events"] != []:
                                check_access = {
                                    "type": events["type"],
                                    "sn": controller.SerialNumber,
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
    global global_сonverter

    response_body = {
        "id": 123456789,
        "success ": len(body["messages"])
    }

    for message in body["messages"]:
        ################################################################
        # Если серийник с таким то номером то совершаем некоторые действия
        for controller in global_сonverter.arr_controllers:
            # Если серийник не совпадает с адресом который был в запросе то пропускаем итерацию
            if (body["sn"] != controller.SerialNumber):
                continue

            # Активация контролера
            if (message['operation'] == "set_active"):
                controller.Active = message["active"]
                controller.LogicMode = message["online"]
                response_body = {
                    "id": 123456789,
                    "success ": 1
                }
                return response_body
            # Установка режима контролера(перепроверить возможно что то сломано)
            if (message['operation'] == "set_mode"):
                controller.LogicMode = message["mode"]
                response_body = {
                    "id": 123456789,
                    "success ": 1
                }
                return response_body

            # if (message['operation'] == "read_cards"):
            #     # if (not _Controller.Selected):
            #     ConverterIronLogic.ControllerApi.Change_Context_Controller(
            #         _Controller.AddressNumber)
            #     # ConverterIronLogic.SelectedControllerForOperation(_index)
            #     ConverterIronLogic.ControllerApi.Update_Bank_Key(
            #         _Controller.Banks)
            #     answer = ConverterIronLogic.ControllerApi.GetAllKeyInControllerJson()
            #     _Controller.KeysInController = answer
            #     response_body = answer
            #     # return answer

            # Формируем пакет сообщений
            send_message(controller.message_queue_in, body)
            # Заканчиваем (ставим разделитель)на пакет сообщений
            send_message(controller.message_queue_in, None)
            
            if message['operation'] == "read_cards":
                # Проверяем наличие данных в очереди
                if not controller.message_queue_out.empty():
                    print("Сообщений нет, контролер => интернет ", controller.serial_number)

                while not message.message_queue_out.empty():
                    items = message.message_queue_out.get()
                    if items is None:
                        print("Сообщения закончились, контролер => интернет = >", controller.serial_number)
                        break
                    print("ТО что отправлен серверу", items)
                    return items
                
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

        print("body=>", body)

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
        web.run_app(host="192.168.0.34", port=8080, app=app)

    threads = (
        threading.Thread(target=run_controller_thread),
        threading.Thread(target=run_app_thread)
    )

    for tread in threads:
        tread.start()

#####################################################################################


if __name__ == '__main__':
    start_service()
