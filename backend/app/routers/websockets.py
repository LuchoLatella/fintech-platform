"""
Router: WebSockets
Re-exporta el router de market que contiene el endpoint WebSocket de precios.
"""
from fastapi import APIRouter

router = APIRouter()

# El WebSocket de precios está en market.py (/ws/v1/quotes)
# Aquí se pueden agregar futuros WebSockets: alertas, señales, noticias

from fastapi import WebSocket, WebSocketDisconnect
import asyncio


@router.websocket("/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket para recibir alertas en tiempo real.
    El cliente debe autenticarse enviando el token JWT como primer mensaje.
    """
    await websocket.accept()
    try:
        # Esperar token de autenticación
        token_msg = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        from jose import jwt, JWTError
        from app.config import settings
        try:
            payload = jwt.decode(token_msg, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("sub")
        except JWTError:
            await websocket.send_json({"type": "error", "message": "Token inválido"})
            await websocket.close()
            return

        await websocket.send_json({"type": "connected", "user_id": user_id})

        # Mantener conexión y enviar alertas cuando lleguen
        # En producción: suscribirse a un canal Redis Pub/Sub por user_id
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})

    except WebSocketDisconnect:
        pass
    except asyncio.TimeoutError:
        await websocket.close(code=1008, reason="Auth timeout")