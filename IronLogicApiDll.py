import ctypes
import json
import time


class bcolors:
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
    __lib_DllInitConverter = None
    ###########################################################

    ###########################################################
    # доступ др dll функции смены контекста контролера (переключение на другой контролер)
    __lib_Dll_Change_Context_Controller = None
    ###########################################################

    ###########################################################
    # доступ др dll функции Cделал хуйню (первичная инициализация позже переделаю мамой клянусь)
    __lib_Dll_Do_Ctr_Events_Menu = None
    ###########################################################

    ###########################################################
    # доступ др dll функции прочитать новые событие
    __lib_Dll_Do_Show_New_Events = None
    ###########################################################

    ###########################################################
    # доступ др dll функции обновление банка ключей
    __lib_Dll_Update_Bank_Key = None
    ###########################################################

    ###########################################################
    # доступ до dll функции для запроса последнего поднесённого ключа
    __lib_Last_Key_Get = None
    ###########################################################

    ###########################################################
    # доступ до dll функции для запроса последних событий
    __lib_Controller_Events_Json = None
    ###########################################################

    ###########################################################
    # доступ до dll функции для запроса всех событий
    __lib_All_Controller_Events_Json = None
    ###########################################################

    ###########################################################
    # доступ до dll функции Открыть текущую дверь
    __lib_Dll_Open_Door = None
    ###########################################################

    ###########################################################
    # доступ до dll функции добавить карточку в выбранный контролер(в конец)
    __lib_Dll_Add_Cart = None
    ###########################################################

    ###########################################################
    # доступ до dll функции добавить карточку в выбранный контролер(с учетом всех ключей удалённых)
    __lib_Dll_Add_Cart_Index = None
    ###########################################################

    ###########################################################
    # доступ до dll функции взять из выбранного контролера все ключи которые там есть
    __lib_Dll_Get_Bank_Key = None
    ###########################################################

    ###########################################################
    # доступ до dll функции удаляет карточку в выбранный контролер
    __lib_Dll_Delete_Cart = None
    ###########################################################

    ###########################################################
    # доступ до dll функции взять из выбранного контролера все ключи которые пометили как удалённые
    __lib_Dll_Get_Delete_Index_Key = None
    ###########################################################

####################################################################################################

    def __init__(self, patch_to_dll: str) -> bool:
        # Вызвали конструктор класса без корректных аргументов
        if (type(patch_to_dll) != str):
            return False
        # Загрузка Dll
        self.__lib = ctypes.CDLL(patch_to_dll)

        ###########################################################
        # Загрузка из DLL функции void DllInitConverter()
        self.__lib_DllInitConverter = self.__lib.DllInitConverter
        self.__lib_DllInitConverter.restype = ctypes.c_bool
        self.__lib_DllInitConverter.argtypes = []
        ###########################################################

        self.__lib_DllInitConverter()  # Загрузка dll

        ###########################################################
        # Загрузка из DLL функции char* DllStrAllControllerEventsJson()
        self.__lib_All_Controller_Events_Json = self.__lib.DllStrAllControllerEventsJson
        self.__lib_All_Controller_Events_Json.restype = ctypes.c_char_p
        self.__lib_All_Controller_Events_Json.argtypes = []
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции bool DllChangeContextController(int indexController)
        self.__lib_Dll_Change_Context_Controller = self.__lib.DllChangeContextController
        self.__lib_Dll_Change_Context_Controller.restype = ctypes.c_bool
        self.__lib_Dll_Change_Context_Controller.argtypes = [ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции int  DllDoCtrEventsMenu(int _CtrAddr, int LastEventIndexInController)
        self.__lib_Dll_Do_Ctr_Events_Menu = self.__lib.DllDoCtrEventsMenu
        self.__lib_Dll_Do_Ctr_Events_Menu.restype = ctypes.c_int
        self.__lib_Dll_Do_Ctr_Events_Menu.argtypes = [
            ctypes.c_int, ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции int DllDoShowNewEvents(int indexEventInController)
        self.__lib_Dll_Do_Show_New_Events = self.__lib.DllDoShowNewEvents
        self.__lib_Dll_Do_Show_New_Events.restype = ctypes.c_int
        self.__lib_Dll_Do_Show_New_Events.argtypes = [ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции void DllUpdateBankKey(int indexBank)
        self.__lib_Dll_Update_Bank_Key = self.__lib.DllUpdateBankKey
        self.__lib_Dll_Update_Bank_Key.restype = ctypes.c_void_p
        self.__lib_Dll_Update_Bank_Key.argtypes = [ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции const char* DllLastKeyGet()
        self.__lib_Last_Key_Get = self.__lib.DllLastKeyGet
        self.__lib_Last_Key_Get.restype = ctypes.c_char_p
        self.__lib_Last_Key_Get.argtypes = []
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции char* DllStrControllerEventsJson()
        self.__lib_Controller_Events_Json = self.__lib.DllStrControllerEventsJson
        self.__lib_Controller_Events_Json.restype = ctypes.c_char_p
        self.__lib_Controller_Events_Json.argtypes = []
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции void DllOpenDoor(int sideLock)
        self.__lib_Dll_Open_Door = self.__lib.DllOpenDoor
        self.__lib_Dll_Open_Door.restype = ctypes.c_void_p
        self.__lib_Dll_Open_Door.argtypes = [ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из Dll функции void DllAddCart(char* stringCart)
        self.__lib_Dll_Add_Cart = self.__lib.DllAddCart
        self.__lib_Dll_Add_Cart.restype = ctypes.c_void_p
        self.__lib_Dll_Add_Cart.argtypes = [ctypes.c_char_p]
        ###########################################################

        ###########################################################
        # Загрузка из Dll функции void DllAddCartWithIndex(char* stringCart,int* IndexArr,int Size)
        self.__lib_Dll_Add_Cart_Index = self.__lib.DllAddCartWithIndex
        self.__lib_Dll_Add_Cart_Index.restype = ctypes.c_void_p
        self.__lib_Dll_Add_Cart_Index.argtypes = [
            ctypes.c_char_p, ctypes.POINTER(ctypes.c_int), ctypes.c_int]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции const char* DllGetBankKey()
        self.__lib_Dll_Get_Bank_Key = self.__lib.DllGetBankKey
        self.__lib_Dll_Get_Bank_Key.restype = ctypes.c_char_p
        self.__lib_Dll_Get_Bank_Key.argtypes = []
        ###########################################################

        ###########################################################
        # Загрузка из Dll функции void DllDeleteCart
        self.__lib_Dll_Delete_Cart = self.__lib.DllDeleteCard
        self.__lib_Dll_Delete_Cart.restype = ctypes.POINTER(ctypes.c_int)
        self.__lib_Dll_Delete_Cart.argtypes = [ctypes.c_char_p]
        ###########################################################

        ###########################################################
        # Загрузка из DLL функции const char* DllGetDeleteIndexKey()
        self.__lib_Dll_Get_Delete_Index_Key = self.__lib.DllGetDeleteIndexKey
        self.__lib_Dll_Get_Delete_Index_Key.restype = ctypes.c_char_p
        self.__lib_Dll_Get_Delete_Index_Key.argtypes = []
        ###########################################################

#######################################################################################

    def Change_Context_Controller(self, indexController: int):
        '''
        Сменить активный контролер

        Args:
            indexController (INT): Индекс контролера для смены контекста

        Returns:
            INT: Код результата выполнения функции
        '''
        self.__lib_Dll_Change_Context_Controller(indexController)

    def Do_Show_New_Events(self, indexEventInController: int):
        '''
        Прочитать новые событие

        Args:
            indexEventInController (INT): Индекс с которого будет считаны события

        Returns:
            INT: Возвращает индекс последнего прочитанного событие в контролере
        '''
        return self.__lib_Dll_Do_Show_New_Events(indexEventInController)

    def Update_Bank_Key(self, indexBank: int):
        '''
        Обновить банк ключей

        Args:
            indexBank (INT): Индекс банка ключей

        Returns:
            void:
        '''
        self.__lib_Dll_Update_Bank_Key(indexBank)

    def Do_Ctr_Events_Menu(self, _CtrAddr: int, LastEventIndexInController: int):
        '''
        Cделал хуйню (первичная инициализация позже переделаю мамой клянусь)

        Args:
            _CtrAddr (INT): Адрес контролера
            LastEventIndexInController (INT): Индекс с которого будет считаны события

        Returns:
            INT: Возвращает индекс последнего прочитанного событие в контролере
        '''
        return self.__lib_Dll_Do_Ctr_Events_Menu(_CtrAddr, LastEventIndexInController)

    def Open_Door(self, sideLock: int):
        '''
        Открыть текущую дверь

        Args:
            sideLock (INT): Сторона замка

        Returns:
            void:
        '''
        self.__lib_Dll_Open_Door(sideLock)

    def Add_Cart(self, Cart: str):
        '''
        Добавить карточку в контролер который был выбран(в конец)

        Args:
            Cart (str): Номер замка в формате HEX (000000FFFFFF) 

        Returns:
            void:
        '''
        c_Cart = Cart.encode()
        self.__lib_Dll_Add_Cart(c_Cart)

    def Add_Cart_Index(self, Cart: str, Index: list):
        '''
        Добавить карточку в контролер который был выбран(по всему контролеру)

        Args:
            Cart (str): Номер замка в формате HEX (000000FFFFFF) 

        Returns:
            void:
        '''
        c_Cart = Cart.encode()
        array = (ctypes.c_int * len(Index))(*Index)
        self.__lib_Dll_Add_Cart_Index(c_Cart, array, len(Index))

    def Delete_Cart(self, Cart: str):
        '''
        Удалить карточку в контролер который был выбран

        Args:
            Cart (str): Номер замка в формате HEX (000000FFFFFF) 

        Returns:
            void:
        '''
        c_Cart = Cart.encode()
        indexClearCart = ctypes.POINTER(ctypes.c_int)
        indexClearCart = self.__lib_Dll_Delete_Cart(c_Cart)
        return indexClearCart

    def debug_print(self, data, f_colors=bcolors.OKBLUE, b_colors=bcolors.BOLD):
        if (self.__debug):
            if (data != "None"):
                print("\n\n\nDebug_Print ==>  " +
                      f_colors+data+b_colors+bcolors.ENDC+'\n')
                # time.sleep(10)

    def GetControllerEventsJson(self) -> json:
        data = self.__lib_Controller_Events_Json()
        if (data != None):
            jsonData = json.loads(data.decode('utf-8'))
            self.debug_print(str(jsonData))
            return jsonData
        else:
            return None

    def GetAllControllerEventsJson(self) -> json:
        data = self.__lib_All_Controller_Events_Json()
        if (data != None):
            jsonData = json.loads(data.decode('utf-8'))
            self.debug_print(str(jsonData))
            return jsonData
        else:
            return None

    def GetAllKeyInControllerJson(self) -> json:
        data = self.__lib_Dll_Get_Bank_Key()
        string_data: str = data.decode("utf-8")
        jsonData = json.loads(string_data)
        self.debug_print(jsonData)
        return jsonData

    def GetDeleteIndexKeyInControllerJson(self) -> json:
        data = self.__lib_Dll_Get_Delete_Index_Key()
        string_data: str = data.decode("utf-8")
        jsonData = json.loads(string_data)
        self.debug_print(jsonData)
        return jsonData

    def GetLastKey(self) -> json:
        data = self.__lib_Last_Key_Get()
        if (data != None):
            jsonData = json.loads(data.decode('utf-8'))
            self.debug_print(str(jsonData))
            return jsonData
        else:
            return None
