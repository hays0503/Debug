from IronLogicApiDll import IronLogicControllerApi
from ControllerInstance import ControllerInstance


class ConverterInstance:

    # Создание объекта для обращению к api
    ControllerApi: IronLogicControllerApi

    # Массив контролеров
    _Controllers: ControllerInstance = []

    # Разрешить переключение между контролерами
    DisableChangeController = False

    # Запущенна задача в контролере
    RunTaskInController = False

    def __init__(self, patch_to_dll: str):
        '''
            @arg
                patch_to_dll : str путь др dll
        '''
        self.ControllerApi = IronLogicControllerApi(patch_to_dll)

    # Устанавливает в флаг что над этим контролером
    # в данный момент ведётся работа а с других этот флаг снимается
    def SelectedControllerForOperation(self, index: int):
        for _index, Controller in enumerate(self._Controllers):
            if (_index == index):
                Controller.Selected = True
            else:
                Controller.Selected = False

    # Функция для добавления новых контролеров
    def AddNewController(self,
                         addressInConverter: int,
                         SerialNumber: int,
                         NameController: str,
                         Banks: int):
        # Создаем объект контролера и наполняем его данными
        newInstance = ControllerInstance()
        newInstance.AddressNumber = addressInConverter
        newInstance.SerialNumber = SerialNumber
        newInstance.NameController = NameController
        newInstance.Banks = Banks
        # Вносим его в список контролеров которые подключены в конвертер
        self._Controllers.append(newInstance)

    # def SetMode(area, body: any):
    #     area[0] = body["mode"]
    #     response_body = {
    #         "id": 123456789,
    #         "success ": 1
    #     }
    #     return response_body

    def RunResponse(self, sn: int, body: any):
        '''
            Запускаем обработчик для обработки и совершение действий с контролерами
            Принимаем json и на основе поля 'operation' совершаем какие либо действие
            над контролерами
        '''
        # ConverterIronLogic является глобальной переменой для класса используется для синхронизации данных между потоков
        ################################################################
        # Если серийник с таким то номером то совершаем некоторые действия
        for _index, _Controller in enumerate(self._Controllers):
            # Если серийник не совпадает с адресом который был в запросе то пропускаем итерацию
            if (sn != _Controller.SerialNumber):
                continue
            # Открытие двери
            if (body['operation'] == "open_door"):
                self.ControllerApi.Open_Door(int(body['direction']))
                answer = {
                    "id": body["id"],
                    "success ": 1
                }
                return answer
            # Ответ на check_access
            if (body['operation'] == "check_access"):
                if (body['granted'] == 1):
                    self.ControllerApi.Open_Door(
                        int(_Controller.ReaderSide))
                    answer = {
                        "id": body["id"],
                        "success ": 1
                    }
                    return answer
            # Добавление карточек
            if (body['operation'] == "add_cards"):
                # Пробежать по всем переданным карточкам и произвести добавление
                for cart in body["cards"]:
                    # Если у нас не удалялись до этого карты то добавляем карты в конец
                    # Иначе сначала в свободные места потом в конец(экономия места используем весь банк ключей)
                    if (not _Controller.KeyIndexInController):
                        self.ControllerApi.Add_Cart(cart["card"])
                    else:
                        self.ControllerApi.Add_Cart_Index(
                            cart["card"], _Controller.KeyIndexInController)
                        _Controller.KeyIndexInController.pop()
                answer = {
                    "id": body["id"],
                    "success ": len(body["cards"])
                }
                return answer

            # Удаление карточек
            if (body['operation'] == "del_cards"):
                # Пробежать по всем переданным карточкам и произвести из экзекуцию
                for cart in body["cards"]:
                    _Controller._rawKeyIndexInController.append(
                        self.ControllerApi.Delete_Cart(cart["card"]))

                # Сбор данных о удалённых ключах
                for _IndexIn_Controller in _Controller._rawKeyIndexInController:
                    index = _IndexIn_Controller.contents.value
                    if (index != -1):
                        _Controller.KeyIndexInController.append(int(index))

                _Controller._rawKeyIndexInController.clear()

                answer = {
                    "id": body["id"],
                    "success ": len(body["cards"]),
                    "indexDeletedCarts": _Controller.KeyIndexInController,

                }
                return answer
            # Запрос на карточки которые находятся в контролере
            if (body['operation'] == "read_cards"):
                self.ControllerApi.Update_Bank_Key(
                    _Controller.Banks)
                answer = self.ControllerApi.GetAllKeyInControllerJson()
                print("\n\n\n+++++++++++++++++++++\n", sn)
                print(answer)
                # if (not len(answer['cards']) == 0):
                _Controller.KeysInController = answer
                return answer
