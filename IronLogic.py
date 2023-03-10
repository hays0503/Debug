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

# Корневые объекты


# Абстракция один конвертер множество контролеров
ConverterIronLogic = ConverterInstance('./ControllerIronLogic.dll')

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
        Controller.KeysInController = ConverterIronLogic.ControllerApi.GetAllKeyInControllerJson()[
            'messages'][0]["cards"]

        ################################################################
        # Собираем информацию по удалённым ключам в контролере
        JsonDllGetDeleteIndexKey = ConverterIronLogic.ControllerApi.GetDeleteIndexKeyInControllerJson()
        ArrCards = JsonDllGetDeleteIndexKey["messages"][0]["cards"]
        ArrCardsIndex = []
        for Index in ArrCards:
            ArrCardsIndex.append(Index["pos"])
        Controller.KeyIndexInController = ArrCardsIndex
        ################################################################

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
            for _index, _Controller in enumerate(ConverterIronLogic._Controllers):

                if (_Controller.Active == ModeController.ACTIVE):

                    # # Не запущена блокирующая операция с контролером
                    # if (not ConverterIronLogic.DisableChangeController):
                    #     print("\n\nSerialNumber ", _Controller.SerialNumber,
                    #           not ConverterIronLogic.DisableChangeController)
                    # Если контролер не выбран выбираем
                    if (not _Controller.Selected):
                        # ConverterIronLogic.RunTaskInController = True
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

                    # ConverterIronLogic.RunTaskInController = False
        except queue.Empty:
            continue


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
    ################################################################
    # Если серийник с таким то номером то совершаем некоторые действия
    for _index, _Controller in enumerate(ConverterIronLogic._Controllers):
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
            answer = SetMode(argWrapper1, body)
            _Controller.LogicMode = argWrapper1[0]
            return answer
        # Открытие двери
        if (body['operation'] == "open_door"):
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
                answer = {
                    "id": body["id"],
                    "success ": 1
                }
                return answer
        # Добавление карточек
        if (body['operation'] == "add_cards"):
            
            # Проверить что за контролер сейчас выбран
            if (not _Controller.Selected):
                ConverterIronLogic.ControllerApi.Change_Context_Controller(
                    _Controller.AddressNumber)
                ConverterIronLogic.SelectedControllerForOperation(_index)
            # Пробежать по всем переданным карточкам и произвести добавление
            for cart in body["cards"]:
                # Если у нас не удалялись до этого карты то добавляем карты в конец
                # Иначе сначала в свободные места потом в конец(экономия места используем весь банк ключей)
                if (not _Controller.KeyIndexInController):
                    ConverterIronLogic.ControllerApi.Add_Cart(cart["card"])
                else:
                    ConverterIronLogic.ControllerApi.Add_Cart_Index(
                        cart["card"], _Controller.KeyIndexInController)
                    _Controller.KeyIndexInController.pop()
            answer = {
                "id": body["id"],
                "success ": len(body["cards"])
            }
            return answer
        # Удаление карточек
        if (body['operation'] == "del_cards"):

            # Проверить что за контролер сейчас выбран
            if (not _Controller.Selected):
                ConverterIronLogic.ControllerApi.Change_Context_Controller(
                    _Controller.AddressNumber)
                ConverterIronLogic.SelectedControllerForOperation(_index)
            # Пробежать по всем переданным карточкам и произвести из экзекуцию
            for cart in body["cards"]:
                _Controller._rawKeyIndexInController.append(
                    ConverterIronLogic.ControllerApi.Delete_Cart(cart["card"]))

            # Сбор данных о удалённых ключах
            for _IndexIn_Controller in _Controller._rawKeyIndexInController:
                index = _IndexIn_Controller.contents.value
                if (index != -1):
                    _Controller.KeyIndexInController.append(int(index))

            _Controller._rawKeyIndexInController.clear()
            _Controller.KeyIndexInController.sort()
            deletedCarts = []
            for _CartsIndex in _Controller.KeyIndexInController:
                deletedCarts.append(
                    _Controller.KeysInController[_CartsIndex])

            answer = {
                "id": body["id"],
                "success ": len(body["cards"]),
                "deletedCarts": deletedCarts,

            }
            return answer
        # Запрос на карточки которые находятся в контролере
        if (body['operation'] == "read_cards"):
            if (not _Controller.Selected):
                ConverterIronLogic.ControllerApi.Change_Context_Controller(
                    _Controller.AddressNumber)
            ConverterIronLogic.SelectedControllerForOperation(_index)
            ConverterIronLogic.ControllerApi.Update_Bank_Key(
                _Controller.Banks)
            answer = ConverterIronLogic.ControllerApi.GetAllKeyInControllerJson()
            _Controller.KeysInController = answer
            return answer


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
        response_body = RunResponse(body['sn'], body['messages'][0])
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
