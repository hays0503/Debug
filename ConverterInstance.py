from IronLogicApiDll import IronLogicControllerApi
from ControllerInstance import ControllerInstance


class ConverterInstance:
    '''
        Класс в котором описана абстракция конвертера
    '''

    # Создание объекта для обращению к api
    controller_api: IronLogicControllerApi

    # Массив контролеров
    arr_controllers: ControllerInstance = []

    # Разрешить переключение между контролерами
    disable_change_controller = False

    # Запущенна задача в контролере
    run_task_in_controller = False

    def __init__(self, patch_to_dll: str, com_address: str):
        '''
            @arg
                patch_to_dll : str путь др dll
        '''
        self.controller_api = IronLogicControllerApi(patch_to_dll, com_address)

    # Устанавливает в флаг что над этим контролером
    # в данный момент ведётся работа а с других этот флаг снимается
    def selected_controller_for_operation(self, index: int):
        '''
            Выбрать контролер для операций
        '''
        for _index, controller in enumerate(self.arr_controllers):
            if _index == index:
                controller.Selected = True
            else:
                controller.Selected = False

    # Функция для добавления новых контролеров
    def add_new_controller(self,
                           address_in_converter: int,
                           serial_number: int,
                           name_controller: str,
                           banks: int):
        '''
            @arg
                address_in_converter: int,
                serial_number: int,
                name_controller: str,
                banks: int
        '''
        # Создаем объект контролера и наполняем его данными
        new_instance = ControllerInstance()
        new_instance.address_number = address_in_converter
        new_instance.serial_number = serial_number
        new_instance.name_controller = name_controller
        new_instance.banks = banks
        # Вносим его в список контролеров которые подключены в конвертер
        self.arr_controllers.append(new_instance)

    def run_response(self, serial_number: int, body: any):
        '''
            Запускаем обработчик для обработки и совершение действий с контролерами
            Принимаем json и на основе поля 'operation' совершаем какие либо действие
            над контролерами
        '''
        # ConverterIronLogic является глобальной
        # переменой для класса используется для синхронизации данных между потоков
        ################################################################
        # Если серийник с таким то номером то совершаем некоторые действия
        for controller in self.arr_controllers:
            # Если серийник не совпадает с адресом который был в запросе то пропускаем итерацию
            if serial_number != controller.serial_number:
                continue
            # Открытие двери
            if body['operation'] == "open_door":
                self.controller_api.open_door(int(body['direction']))
                answer = {
                    "id": body["id"],
                    "success ": 1
                }
                return answer
            # Ответ на check_access
            if body['operation'] == "check_access":
                print("body['granted'] ", body['granted'])
                if body['granted'] == 1:
                    self.controller_api.open_door(
                        int(controller.reader_side))
                    answer = {
                        "id": body["id"],
                        "success ": 1
                    }
                    return answer
            # Добавление карточек
            if body['operation'] == "add_cards":
                # Пробежать по всем переданным карточкам и произвести добавление
                for cart in body["cards"]:
                    # Если у нас не удалялись
                    # до этого карты то добавляем карты в конец
                    # Иначе сначала в свободные места
                    # потом в конец(экономия места используем весь банк ключей)
                    if not controller.key_index_in_controller:
                        self.controller_api.add_cart(cart["card"])
                    else:
                        self.controller_api.add_cart_index(
                            cart["card"], controller.key_index_in_controller)
                        controller.key_index_in_controller.pop()
                answer = {
                    "id": body["id"],
                    "success ": len(body["cards"])
                }
                return answer
            # Удаление всех карточек
            if body['operation'] == "clear_cards":
                self.controller_api.delete_all_cart()
                controller.key_index_in_controller.clear()
                answer = {
                    "id": body["id"],
                    "success ": 1
                }
                return answer
            # Удаление карточек
            if body['operation'] == "del_cards":
                # Пробежать по всем переданным карточкам и произвести из экзекуцию
                for cart in body["cards"]:
                    controller.raw_key_index_in_controller.append(
                        self.controller_api.delete_cart(cart["card"]))

                # Сбор данных о удалённых ключах
                for _index_in_controller in controller.raw_key_index_in_controller:
                    index = _index_in_controller.contents.value
                    # print("_index_in_controller.contents.value   ",
                    #       _index_in_controller.contents.value)
                    # print("controller.key_index_in_controller    ",
                    #       controller.key_index_in_controller)
                    if (index != -1):
                        controller.key_index_in_controller.append(int(index))

                controller.raw_key_index_in_controller.clear()

                answer = {
                    "id": body["id"],
                    "success ": len(body["cards"]),
                    "indexDeletedCarts": controller.key_index_in_controller,

                }
                return answer
            # Запрос на карточки которые находятся в контролере
            if body['operation'] == "read_cards":
                self.controller_api.update_bank_key(
                    controller.banks)
                controller.keys_in_controller = self.controller_api.get_all_key_in_controller_json()
                # print("\n\n\n+++++++++++++++++++++\n", serial_number)
                controller.message_queue_out.put(
                    controller.keys_in_controller)
                controller.message_queue_out.put(None)
                # print("controller.message_queue_out=> ",
                #       controller.message_queue_out)
                # print("controller.message_queue_out=> ",
                #       controller.message_queue_out.queue)
                return controller.keys_in_controller

        return None
