#!/usr/bin/env python3

import asyncio
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Set
import json
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True
)

app = FastAPI(
    title="RAG Pipeline Socket.IO Server",
    description="Real-time updates for RAG pipeline processing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_app = socketio.ASGIApp(sio, app)

connected_clients: Dict[str, Dict[str, Any]] = {}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "connected_clients": len(connected_clients),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/clients")
async def get_clients():
    return {
        "connected_clients": list(connected_clients.keys()),
        "count": len(connected_clients)
    }

@sio.event
async def connect(sid, environ, auth):
    logger.info(f"[SOCKET-SERVER-connect] Client {sid} connected")
    
    connected_clients[sid] = {
        "connected_at": datetime.now().isoformat(),
        "subscriptions": set(),
        "user_id": auth.get("user_id") if auth else None
    }
    
    await sio.emit('message', {
        'type': 'connection_status',
        'status': 'connected',
        'message': 'Connected to RAG pipeline server',
        'timestamp': datetime.now().isoformat(),
        'server': 'rag_pipeline'
    }, room=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"[SOCKET-SERVER-disconnect] Client {sid} disconnected")
    if sid in connected_clients:
        del connected_clients[sid]

@sio.event
async def message(sid, data):
    logger.info(f"[SOCKET-SERVER-message] Received from {sid}: {data}")
    
    await sio.emit('message', {
        'type': 'echo',
        'original_data': data,
        'message': f'Server received your message: {data}',
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    }, room=sid)

@sio.event
async def subscribe_to_updates(sid, data):
    subscription_type = data.get('type', 'all')
    
    if sid in connected_clients:
        connected_clients[sid]['subscriptions'].add(subscription_type)
        
        await sio.emit('message', {
            'type': 'subscription_confirmed',
            'subscription_type': subscription_type,
            'message': f'Subscribed to {subscription_type} updates',
            'timestamp': datetime.now().isoformat()
        }, room=sid)
        
        logger.info(f"[SOCKET-SERVER-subscribe] Client {sid} subscribed to {subscription_type}")

@sio.event
async def unsubscribe_from_updates(sid, data):
    subscription_type = data.get('type', 'all')
    
    if sid in connected_clients:
        connected_clients[sid]['subscriptions'].discard(subscription_type)
        
        await sio.emit('message', {
            'type': 'subscription_cancelled',
            'subscription_type': subscription_type,
            'message': f'Unsubscribed from {subscription_type} updates',
            'timestamp': datetime.now().isoformat()
        }, room=sid)
        
        logger.info(f"[SOCKET-SERVER-unsubscribe] Client {sid} unsubscribed from {subscription_type}")

@sio.event
async def broadcast(sid, data):
    logger.info(f"[SOCKET-SERVER-broadcast] Received broadcast from {sid}: {data}")
    
    await sio.emit('broadcast-received', {
        'type': 'confirmation',
        'original_message': data.get('message', ''),
        'message': 'Broadcast successfully received by server',
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    }, room=sid)
    
    logger.info(f"[SOCKET-SERVER-broadcast] Sent confirmation back to {sid}")

async def emit_processing_status(file_info: Dict[str, Any], status: str, pipeline_type: str = "unknown"):
    update_data = {
        'type': 'file_processing',
        'status': status,
        'file_info': file_info,
        'pipeline_type': pipeline_type,
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    }
    
    logger.info(f"[SOCKET-SERVER-emit_processing_status] Broadcasting: {update_data}")
    
    for sid, client_data in connected_clients.items():
        if 'file_processing' in client_data['subscriptions'] or 'all' in client_data['subscriptions']:
            await sio.emit('message', update_data, room=sid)

async def emit_pipeline_status(pipeline_type: str, status: str, details: Dict[str, Any] = None):
    update_data = {
        'type': 'pipeline_status',
        'pipeline_type': pipeline_type,
        'status': status,
        'details': details or {},
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    }
    
    logger.info(f"[SOCKET-SERVER-emit_pipeline_status] Broadcasting: {update_data}")
    
    for sid, client_data in connected_clients.items():
        if 'pipeline_status' in client_data['subscriptions'] or 'all' in client_data['subscriptions']:
            await sio.emit('message', update_data, room=sid)

async def emit_error_notification(error_info: Dict[str, Any], pipeline_type: str = "unknown"):
    error_data = {
        'type': 'error',
        'error_info': error_info,
        'pipeline_type': pipeline_type,
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    }
    
    logger.error(f"[SOCKET-SERVER-emit_error_notification] Broadcasting error: {error_data}")
    
    for sid in connected_clients.keys():
        await sio.emit('message', error_data, room=sid)

async def broadcast_to_all(message_data: Dict[str, Any]):
    """Broadcast a message to all connected clients"""
    message_data['timestamp'] = datetime.now().isoformat()
    message_data['from_server'] = True
    
    for sid in connected_clients.keys():
        await sio.emit('message', message_data, room=sid)

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("SOCKET_PORT", 8002))
    host = os.environ.get("SOCKET_HOST", "0.0.0.0")
    
    logger.info(f"[SOCKET-SERVER-main] Starting Socket.IO server on {host}:{port}")
    
    uvicorn.run(
        socket_app,
        host=host,
        port=port,
        log_level="info"
    )