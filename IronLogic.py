
from contextlib import suppress
import aiohttp
from aiohttp import web
import asyncio
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


class InfoInController:
    '''
        Информация о контролере
    '''
    ControllerApi: IronLogicControllerApi
    EventIndexInControllerV1: int = 0
    ModeControllerV1: int = ModeController.NORMAL
    EventIndexInControllerV2: int = 0
    ModeControllerV2: int = ModeController.NORMAL
    ActiveControllerV1: int = 0
    ActiveControllerV2: int = 0
    ONLINEControllerV1: int = 0
    ONLINEControllerV2: int = 0


# Корневые объекты

# Абстракция один конвертер множество контролеров
ConverterIronLogic = ConverterInstance('./ControllerIronLogic.dll')

# Старая реализация для проверки (рефакториться)
Controller = InfoInController()

# Web - часть
appController = web.Application()
# Web - часть
appSender = web.Application()
# Web - часть
app = web.Application()
# Web - часть
message_queue = queue.Queue()

BASE_URL = 'http://192.168.0.129:8000'

#####################################################################################


def POWER_ON():
    '''
        Сообщение включение (web-json)
    '''
    JsonObject = {
        "id": 123456789,
        "operation": "power_on",
        "fw": "1.0.1",
        "conn_fw": "2.0.2",
        "active": 0,
        "mode": 0,
        "controller_ip": "192.168.0.222"
    }
    return JsonObject
#####################################################################################

#####################################################################################


def Build_Message(type: str, sn: str, Messages):
    '''
        Построение типового (web-json)
    '''
    ObjectBuildMessage = {
        "type": type,
        "sn": sn,
        "messages": [Messages]
    }
    return ObjectBuildMessage
#####################################################################################

#####################################################################################


async def get_http_response(urls, Events) -> dict:
    '''
        Отправка данных на удалённый сервер
    '''
    tasks = []
    Events = json.dumps(Events)
    print("print(type(Events)) =>", type(Events))
    async with aiohttp.ClientSession() as session:
        task = asyncio.ensure_future(
            session.post(url=urls, data=Events, timeout=3))  # Создай
        tasks.append(task)  # Добавь в массив заданий
        responses = await asyncio.gather(*tasks)  # Запусти все задание
        print("\n\nresponses ====>", responses,
              "type(responses) ======>", type(responses))
        # print("\nresponses.content ====>", responses[0].content.readany())
        async for line in responses[0].content:
            print(line)
    return f'Exit in func => get_http_response()'
#####################################################################################


async def run_task(_app, urls, Events):
    task = asyncio.create_task(get_http_response())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task  # Ensure any exceptions etc. are raised.

#####################################################################################


def SendPost(urls, Events):
    '''
        Отправка данных на удалённый сервер
    '''
    print(Events)
    try:
        data = asyncio.run(get_http_response(
            urls=urls, Events=Events))
        print("\nget_http_response => ", data)
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
        SendPost(urls=BASE_URL, Events=Controller.POWER_ON())


##########################################
# Функция для отправки сообщений в очередь


def send_message(message):
    message_queue.put(message)
##########################################


def MainMiddleware():
    global ConverterIronLogic

    # start_time = datetime.now()
    ##########################################

    while (True):
        try:
            # Пробегаем по каждому контролеру если контролер
            # на данный момент активен переключаем контекст
            # обработки и опрашиваем на новые события
            for _index ,_Controller in enumerate(ConverterIronLogic._Controllers):

                if (_Controller.Active == ModeController.ACTIVE):

                    # Если контролер не выбран выбираем
                    if (not _Controller.Selected):
                        ConverterIronLogic.ControllerApi.Change_Context_Controller(
                            _Controller.AddressNumber)
                        ConverterIronLogic.SelectedControllerForOperation(
                            _index)

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
                                print("Send =>  ", Events)
                        # Уже отработали в режиме автономки идем к след контролеру в цикле
                        continue

                    # Работа через двух факторный режим блокируем и потом открываем дверь
                    if (_Controller.LogicMode == ModeController.ONLINE):
                        for messages in Events["messages"]:
                            if messages["events"] != []:
                                Check_access = {
                                    "type": Events["type"],
                                    "sn": Events["sn"],
                                    "messages": [
                                        {
                                            "id": 1,
                                            "operation": "check_access",
                                            "card": messages["events"][0]["card"],
                                            "reader": messages["events"][0]["direct"]
                                        }
                                    ]
                                }
                                _Controller.ReaderSide = messages["events"][0]["direct"]
                                print("Send =>  ", Check_access)
                                SendPost(urls=BASE_URL,
                                         Events=Check_access)

            # ###########################################################
            # if (Controller.ActiveControllerV1 == ModeController.ACTIVE):
            #     Controller.ControllerApi.Change_Context_Controller(1)
            #     Controller.EventIndexInControllerV1 = Controller.ControllerApi.Do_Show_New_Events(
            #         Controller.EventIndexInControllerV1)
            #     Events = Controller.ControllerApi.GetControllerEventsJson()
            #     print("Controller.ONLINEControllerV1 =>",
            #           Controller.ONLINEControllerV1)
            #     if (Controller.ONLINEControllerV1 == ModeController.OFFLINE):
            #         if Events["messages"][0]["events"] != []:
            #             SendPost(urls='http://192.168.0.129:8000',
            #                      Events=Events)
            #             print("Send =>  ", Events)
            #     else:
            #         # Работа через двух факторный режим блокируем и потом открываем дверь
            #         if (Controller.ONLINEControllerV1 == ModeController.ONLINE):
            #             if Events["messages"][0]["events"] != []:
            #                 Check_access = {
            #                     "type": Events["type"],
            #                     "sn": Events["sn"],
            #                     "messages": [
            #                         {
            #                             "id": 123456789,
            #                             "operation": "check_access",
            #                             "card": Events["messages"][0]["events"][0]["card"],
            #                             "reader": Events["messages"][0]["events"][0]["direct"]
            #                         }
            #                     ]
            #                 }

            #                 print("Send =>  ", Check_access)
            #                 SendPost(urls='http://192.168.0.129:8000',
            #                          Events=Check_access)
        except queue.Empty:
            continue
    ############################################################################
    # print(datetime.now() - start_time)
    ####################################################################################


# def MainMiddlewareOld():
#     global Controller

#     # start_time = datetime.now()
#     ##########################################

#     while (True):
#         try:
#             ###########################################################
#             if (Controller.ActiveControllerV1 == ModeController.ACTIVE):
#                 Controller.ControllerApi.Change_Context_Controller(1)
#                 Controller.EventIndexInControllerV1 = Controller.ControllerApi.Do_Show_New_Events(
#                     Controller.EventIndexInControllerV1)
#                 Events = Controller.ControllerApi.GetControllerEventsJson()
#                 print("Controller.ONLINEControllerV1 =>",
#                       Controller.ONLINEControllerV1)
#                 if (Controller.ONLINEControllerV1 == ModeController.OFFLINE):
#                     if Events["messages"][0]["events"] != []:
#                         SendPost(urls='http://192.168.0.129:8000',
#                                  Events=Events)
#                         print("Send =>  ", Events)
#                 else:
#                     # Работа через двух факторный режим блокируем и потом открываем дверь
#                     if (Controller.ONLINEControllerV1 == ModeController.ONLINE):
#                         if Events["messages"][0]["events"] != []:
#                             Check_access = {
#                                 "type": Events["type"],
#                                 "sn": Events["sn"],
#                                 "messages": [
#                                     {
#                                         "id": 123456789,
#                                         "operation": "check_access",
#                                         "card": Events["messages"][0]["events"][0]["card"],
#                                         "reader": Events["messages"][0]["events"][0]["direct"]
#                                     }
#                                 ]
#                             }

#                             print("Send =>  ", Check_access)
#                             SendPost(urls='http://192.168.0.129:8000',
#                                      Events=Check_access)
#         except queue.Empty:
#             continue
#     ############################################################################
#     # print(datetime.now() - start_time)
#     ####################################################################################


def SetActive(ActiveController, OnlineController, body: any):
    ActiveController[0] = body["active"]
    OnlineController[0] = body["online"]
    response_body = {
        "id": 123456789,
        "success ": 1
    }
    return response_body


def SetMode(area, body: any):
    area[0] = body["mode"]
    response_body = {
        "id": 123456789,
        "success ": 1
    }
    return response_body


def RunResponse(sn: int, body: any):
    '''
        Запускаем обработчик для обработки и совершение действий с контролерами
        Принимаем json и на основе поля 'operation' совершаем какие либо действие
        над контролерами
    '''
    # ConverterIronLogic является глобальной переменой для класса используется для синхронизации данных между потоков
    global ConverterIronLogic
    print("\n\n\nsn =>", sn)
    print(body['operation'])
    ################################################################
    # Если серийник с таким то номером то совершаем некоторые действия
    for _index ,_Controller in enumerate(ConverterIronLogic._Controllers):
        # Если серийник не совпадает с адресом который был в запросе то пропускаем итерацию
        if (sn != _Controller.SerialNumber):
            continue
        # Активация контролера
        if (body['operation'] == "set_active"):
            argWrapper1 = [_Controller.Active]
            argWrapper2 = [_Controller.LogicMode]
            res = SetActive(ActiveController=argWrapper1,
                            OnlineController=argWrapper2, body=body)
            _Controller.Active = argWrapper1[0]
            _Controller.LogicMode = argWrapper2[0]
            return res
        # Установка режима контролера(перепроверить возможно что то сломано)
        if (body['operation'] == "set_mode"):
            argWrapper1 = [_Controller.LogicMode]
            return SetMode(argWrapper1, body)
        # Открытие двери
        if (body['operation'] == "open_door"):
            print(body['direction'])
            # Если контролер не выбран выбираем
            if (not _Controller.Selected):
                ConverterIronLogic.ControllerApi.Change_Context_Controller(
                    _Controller.AddressNumber)
                ConverterIronLogic.SelectedControllerForOperation(_index)
            ConverterIronLogic.ControllerApi.Open_Door(int(body['direction']))
            answer = {
                "id": body["id"],
                "success ": 1
            }
            return answer
        # Ответ на check_access
        if (body['operation'] == "check_access"):
            if (body['granted'] == 1):
                # Если контролер не выбран выбираем
                if (not _Controller.Selected):
                    ConverterIronLogic.ControllerApi.Change_Context_Controller(
                        _Controller.AddressNumber)
                    ConverterIronLogic.SelectedControllerForOperation(_index)
                ConverterIronLogic.ControllerApi.Open_Door(
                    int(_Controller.ReaderSide))
        # Добавление карточек
        if (body['operation'] == "add_cards"):
            print("Карточки которые будут добавлены в контролер => ",
                  body["cards"])
            if (not _Controller.Selected):
                ConverterIronLogic.ControllerApi.Change_Context_Controller(
                    _Controller.AddressNumber)
                ConverterIronLogic.SelectedControllerForOperation(_index)
            for cart in body["cards"]:
                ConverterIronLogic.ControllerApi.Add_Cart(cart["card"])
            answer = {
                "id": body["id"],
                "success ": len(body["cards"])
            }
            return answer


def RunServer():
    ################## Обработчик входящих подключений ##################################
    async def Mock(request):
        #########################################
        # Обработчик входящих подключений
        body = await request.json()

        print(body)
        print(body['messages'][0])

        #########################################
        # Обработка включение контролера от упр сервера
        response_body = RunResponse(body['sn'], body['messages'][0])
        #########################################
        return web.json_response(response_body)
    #####################################################################################
    # Инициализация контролеров
    InitMiddleware()
    # Обработчик действий с контролера

    def Run_Controller_Thread():
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
