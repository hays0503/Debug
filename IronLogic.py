
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
ConverterIronLogic = ConverterInstance

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
            session.post(url=urls, data=Events))  # Создай
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

    Controller.ControllerApi = IronLogicControllerApi(
        './ControllerIronLogic.dll')
    ################################################################
    # Подготовка первого контролера
    ################################################################
    Controller.EventIndexInControllerV1 = Controller.ControllerApi.Do_Ctr_Events_Menu(
        1, -1)
    Controller.ControllerApi.Update_Bank_Key(0)
    SendPost(urls='http://192.168.0.129:8000',
             Events=Build_Message(type="Z5R Net 8000", sn=4232, Messages=POWER_ON()))
    ################################################################
    # Подготовка второго контролера
    ################################################################
    Controller.EventIndexInControllerV2 = Controller.ControllerApi.Do_Ctr_Events_Menu(
        2, -1)
    Controller.ControllerApi.Update_Bank_Key(0)
    SendPost(urls='http://192.168.0.129:8000',
             Events=Build_Message(type="Z5R Net 8000", sn=4225, Messages=POWER_ON()))
    ################################################################

##########################################
# Функция для отправки сообщений в очередь


def send_message(message):
    message_queue.put(message)
##########################################


def MainMiddleware():
    global Controller

    # start_time = datetime.now()
    ##########################################

    while (True):
        try:
            ###########################################################
            if (Controller.ActiveControllerV1 == ModeController.ACTIVE):
                Controller.ControllerApi.Change_Context_Controller(1)
                Controller.EventIndexInControllerV1 = Controller.ControllerApi.Do_Show_New_Events(
                    Controller.EventIndexInControllerV1)
                Events = Controller.ControllerApi.GetControllerEventsJson()
                print("Controller.ONLINEControllerV1 =>",
                      Controller.ONLINEControllerV1)
                if (Controller.ONLINEControllerV1 == ModeController.OFFLINE):
                    if Events["messages"][0]["events"] != []:
                        SendPost(urls='http://192.168.0.129:8000',
                                 Events=Events)
                        print("Send =>  ", Events)
                else:
                    # Работа через двух факторный режим блокируем и потом открываем дверь
                    if (Controller.ONLINEControllerV1 == ModeController.ONLINE):
                        if Events["messages"][0]["events"] != []:
                            Check_access = {
                                "type": Events["type"],
                                "sn": Events["sn"],
                                "messages": [
                                    {
                                        "id": 123456789,
                                        "operation": "check_access",
                                        "card": Events["messages"][0]["events"][0]["card"],
                                        "reader": Events["messages"][0]["events"][0]["direct"]
                                    }
                                ]
                            }

                            print("Send =>  ", Check_access)
                            SendPost(urls='http://192.168.0.129:8000',
                                     Events=Check_access)
        except queue.Empty:
            continue
    ############################################################################
    # print(datetime.now() - start_time)
    ####################################################################################


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
    # Controller является глобальной переменой для класса используется для синхронизации данных между потоков
    global Controller
    print("sn =>", sn)
    print(body['operation'])
    ################################################################
    # Если серийник с таким то номером то совершаем некоторые действия
    if (sn == 4232):
        # Активирует / деактивирует работу контроллера с сервером
        if (body['operation'] == "set_active"):
            argWrapper1 = [Controller.ActiveControllerV1]
            argWrapper2 = [Controller.ONLINEControllerV1]
            res = SetActive(ActiveController=argWrapper1,
                            OnlineController=argWrapper2, body=body)
            Controller.ActiveControllerV1 = argWrapper1[0]
            Controller.ONLINEControllerV1 = argWrapper2[0]
            return res
        # Установка режима
        if (body['operation'] == "set_mode"):
            return SetMode(Controller.ModeControllerV2, body)
        # Открытие двери
        if (body['operation'] == "open_door"):
            print(body['direction'])
            Controller.ControllerApi.Change_Context_Controller(1)
            Controller.ControllerApi.Open_Door(int(body['direction']))
            answer = {
                "id": body["id"],
                "success ": 1
            }
            return answer
        # Ответ на check_access
        if (body['operation'] == "check_access"):
            if (body['granted'] == 1):
                Controller.ControllerApi.Change_Context_Controller(1)
                Controller.ControllerApi.Open_Door(int(1))
        # Добавление карточек
        if (body['operation'] == "add_cards"):
            print("Карточки которые будут добавлены в контролер => ",
                  body["cards"])
            Controller.ControllerApi.Change_Context_Controller(1)
            for cart in body["cards"]:
                Controller.ControllerApi.Add_Cart(cart["card"])
            answer = {
                "id": body["id"],
                "success ": len(body["cards"])
            }
            return answer
###############################################################
    # Если серийник с таким то номером то совершаем некоторые действия
    if (sn == 4225):
        # Активирует / деактивирует работу контроллера с сервером
        if (body['operation'] == "set_active"):
            argWrapper1 = [Controller.ActiveControllerV2]
            argWrapper2 = [Controller.ONLINEControllerV2]
            res = SetActive(ActiveController=argWrapper1,
                            OnlineController=argWrapper2, body=body)
            Controller.ActiveControllerV2 = argWrapper1[0]
            Controller.ONLINEControllerV2 = argWrapper2[0]
            return res
        # Установка режима
        if (body['operation'] == "set_mode"):
            return SetMode(Controller.ModeControllerV2, body)
        if (body['operation'] == "open_door"):
            Controller.ControllerApi.Change_Context_Controller(2)
            Controller.ControllerApi.Open_Door(int(body['direction']))


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
