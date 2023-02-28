import os
import ctypes
import time
import requests
import aiohttp
import asyncio

lib = ctypes.CDLL('./ControllerIronLogic.dll')
lib_run = lib.run
lib_run.restype = ctypes.c_void_p
lib_run.argtypes = []

lib_Last_Key_Get = lib.LastKeyGet
lib_Last_Key_Get.restype = ctypes.c_char_p
lib_Last_Key_Get.argtypes = []

lib_Controller_Events_Json = lib.strControllerEventsJson
lib_Controller_Events_Json.restype = ctypes.c_char_p
lib_Controller_Events_Json.argtypes = []


async def get_http_response(urls, Events) -> dict:
    tasks = []
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


def main():
    while True:
        Events = lib_Controller_Events_Json()
        if Events != None:  # Если не пустое событие
            data = asyncio.run(get_http_response(
                urls='http://192.168.0.129:8000', Events=Events))
            print("\nget_http_response => ", data)
            # break


if __name__ == '__main__':
    lib_run()
    main()
