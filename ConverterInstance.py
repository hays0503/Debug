from IronLogicApiDll import IronLogicControllerApi
from ControllerInstance import ControllerInstance


class ConverterInstance:

    # Создание объекта для обращению к api
    ControllerApi: IronLogicControllerApi

    # Массив контролеров
    _Controllers: ControllerInstance = []

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
