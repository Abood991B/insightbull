"""
WebSocket configuration for real-time updates
"""
import logging
import socketio
from config import settings

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.CORS_ORIGINS,
    ping_interval=settings.WEBSOCKET_PING_INTERVAL,
    ping_timeout=60
)

# Create Socket.IO ASGI app
sio_app = socketio.ASGIApp(sio)


@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    logger.info(f"Client connected: {sid}")
    await sio.emit('connection_established', {'message': 'Connected to server'}, to=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {sid}")


@sio.event
async def subscribe_stock(sid, data):
    """Subscribe to real-time updates for specific stock"""
    stock_symbol = data.get('symbol')
    if stock_symbol:
        await sio.enter_room(sid, f"stock_{stock_symbol}")
        logger.info(f"Client {sid} subscribed to {stock_symbol}")
        await sio.emit('subscribed', {'symbol': stock_symbol}, to=sid)


@sio.event
async def unsubscribe_stock(sid, data):
    """Unsubscribe from stock updates"""
    stock_symbol = data.get('symbol')
    if stock_symbol:
        await sio.leave_room(sid, f"stock_{stock_symbol}")
        logger.info(f"Client {sid} unsubscribed from {stock_symbol}")
        await sio.emit('unsubscribed', {'symbol': stock_symbol}, to=sid)


async def emit_sentiment_update(stock_symbol: str, sentiment_data: dict):
    """Emit sentiment update to subscribed clients"""
    room = f"stock_{stock_symbol}"
    await sio.emit('sentiment_update', {
        'symbol': stock_symbol,
        'data': sentiment_data
    }, room=room)
    logger.debug(f"Emitted sentiment update for {stock_symbol}")


async def emit_price_update(stock_symbol: str, price_data: dict):
    """Emit price update to subscribed clients"""
    room = f"stock_{stock_symbol}"
    await sio.emit('price_update', {
        'symbol': stock_symbol,
        'data': price_data
    }, room=room)
    logger.debug(f"Emitted price update for {stock_symbol}")


async def emit_correlation_update(stock_symbol: str, correlation_data: dict):
    """Emit correlation update to subscribed clients"""
    room = f"stock_{stock_symbol}"
    await sio.emit('correlation_update', {
        'symbol': stock_symbol,
        'data': correlation_data
    }, room=room)
    logger.debug(f"Emitted correlation update for {stock_symbol}")
