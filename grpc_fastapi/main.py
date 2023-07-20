import asyncio
import json
import logging
import typing
from uuid import uuid4

from fastapi import FastAPI
from grpclib.client import Channel
from grpclib.server import Server
from grpclib.utils import graceful_exit
from starlette.responses import Response

from grpc_fastapi.db import MOCK_DB
from grpc_fastapi.service_grpc import FastApiGrpcBase as BASE_SERVICE
from grpc_fastapi.service_grpc import FastApiGrpcStub as BASE_STUB
from grpc_fastapi.service_pb2 import EntityRequest, EntityResponse

GRPC_HOST = "127.0.0.1"
GRPC_PORT = 50051
app = FastAPI()
grpc_task = None


# Settings for logger
logger = logging.getLogger("fastapi")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(log_format)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")


@app.on_event("startup")
async def start_event():
    logger.info("Start gRPC Server")
    await start_grpc_server()


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Stop gRPC server")
    grpc_task.cancel()


class Client:
    @staticmethod
    async def GetRecord(id: str):
        async with Channel(GRPC_HOST, GRPC_PORT) as channel:
            sender = BASE_STUB(channel)
            result = await sender.GetRecord(EntityRequest(id=id))
            return result


class Service(BASE_SERVICE):
    async def GetRecord(self, stream):
        entity_id = None
        entity_name = ""
        entity_description = ""
        request = await stream.recv_message()
        if request:
            entity_id = request.id
            for entity in MOCK_DB:
                if str(entity.get("id")) == request.id:
                    entity_name = entity.get("name")
                    entity_description = entity.get("description")
            response = EntityResponse(
                id=entity_id,
                name=entity_name,
                description=entity_description,
            )
            logger.debug(f"Get request for id: `{response.id}`")
            await stream.send_message(response)


async def start_grpc_server():
    global grpc_task
    grpc_task = asyncio.create_task(
        grpc_server(host=GRPC_HOST, port=GRPC_PORT)
    )


async def grpc_server(*, host: str = "127.0.0.1", port: int = 50051):
    server = Server([Service()])
    with graceful_exit([server]):
        await server.start(host, port)
        logger.debug(f"Serving on {host}:{port}")
        await server.wait_closed()


@app.post("/{name}", response_class=PrettyJSONResponse)
async def save_to_db(name: str, description: str | None = None):
    MOCK_DB.append(
        {
            "id": uuid4(),
            "name": name,
            "description": description,
        }
    )
    return {"DB": MOCK_DB}


@app.get("/{record_id}", response_class=PrettyJSONResponse)
async def get_result(record_id: str):
    result = await Client.GetRecord(record_id)
    model = {
        "id": result.id,
        "name": result.name,
        "description": result.description,
    }
    return {"RESULT": model}
    # return {"RESULT": 1}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, workers=4)
