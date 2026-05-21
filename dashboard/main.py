import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from cassandra_reader import connect, get_all_servers_latest, get_recent_actions
from kafka_stream import kafka_event_stream

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [dashboard] %(levelname)s %(message)s",
)

app = FastAPI(title="Infra Monitor Dashboard")
templates = Jinja2Templates(directory="templates")

_cluster = None
_session = None


@app.on_event("startup")
def startup():
    global _cluster, _session
    _cluster, _session = connect()
    logging.getLogger(__name__).info("Connected to Cassandra")


@app.on_event("shutdown")
def shutdown():
    if _cluster:
        _cluster.shutdown()


def _fetch_data() -> dict:
    servers = get_all_servers_latest(_session)
    actions = get_recent_actions(_session, limit=20)

    # Format timestamps for display
    for s in servers:
        ts = s.get("collected_at")
        s["last_seen"] = ts.strftime("%Y-%m-%d %H:%M:%S UTC") if ts else "—"

    for a in actions:
        ts = a.get("actioned_at")
        a["actioned_at_str"] = ts.strftime("%Y-%m-%d %H:%M:%S UTC") if ts else "—"
        # Truncate long diagnosis text
        diag = a.get("diagnosis", "")
        a["diagnosis_short"] = diag[:120] + "…" if len(diag) > 120 else diag

    return {"servers": servers, "actions": actions}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    data = _fetch_data()
    return templates.TemplateResponse("index.html", {"request": request, **data})


@app.get("/api/status", response_class=JSONResponse)
async def api_status():
    data = _fetch_data()
    # Convert datetimes to strings for JSON serialisation
    for s in data["servers"]:
        s.pop("collected_at", None)
    for a in data["actions"]:
        a.pop("actioned_at", None)
    return data


@app.get("/stream/kafka")
async def stream_kafka():
    return StreamingResponse(
        kafka_event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
