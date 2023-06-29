"""
Простая имплементация сервера для работы по gRPC
"""
from concurrent import futures
import logging
from typing import Optional

import grpc
from proto_core.service_pb2_grpc import RouteGuideServicer as BASE_SERVICER
from proto_core.service_pb2_grpc import add_RouteGuideServicer_to_server
from proto_core.service_pb2 import Feature, Point

MOCK_DB_DATA = [
    Feature(
        name="Test 1",
        location=Point(
            latitude=1,
            longitude=2,
        )
    ),
    Feature(
        name="Test 2",
        location=Point(
            latitude=3,
            longitude=4,
        )
    ),
]

def mock_query_db(query) -> Optional[Feature]:
    """
    Имитация работы БД -> итерация по всем элементам и сравнение с запросом
    """
    for feature in MOCK_DB_DATA:
        if feature.location == query:
            return feature
    return None

"""
Класс который должен имплементировать все методы, которые описанные в
`service.proto`
"""
class RouteGuideServicer(BASE_SERVICER):
    def GetFeature(self, request, context) -> Feature:
        result = mock_query_db(request)
        if result is None:
            logging.info(f"Fail - Не найдена запись {request}")
            return Feature(name="", location=request)
        else:
            logging.info(f"ОК - Найдена запись {request}")
            return result

def server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_RouteGuideServicer_to_server(
        RouteGuideServicer(),
        server,
    )
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server()

