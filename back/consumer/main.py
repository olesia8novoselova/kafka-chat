from fastapi import FastAPI, Request
from prometheus_client import start_http_server, Gauge
from fastapi.middleware.cors import CORSMiddleware
from custom_websockets.endpoints.send_client_message import router as client_router
from custom_websockets.endpoints.subscribe import router as subscribe_router 
from custom_websockets.endpoints.send_client_message import initialize_state as client_init_state
from custom_websockets.endpoints.subscribe import initialize_state as subscribe_init_state
import asyncio
from contextlib import asynccontextmanager
from config.logger_config import logger

start_http_server(8004)

APP_INFO = Gauge(
    'app_info', 
    'Application metadata',
    ['version', 'service']
).labels(version='1.0', service='consumer')

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI application startup event triggered.")
    logger.info("Creating temporary state for FastAPI application.")

    client_init_state(app.state)
    subscribe_init_state(app.state)

    app.state.consumers = {}

    try:
        yield
    except asyncio.CancelledError:
        logger.warning("Application shutdown interrupted by CancelledError.")
    finally:
        logger.info("FastAPI application shutdown event triggered.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(client_router)
app.include_router(subscribe_router)

@app.get("/health")
async def health_check():
    return {"status": "Consumer is running"}


@app.middleware("http")
async def track_metrics(request: Request, call_next):
    response = await call_next(request)
    return response