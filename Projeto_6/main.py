import threading
import json
import datetime
import time
from collections import deque
import queue
from flask import Flask, Response, render_template, stream_with_context
import zmq


recent_logs = deque(maxlen=50)
recent_alerts = deque(maxlen=50)
severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

_sse_clients = []
_sse_lock    = threading.Lock()


def broadcast(etype: str, data: dict):
    """Coloca o evento na fila de cada cliente SSE conectado."""
    msg = f"event: {etype}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    with _sse_lock:
        for q in _sse_clients:
            q.put_nowait(msg)



def zmq_consumer():
    """Consome eventos ZMQ de forma síncrona em thread dedicada"""

    ctx  = zmq.Context()
    sock = ctx.socket(zmq.SUB)
    sock.connect("tcp://localhost:5555")   # producer de logs
    sock.connect("tcp://localhost:5556")   # engine de alertas
    sock.subscribe("")

    print("🔌 [Dashboard ZMQ] Conectado nas portas 5555 e 5556...")

    while True:
        try:
            packet = sock.recv_json()
            ptype  = packet.get("type")

            if ptype == "LOG":
                packet.setdefault("timestamp", datetime.datetime.now().strftime("%H:%M:%S"))
                recent_logs.appendleft(packet)
                broadcast("log", packet)

            elif ptype == "ALERT":
                packet["received_at"] = datetime.datetime.now().strftime("%H:%M:%S")
                recent_alerts.appendleft(packet)

                sev = packet.get("triage", {}).get("severity", "LOW")
                if sev in severity_counts:
                    severity_counts[sev] += 1

                broadcast("alert", packet)

        except Exception as e:
            print(f"[ZMQ] Erro: {e}")

app = Flask(__name__)

@app.route("/")
def index():
    """Renderiza o dashboard com estado inicial"""
    return render_template(
        "index.html",
        logs=list(recent_logs),
        alerts=list(recent_alerts),
        counts=severity_counts,
    )


@app.route("/stream")
def stream():
    """
    Endpoint SSE — cada cliente que conecta aqui recebe sua própria Queue.
    A thread ZMQ faz broadcast colocando eventos em todas as filas.
    Assim o browser recebe o evento IMEDIATAMENTE, sem polling.
    """

    client_queue = queue.Queue()

    with _sse_lock:
        _sse_clients.append(client_queue)

    def event_generator():
        try:
            while True:
                try:
                    msg = client_queue.get(timeout=15)
                    yield msg
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            with _sse_lock:
                _sse_clients.remove(client_queue)

    return Response(
        stream_with_context(event_generator()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

if __name__ == "__main__":

    t = threading.Thread(target=zmq_consumer, daemon=True)
    t.start()

    print("[Dashboard] Acessível em http://localhost:5000")

    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)