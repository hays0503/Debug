# pylint: disable=no-else-return
import ctypes
import json


class HexColors:
    '''
        Цвета
    '''
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class IronLogicControllerApi:
    ###########################################################
    # доступ до Dll
    __lib = None
    ###########################################################

    ###########################################################
    # Включен ли режим дебаг информации
    __debug = False
    ###########################################################

    ###########################################################
    # доступ до dll функции инициализации библиотеки
    __lib_dll_init_converter = None
    ###########################################################

    ###########################################################
    # доступ др dll функции смены контекста контролера (переключение на другой контролер)
    __lib_dll_change_context_controller = None
    ###########################################################

    ###########################################################
    # доступ др dll функции Cделал хуйню (первичная инициализация позже переделаю мамой клянусь)
    __lib_dll_do_ctr_events_menu = None
    ###########################################################

    ###########################################################
    # доступ др dll функции прочитать новые событие
    __lib_dll_do_show_new_events = None
    ###########################################################

    ###########################################################
    # доступ др dll функции обновление банка ключей
    __lib_dll_update_bank_key = None
    ###########################################################

    ###########################################################
    # доступ до dll функции для запроса последнего поднесённого ключа
    __lib_last_key_get = None
    ###########################################################

    ###########################################################
    # доступ до dll функции для запроса последних событий
    __lib_controller_events_json = None
    ###########################################################

    ###########################################################
    # доступ до dll функции для запроса всех событий
    __lib_all_controller_events_json = None
    ###########################################################

    ###########################################################
    # доступ до dll функции Открыть текущую дверь
    __lib_dll_open_door = None
    ###########################################################

    ###########################################################
    # доступ до dll функции добавить карточку в выбранный контролер(в конец)
    __lib_dll_add_cart = None
    ###########################################################

    ###########################################################
    # доступ до dll функции добавить карточку в выбранный контролер(с учетом всех ключей удалённых)
    __lib_dll_add_cart_index = None
    ###########################################################

    ###########################################################
    # доступ до dll функции взять из выбранного контролера все ключи которые там есть
    __lib_dll_get_bank_key = None
    ###########################################################

    ###########################################################
    # доступ до dll функции удаляет карточку в выбранный контролер
    __lib_dll_delete_cart = None
    ###########################################################

    ###########################################################
    # доступ до dll функции удаляет карточку в выбранный контролер
    __lib_dll_all_delete_cart = None
    ###########################################################

    ###########################################################
    # доступ до dll функции взять из выбранного контролера все ключи которые пометили как удалённые
    __lib_dll_get_delete_index_key = None
    ###########################################################

####################################################################################################

    def __init__(self, patch_to_dll: str, com_address: str) -> bool:
        # Вызвали конструктор класса без корректных аргументов
        if not isinstance(patch_to_dll, str):
            raise ValueError("Путь до dll не найден")
        # Загрузка Dll
        self.__lib = ctypes.WinDLL(patch_to_dll)

        ###########################################################
        # Загрузка из DLL функции void DllInitConverter()
        self.__lib_dll_init_converter = self.__lib.DllInitConverter
        self.__lib_dll_init_converter.restype = ctypes.c_bool
        self.__lib_dll_init_converter.argtypes = [ctypes.c_char_p]
        ###########################################################
        dirt_com_address = com_address.encode()
        self.__lib_dll_init_converter(dirt_com_address)  # Загрузка dll

        ###########################################################
        # Загрузка из DLL функции char* DllStrAllControllerEventsJson()
        self.__lib_all_controller_events_json = self.__lib.DllStrAllControllerEventsJson
        self.__lib_all_controller_events_json.restype = ctypes.c_char_p
        self.__lib_all_controller_events_json.argtypes = []
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции bool DllChangeContextController(int indexController)
        self.__lib_dll_change_context_controller = self.__lib.DllChangeContextController
        self.__lib_dll_change_context_controller.restype = ctypes.c_bool
        self.__lib_dll_change_context_controller.argtypes = [ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции
        # int  DllDoCtrEventsMenu(int _CtrAddr, int LastEventIndexInController)
        self.__lib_dll_do_ctr_events_menu = self.__lib.DllDoCtrEventsMenu
        self.__lib_dll_do_ctr_events_menu.restype = ctypes.c_int
        self.__lib_dll_do_ctr_events_menu.argtypes = [
            ctypes.c_int, ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции int DllDoShowNewEvents(int indexEventInController)
        self.__lib_dll_do_show_new_events = self.__lib.DllDoShowNewEvents
        self.__lib_dll_do_show_new_events.restype = ctypes.c_int
        self.__lib_dll_do_show_new_events.argtypes = [ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции void DllUpdateBankKey(int indexBank)
        self.__lib_dll_update_bank_key = self.__lib.DllUpdateBankKey
        self.__lib_dll_update_bank_key.restype = ctypes.c_void_p
        self.__lib_dll_update_bank_key.argtypes = [ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции const char* DllLastKeyGet()
        self.__lib_last_key_get = self.__lib.DllLastKeyGet
        self.__lib_last_key_get.restype = ctypes.c_char_p
        self.__lib_last_key_get.argtypes = []
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции char* DllStrControllerEventsJson()
        self.__lib_controller_events_json = self.__lib.DllStrControllerEventsJson
        self.__lib_controller_events_json.restype = ctypes.c_char_p
        self.__lib_controller_events_json.argtypes = []
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции void DllOpenDoor(int sideLock)
        self.__lib_dll_open_door = self.__lib.DllOpenDoor
        self.__lib_dll_open_door.restype = ctypes.c_void_p
        self.__lib_dll_open_door.argtypes = [ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из Dll функции void DllAddCart(char* stringCart)
        self.__lib_dll_add_cart = self.__lib.DllAddCart
        self.__lib_dll_add_cart.restype = ctypes.c_void_p
        self.__lib_dll_add_cart.argtypes = [ctypes.c_char_p]
        ###########################################################

        ###########################################################
        # Загрузка из Dll функции void DllAddCartWithIndex(char* stringCart,int* IndexArr,int Size)
        self.__lib_dll_add_cart_index = self.__lib.DllAddCartWithIndex
        self.__lib_dll_add_cart_index.restype = ctypes.c_void_p
        self.__lib_dll_add_cart_index.argtypes = [
            ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции const char* DllGetBankKey()
        self.__lib_dll_get_bank_key = self.__lib.DllGetBankKey
        self.__lib_dll_get_bank_key.restype = ctypes.c_char_p
        self.__lib_dll_get_bank_key.argtypes = []
        ###########################################################

        ###########################################################
        # Загрузка из Dll функции void DllDeleteCart
        self.__lib_dll_delete_cart = self.__lib.DllDeleteCard
        self.__lib_dll_delete_cart.restype = ctypes.POINTER(ctypes.c_int)
        self.__lib_dll_delete_cart.argtypes = [ctypes.c_char_p]
        ###########################################################

        ###########################################################
        # Загрузка из Dll функции void DllClearBank
        self.__lib_dll_all_delete_cart = self.__lib.DllClearBank
        self.__lib_dll_all_delete_cart.restype = ctypes.c_void_p
        self.__lib_dll_all_delete_cart.argtypes = []
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции const char* DllGetDeleteIndexKey()
        self.__lib_dll_get_delete_index_key = self.__lib.DllGetDeleteIndexKey
        self.__lib_dll_get_delete_index_key.restype = ctypes.c_char_p
        self.__lib_dll_get_delete_index_key.argtypes = []
        ###########################################################

#######################################################################################

    def change_context_controller(self, index_controller: int):
        '''
        Сменить активный контролер

        Args:
            indexController (INT): Индекс контролера для смены контекста

        Returns:
            INT: Код результата выполнения функции
        '''
        self.__lib_dll_change_context_controller(index_controller)

    def do_show_new_events(self, index_event_in_controller: int):
        '''
        Прочитать новые событие

        Args:
            indexEventInController (INT): Индекс с которого будет считаны события

        Returns:
            INT: Возвращает индекс последнего прочитанного событие в контролере
        '''
        return self.__lib_dll_do_show_new_events(index_event_in_controller)

    def update_bank_key(self, index_bank: int):
        '''
        Обновить банк ключей

        Args:
            indexBank (INT): Индекс банка ключей

        Returns:
            void:
        '''
        self.__lib_dll_update_bank_key(index_bank)

    def do_ctr_events_menu(self, _ctr_addr: int, last_event_index_in_controller: int):
        '''
        Cделал хуйню (первичная инициализация позже переделаю мамой клянусь)

        Args:
            _CtrAddr (INT): Адрес контролера
            LastEventIndexInController (INT): Индекс с которого будет считаны события

        Returns:
            INT: Возвращает индекс последнего прочитанного событие в контролере
        '''
        return self.__lib_dll_do_ctr_events_menu(_ctr_addr, last_event_index_in_controller)

    def open_door(self, side_lock: int):
        '''
        Открыть текущую дверь

        Args:
            sideLock (INT): Сторона замка

        Returns:
            void:
        '''
        self.__lib_dll_open_door(side_lock)

    def add_cart(self, cart: str):
        '''
        Добавить карточку в контролер который был выбран(в конец)

        Args:
            Cart (str): Номер замка в формате HEX (000000FFFFFF) 

        Returns:
            void:
        '''
        dirt_string_cart = cart.encode()
        self.__lib_dll_add_cart(dirt_string_cart)

    def delete_all_cart(self):
        '''
        Удалить все карточки в контролер который были

        Returns:
            void:
        '''
        self.__lib_dll_all_delete_cart()

    def add_cart_index(self, cart: str, index: list):
        '''
        Добавить карточку в контролер который был выбран(по всему контролеру)

        Args:
            Cart (str): Номер замка в формате HEX (000000FFFFFF) 

        Returns:
            void:
        '''
        dirt_string_cart = cart.encode()
        array = (ctypes.c_int * len(index))(*index)
        self.__lib_dll_add_cart_index(dirt_string_cart, array, len(index))

    def delete_cart(self, cart: str):
        '''
        Удалить карточку в контролер который был выбран

        Args:
            Cart (str): Номер замка в формате HEX (000000FFFFFF) 

        Returns:
            void:
        '''
        dirt_string_cart = cart.encode()
        index_clear_cart = ctypes.POINTER(ctypes.c_int)
        index_clear_cart = self.__lib_dll_delete_cart(dirt_string_cart)
        return index_clear_cart

    def debug_print(self, data, f_colors=HexColors.OKBLUE, b_colors=HexColors.BOLD):
        '''
        Вывод информации если включена отладка

        Args:
            data (str): данные для вывода
            f_colors
            b_colors

        Returns:
            void:
        '''
        if self.__debug:
            if data != "None":
                print("\n\n\nDebug_Print ==>  " +
                      f_colors+data+b_colors+b_colors.ENDC+'\n')
                # time.sleep(10)

    def get_controller_events_json(self) -> json:
        '''
            Взять события из контролера
        '''
        data = self.__lib_controller_events_json()
        if data is not None:
            json_data = json.loads(data.decode('utf-8'))
            self.debug_print(str(json_data))
            return json_data
        else:
            return None

    def get_all_controller_events_json(self) -> json:
        '''
            Взять все события из контролера
        '''
        data = self.__lib_all_controller_events_json()
        if data is not None:
            json_data = json.loads(data.decode('utf-8'))
            self.debug_print(str(json_data))
            return json_data
        else:
            return None

    def get_all_key_in_controller_json(self) -> json:
        '''
            Взять все ключи из контролера
        '''
        data = self.__lib_dll_get_bank_key()
        string_data: str = data.decode("utf-8")
        json_data = json.loads(string_data)
        self.debug_print(json_data)
        return json_data

    def get_delete_index_key_in_controller_json(self) -> json:
        '''
            Взять все индексы ключей из контролера которые были удаленны
        '''
        data = self.__lib_dll_get_delete_index_key()
        string_data: str = data.decode("utf-8")
        json_data = json.loads(string_data)
        self.debug_print(json_data)
        return json_data

    def get_last_key(self) -> json:
        '''
            Взять последний ключ поднесённый к контролеру
        '''
        data = self.__lib_last_key_get()
        if data is not None:
            json_data = json.loads(data.decode('utf-8'))
            self.debug_print(str(json_data))
            return json_data
        else:
            return None
