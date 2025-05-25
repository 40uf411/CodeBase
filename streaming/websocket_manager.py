from typing import List, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from uuid import UUID

class ConnectionManager:
    """
    WebSocket connection manager for real-time streaming.
    
    Handles:
    - Connection management
    - Broadcasting messages
    - Permission checks
    - Entity-specific subscriptions
    """
    
    def __init__(self):
        # Active connections: {client_id: {"websocket": websocket, "subscriptions": [entity_ids]}}
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        # Entity subscriptions: {entity_id: [client_ids]}
        self.entity_subscribers: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Connect a new client.
        
        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.active_connections[client_id] = {
            "websocket": websocket,
            "subscriptions": []
        }
    
    def disconnect(self, client_id: str) -> None:
        """
        Disconnect a client.
        
        Args:
            client_id: Client identifier
        """
        # Remove client from entity subscriptions
        for entity_id, subscribers in self.entity_subscribers.items():
            if client_id in subscribers:
                subscribers.remove(client_id)
        
        # Remove client from active connections
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def subscribe(self, client_id: str, entity_id: str) -> None:
        """
        Subscribe a client to an entity.
        
        Args:
            client_id: Client identifier
            entity_id: Entity identifier
        """
        # Add entity to client subscriptions
        if client_id in self.active_connections:
            if entity_id not in self.active_connections[client_id]["subscriptions"]:
                self.active_connections[client_id]["subscriptions"].append(entity_id)
        
        # Add client to entity subscribers
        if entity_id not in self.entity_subscribers:
            self.entity_subscribers[entity_id] = []
        
        if client_id not in self.entity_subscribers[entity_id]:
            self.entity_subscribers[entity_id].append(client_id)
    
    async def unsubscribe(self, client_id: str, entity_id: str) -> None:
        """
        Unsubscribe a client from an entity.
        
        Args:
            client_id: Client identifier
            entity_id: Entity identifier
        """
        # Remove entity from client subscriptions
        if client_id in self.active_connections:
            if entity_id in self.active_connections[client_id]["subscriptions"]:
                self.active_connections[client_id]["subscriptions"].remove(entity_id)
        
        # Remove client from entity subscribers
        if entity_id in self.entity_subscribers:
            if client_id in self.entity_subscribers[entity_id]:
                self.entity_subscribers[entity_id].remove(client_id)
    
    async def broadcast_to_entity_subscribers(self, entity_id: str, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all subscribers of an entity.
        
        Args:
            entity_id: Entity identifier
            message: Message to broadcast
        """
        if entity_id in self.entity_subscribers:
            for client_id in self.entity_subscribers[entity_id]:
                if client_id in self.active_connections:
                    websocket = self.active_connections[client_id]["websocket"]
                    await websocket.send_json(message)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message to broadcast
        """
        for client_id, connection in self.active_connections.items():
            websocket = connection["websocket"]
            await websocket.send_json(message)
    
    async def send_personal_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """
        Send a message to a specific client.
        
        Args:
            client_id: Client identifier
            message: Message to send
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]["websocket"]
            await websocket.send_json(message)


# Singleton instance
connection_manager = ConnectionManager()


async def handle_websocket_connection(websocket: WebSocket, client_id: str, user_id: Optional[UUID] = None):
    """
    Handle a WebSocket connection.
    
    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
        user_id: User ID for authentication (optional)
    """
    await connection_manager.connect(websocket, client_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "message": "Connected to WebSocket server"
        })
        
        # Handle messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle subscription requests
                if message.get("type") == "subscribe" and "entity_id" in message:
                    entity_id = message["entity_id"]
                    await connection_manager.subscribe(client_id, entity_id)
                    await websocket.send_json({
                        "type": "subscription_success",
                        "entity_id": entity_id
                    })
                
                # Handle unsubscription requests
                elif message.get("type") == "unsubscribe" and "entity_id" in message:
                    entity_id = message["entity_id"]
                    await connection_manager.unsubscribe(client_id, entity_id)
                    await websocket.send_json({
                        "type": "unsubscription_success",
                        "entity_id": entity_id
                    })
                
                # Echo other messages back (for testing)
                else:
                    await websocket.send_json({
                        "type": "echo",
                        "message": message
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
    
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        # Handle other exceptions
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
        connection_manager.disconnect(client_id)
