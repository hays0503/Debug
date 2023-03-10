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
ConverterIronLogic = ConverterInstance('./ControllerIronLogic.dll')

# Web - часть
appController = web.Application()
# Web - часть
appSender = web.Application()
# Web - часть
app = web.Application()


BASE_URL = 'http://192.168.0.129:8000'

#####################################################################################


async def get_http_response(urls, Events) -> dict:
    '''
        Отправка данных на удалённый сервер
    '''
    tasks = []
    Events = json.dumps(Events)
    async with aiohttp.ClientSession() as session:
        task = asyncio.ensure_future(
            session.post(url=urls, data=Events, timeout=3))  # Создай
        tasks.append(task)  # Добавь в массив заданий
        responses = await asyncio.gather(*tasks)  # Запусти все задание
    return f'Exit in func => get_http_response()'
#####################################################################################


def SendPost(urls, Events):
    '''
        Отправка данных на удалённый сервер
    '''
    # print(Events)
    try:
        data = asyncio.run(get_http_response(
            urls=urls, Events=Events))
        # print("\nget_http_response => ", data)
    except Exception as e:
        print("Что то пошло не по плану", e)
#####################################################################################

#####################################################################################


def InitMiddleware():

    ################################################################
    # Создание первого контролера
    ################################################################
    ConverterIronLogic.AddNewController(1, 4232, "Z5R Net 8000", 1)
    ConverterIronLogic.AddNewController(2, 4225, "Z5R Net 8000", 1)
    ################################################################
    # Подготовка контролеров
    ################################################################
    # Пробегаем по каждому инициализируем внутренне состояния (dll-кишков)
    # а также смотрим какой последний был индекс события
    for Controller in ConverterIronLogic._Controllers:
        Controller.EventsIterator = ConverterIronLogic.ControllerApi.Do_Ctr_Events_Menu(
            Controller.AddressNumber, -1)
        ConverterIronLogic.ControllerApi.Update_Bank_Key(Controller.Banks)
        Controller.KeysInController = ConverterIronLogic.ControllerApi.GetAllKeyInControllerJson()

        ################################################################
        # Собираем информацию по удалённым ключам в контролере
        JsonDllGetDeleteIndexKey = ConverterIronLogic.ControllerApi.GetDeleteIndexKeyInControllerJson()
        ArrCards = JsonDllGetDeleteIndexKey["cards"]
        ArrCardsIndex = []
        for Index in ArrCards:
            ArrCardsIndex.append(Index["pos"])
        Controller.KeyIndexInController = ArrCardsIndex
        ################################################################

        SendPost(urls=BASE_URL, Events=Controller.POWER_ON())


##########################################
# Функция для отправки сообщений в очередь
def send_message(message_queue, message):
    message_queue.put(message)
##########################################


##########################################
# Функция для обработки сообщений в очередь
def run_processing_message(message, sn):
    # Проверяем наличие данных в очереди
    if (not message.empty()):
        print("Сообщений нет, контролер = >", sn)

    while not message.empty():
        items = message.get()
        if items is None:
            print("Сообщения закончились, контролер = >", sn)
            break
        for item in items["messages"]:
            print("\n\n\nПерехватил и отправил на обработку сообщение: ", items)
            response_body = ConverterIronLogic.RunResponse(items["sn"], item)
            print("ТО что отправлен серверу", response_body)
            # SendPost(urls=BASE_URL, Events=response_body)
##########################################


def MainMiddleware():
    # ConverterIronLogic является глобальной переменой для класса используется для синхронизации данных между потоков
    global ConverterIronLogic

    while (True):
        try:
            # Пробегаем по каждому контролеру если контролер
            # на данный момент активен переключаем контекст
            # обработки и опрашиваем на новые события
            for _index, _Controller in enumerate(ConverterIronLogic._Controllers):

                if (_Controller.Active == ModeController.ACTIVE):
                    # print("_Controller.SerialNumber= ",_Controller.SerialNumber,
                    #   "_Controller.Active= ",_Controller.Active,
                    #   "not _Controller.Selected= ",not _Controller.Selected)
                    # Если контролер не выбран выбираем
                    # if (not _Controller.Selected):
                    ConverterIronLogic.ControllerApi.Change_Context_Controller(
                        _Controller.AddressNumber)
                    ConverterIronLogic.SelectedControllerForOperation(_index)

                    run_processing_message(
                        _Controller.message_queue, _Controller.SerialNumber)

                    # Проверка на новые события
                    # (проходим по индексам текущий индекс минус старый индекс равно кол новых событий)
                    OldEventsIterator = _Controller.EventsIterator
                    _Controller.EventsIterator = ConverterIronLogic.ControllerApi.Do_Show_New_Events(
                        _Controller.EventsIterator)

                    # Если новый индекс совпадает со старым значит новых событий нет
                    if (OldEventsIterator == _Controller.EventsIterator):
                        continue

                    # Вызываем гетер и берем все событие которые скопились
                    Events = ConverterIronLogic.ControllerApi.GetControllerEventsJson()

                    if (_Controller.LogicMode == ModeController.OFFLINE):
                        for messages in Events["messages"]:
                            # Если у нас массив сообщений не пустой тогда отправим эти данные
                            if messages["events"] != []:
                                SendPost(
                                    urls=BASE_URL, Events=Events)
                                # ##print("Send =>  ", Events)
                        # Уже отработали в режиме автономки идем к след контролеру в цикле
                        continue

                    # Работа через двух факторный режим блокируем и потом открываем дверь
                    if (_Controller.LogicMode == ModeController.ONLINE):
                        for messages in Events["messages"]:
                            if messages["events"] != []:
                                Check_access = {
                                    "type": Events["type"],
                                    "sn": _Controller.SerialNumber,
                                    "messages": [
                                        {
                                            "id": 1,
                                            "operation": "check_access",
                                            "card": messages["events"][0]["card"].upper(),
                                            "reader": messages["events"][0]["direct"]
                                        }
                                    ]
                                }
                                _Controller.ReaderSide = messages["events"][0]["direct"]
                                SendPost(urls=BASE_URL,
                                         Events=Check_access)
        except queue.Empty:
            continue


def RunResponse(body: any):
    '''
        Запускаем обработчик для обработки и совершение действий с контролерами
        Принимаем json и на основе поля 'operation' совершаем какие либо действие
        над контролерами
    '''
    # ConverterIronLogic является глобальной переменой для класса используется для синхронизации данных между потоков
    global ConverterIronLogic

    response_body = {
        "id": 123456789,
        "success ": len(body["messages"])
    }

    for message in body["messages"]:
        ################################################################
        # Если серийник с таким то номером то совершаем некоторые действия
        for _index, _Controller in enumerate(ConverterIronLogic._Controllers):
            # Если серийник не совпадает с адресом который был в запросе то пропускаем итерацию
            if (body["sn"] != _Controller.SerialNumber):
                continue

            # Активация контролера
            if (message['operation'] == "set_active"):
                _Controller.Active = message["active"]
                _Controller.LogicMode = message["online"]
                response_body = {
                    "id": 123456789,
                    "success ": 1
                }
                return response_body
            # Установка режима контролера(перепроверить возможно что то сломано)
            if (message['operation'] == "set_mode"):
                _Controller.LogicMode = message["mode"]
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
            send_message(_Controller.message_queue, body)

        # Заканчиваем (ставим разделитель)на пакет сообщений
    send_message(_Controller.message_queue, None)

    return response_body


def RunServer():
    ################## Обработчик входящих подключений ##################################
    async def Mock(request):
        #########################################
        # Обработчик входящих подключений
        body = await request.json()

        print("body=>", body)

        if (len(body['messages']) == 0):
            return web.json_response({"ok": "ok"})
        #########################################
        # Обработка включение контролера от упр сервера
        response_body = RunResponse(body)
        #########################################
        return web.json_response(response_body)
    #####################################################################################

    def Run_Controller_Thread():
        # Инициализация контролеров
        time.sleep(5)
        InitMiddleware()
        # Обработчик действий с контролера
        appController.cleanup_ctx.append(MainMiddleware())

    def Run_App_Thread():
        app.add_routes([web.get('/', Mock)])
        web.run_app(host="192.168.0.34", port=8080, app=app)

    threads = (
        threading.Thread(target=Run_Controller_Thread),
        threading.Thread(target=Run_App_Thread)
    )

    for t in threads:
        t.start()

#####################################################################################


if __name__ == '__main__':
    RunServer()
