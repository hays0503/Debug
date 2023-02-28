import ControllerInstance


class ConverterInstance:

    # Массив контролеров
    _Controllers: ControllerInstance = []

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
