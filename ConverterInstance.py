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
