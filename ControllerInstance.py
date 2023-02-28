

class ControllerInstance:

    # Сторона с которой была приложена карточка
    # -1 означает что на данный момент карточки еще не было
    ReaderSide = -1

    # Последний раз какая карта была приложена
    LastCart = "null"

    # Адрес который присвоен контролеру в конвертере
    # -1 означает что на данный момент не присвоен адрес
    AddressNumber = -1

    # Серийный адрес контролера
    # -1 означает что на данный момент не присвоен серийный адрес
    SerialNumber = -1

    # Название (имя-модели) контролера
    # null означает что на данный момент не присвоен
    NameController = "null"

    # Версия программного обеспечения
    # -1 означает что на данный момент не присвоен
    VersionNumber = -1

    # Количество банков с ключами которые есть в контролере
    # -1 означает что на данный момент не присвоен
    Banks = -1

    # Количество ключей которые могут содержать в себе контролер
    # -1 означает что на данный момент не присвоен
    Keys = -1

    # Массив из ключей который есть в контролере
    # [] означает что на данный момент ключей нет или структура не была инициализированная
    KeysInController = []

    # Количество событий которые может в себе хранить контроллер
    # -1 означает что на данный момент не присвоен
    Events = -1

    # Указатель на последнее событие
    # -1 означает что на данный момент не присвоен
    EventsIterator = -1

    # Массив из событий который есть в контролере
    # [] означает что на данный момент событий нет или структура не была инициализированная
    EventsInController = []

    # Режим в котором сейчас работает контроллер
    # -1 означает что на данный момент не присвоен (не включён в обработку)
    # 0 Автономный режим
    # 1 Режим онлайн
    LogicMode = -1

    # Включен ли контролер
    # -1 означает что на данный момент не присвоен
    Active = -1

    def POWER_ON(self):
        '''
            Сообщение включение (web-json)
            Один из первичных этапов в рукопожатие контролер <--> сервер
        '''
        JsonObject = {
            "id": 1,
            "operation": "power_on",
            "fw": self.VersionNumber,
            "conn_fw": self.VersionNumber,
            "active": self.Active,
            "mode": self.LogicMode,
            # Так как всё равно обращаемся по серийнику то ip не задействуем
            "controller_ip": "0.0.0.0"
        }
        return self.Build_Message(JsonObject)

    def Build_Message(self, Messages: any):
        '''
            Построение типового (web-json)
        '''
        ObjectBuildMessage = {
            "type": self.NameController,
            "sn": self.SerialNumber,
            "messages": [Messages]
        }
        return ObjectBuildMessage
