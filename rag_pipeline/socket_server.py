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
    print(f"[SOCKET-SERVER-connect] ===== NEW CLIENT CONNECTED: {sid} =====")
    logger.info(f"[SOCKET-SERVER-connect] Client {sid} connected")
    
    connected_clients[sid] = {
        "connected_at": datetime.now().isoformat(),
        "subscriptions": set(),
        "user_id": auth.get("user_id") if auth else None
    }
    
    print(f"[SOCKET-SERVER-connect] Total connected clients: {len(connected_clients)}")
    print(f"[SOCKET-SERVER-connect] Connected client IDs: {list(connected_clients.keys())}")
    
    await sio.emit('message', {
        'type': 'connection_status',
        'status': 'connected',
        'message': 'Connected to RAG pipeline server',
        'timestamp': datetime.now().isoformat(),
        'server': 'rag_pipeline'
    }, room=sid)

@sio.event
async def disconnect(sid):
    print(f"[SOCKET-SERVER-disconnect] ===== CLIENT DISCONNECTED: {sid} =====")
    logger.info(f"[SOCKET-SERVER-disconnect] Client {sid} disconnected")
    if sid in connected_clients:
        del connected_clients[sid]
    print(f"[SOCKET-SERVER-disconnect] Remaining clients: {len(connected_clients)}")

@sio.event
async def message(sid, data):
    print(f"[SOCKET-SERVER-message] Received from {sid}: {data}")
    logger.info(f"[SOCKET-SERVER-message] Received from {sid}: {data}")
    
    # Check if it's an identification message
    if isinstance(data, dict) and data.get('type') == 'identify':
        client_name = data.get('client', 'unknown')
        print(f"[SOCKET-SERVER-message] ===== CLIENT IDENTIFIED: {client_name} (SID: {sid}) =====")
        if sid in connected_clients:
            connected_clients[sid]['client_name'] = client_name
    
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

@sio.on("upload-complete")
async def upload_complete(sid, data):
    file_name = data.get('fileName', 'Unknown')
    google_drive_id = data.get('googleDriveId', 'Unknown')
    file_size = data.get('fileSize', 0)
    
    print(f"[SOCKET-SERVER-upload_complete] UPLOAD COMPLETED! File: {file_name}")
    print(f"[SOCKET-SERVER-upload_complete] Google Drive ID: {google_drive_id}")
    print(f"[SOCKET-SERVER-upload_complete] File Size: {file_size} bytes")
    print(f"[SOCKET-SERVER-upload_complete] Received from client: {sid}")
    print(f"[SOCKET-SERVER-upload_complete] Connected clients: {list(connected_clients.keys())}")
    
    logger.info(f"[SOCKET-SERVER-upload_complete] Upload completed - File: {file_name}, Drive ID: {google_drive_id}, Size: {file_size}")
    
    # Acknowledge to the original sender
    await sio.emit('message', {
        'type': 'upload_acknowledged',
        'file_name': file_name,
        'google_drive_id': google_drive_id,
        'message': f'Upload of {file_name} acknowledged by server',
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    }, room=sid)
    
    # Broadcast upload completion to all connected clients (including Google Drive watcher)
    print(f"[SOCKET-SERVER-upload_complete] Broadcasting upload completion to {len(connected_clients)} connected clients")
    await sio.emit('upload-complete', {
        'fileName': file_name,
        'googleDriveId': google_drive_id,
        'fileSize': file_size,
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    })  # No room specified = broadcast to all clients

@sio.on("processing-started")
async def processing_started(sid, data):
    file_name = data.get('fileName', 'Unknown')
    google_drive_id = data.get('googleDriveId', 'Unknown')
    pipeline_type = data.get('pipelineType', 'unknown')
    
    print(f"[SOCKET-SERVER-processing_started] PROCESSING STARTED! File: {file_name}")
    print(f"[SOCKET-SERVER-processing_started] Google Drive ID: {google_drive_id}")
    print(f"[SOCKET-SERVER-processing_started] Pipeline Type: {pipeline_type}")
    print(f"[SOCKET-SERVER-processing_started] Received from client: {sid}")
    
    logger.info(f"[SOCKET-SERVER-processing_started] Processing started - File: {file_name}, Drive ID: {google_drive_id}, Pipeline: {pipeline_type}")
    
    # Acknowledge to the original sender
    await sio.emit('message', {
        'type': 'processing_started_acknowledged',
        'file_name': file_name,
        'google_drive_id': google_drive_id,
        'message': f'Processing started for {file_name} acknowledged by server',
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    }, room=sid)
    
    # Broadcast processing started to all connected clients (including frontend)
    print(f"[SOCKET-SERVER-processing_started] Broadcasting processing started to {len(connected_clients)} connected clients")
    await sio.emit('processing-started', {
        'fileName': file_name,
        'googleDriveId': google_drive_id,
        'pipelineType': pipeline_type,
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    })  # No room specified = broadcast to all clients

@sio.on("processing-complete")
async def processing_complete(sid, data):
    file_name = data.get('fileName', 'Unknown')
    google_drive_id = data.get('googleDriveId', 'Unknown')
    pipeline_type = data.get('pipelineType', 'unknown')
    
    print(f"[SOCKET-SERVER-processing_complete] PROCESSING COMPLETE! File: {file_name}")
    print(f"[SOCKET-SERVER-processing_complete] Google Drive ID: {google_drive_id}")
    print(f"[SOCKET-SERVER-processing_complete] Pipeline Type: {pipeline_type}")
    print(f"[SOCKET-SERVER-processing_complete] Received from client: {sid}")
    
    logger.info(f"[SOCKET-SERVER-processing_complete] Processing complete - File: {file_name}, Drive ID: {google_drive_id}, Pipeline: {pipeline_type}")
    
    # Acknowledge to the original sender
    await sio.emit('message', {
        'type': 'processing_complete_acknowledged',
        'file_name': file_name,
        'google_drive_id': google_drive_id,
        'message': f'Processing complete for {file_name} acknowledged by server',
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    }, room=sid)
    
    # Broadcast processing complete to all connected clients (including frontend)
    print(f"[SOCKET-SERVER-processing_complete] Broadcasting processing complete to {len(connected_clients)} connected clients")
    await sio.emit('processing-complete', {
        'fileName': file_name,
        'googleDriveId': google_drive_id,
        'pipelineType': pipeline_type,
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    })  # No room specified = broadcast to all clients

@sio.on("processing-failed")
async def processing_failed(sid, data):
    file_name = data.get('fileName', 'Unknown')
    google_drive_id = data.get('googleDriveId', 'Unknown')
    pipeline_type = data.get('pipelineType', 'unknown')
    error_message = data.get('error', 'Unknown error')
    
    print(f"[SOCKET-SERVER-processing_failed] PROCESSING FAILED! File: {file_name}")
    print(f"[SOCKET-SERVER-processing_failed] Google Drive ID: {google_drive_id}")
    print(f"[SOCKET-SERVER-processing_failed] Pipeline Type: {pipeline_type}")
    print(f"[SOCKET-SERVER-processing_failed] Error: {error_message}")
    print(f"[SOCKET-SERVER-processing_failed] Received from client: {sid}")
    
    logger.error(f"[SOCKET-SERVER-processing_failed] Processing failed - File: {file_name}, Drive ID: {google_drive_id}, Pipeline: {pipeline_type}, Error: {error_message}")
    
    # Acknowledge to the original sender
    await sio.emit('message', {
        'type': 'processing_failed_acknowledged',
        'file_name': file_name,
        'google_drive_id': google_drive_id,
        'error': error_message,
        'message': f'Processing failed for {file_name} acknowledged by server',
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    }, room=sid)
    
    # Broadcast processing failed to all connected clients (including frontend)
    print(f"[SOCKET-SERVER-processing_failed] Broadcasting processing failed to {len(connected_clients)} connected clients")
    await sio.emit('processing-failed', {
        'fileName': file_name,
        'googleDriveId': google_drive_id,
        'pipelineType': pipeline_type,
        'error': error_message,
        'timestamp': datetime.now().isoformat(),
        'from_server': True
    })  # No room specified = broadcast to all clients

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