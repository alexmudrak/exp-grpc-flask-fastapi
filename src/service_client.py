"""
Простая реализация клиента для получения данных от сервера
по протоколу gRPC
"""
import logging

import grpc
from proto_core.service_pb2_grpc import RouteGuideStub
from proto_core.service_pb2 import Feature, Point


def get_one_futers(stub: RouteGuideStub, point: Point):
    feature: Feature = stub.GetFeature(point)
    # Если возврат был не получен объект Point, значит ошибка
    # на сервере
    if not feature.location:
        logging.critical("Ошибка на сервере")
        return
    if feature.name:
        # Все хооршо, объект найден
        logging.info(
            f"Найдено мето {feature.name} "
            f"(x: {feature.location.latitude}, "
            f"y: {feature.location.longitude})"
        )
    else:
        # Объект не найден в БД сервера
        logging.info("Место не найдено!")


def get_future(stub: RouteGuideStub):
    """
    Попытка сделать 3 одиночных запроса по gRPC.
    2 запроса должны вернуть результат, а последний
    должен вернуть информацию о том, что объект не найден
    """
    get_one_futers(stub, Point(latitude=1, longitude=2))
    get_one_futers(stub, Point(latitude=3, longitude=4))
    get_one_futers(stub, Point(latitude=5, longitude=6))


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        # Заглушка для доступа к методам сервера
        stub = RouteGuideStub(channel)
        get_future(stub)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
