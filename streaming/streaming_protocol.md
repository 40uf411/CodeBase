# Real-Time Streaming Protocol

This document outlines the protocol for real-time data streaming in the FastAPI application.

## WebSocket Protocol

### Connection

To establish a WebSocket connection:

```
ws://{server_url}/ws/{client_id}
```

Where `client_id` is a unique identifier for the client.

### Message Format

All messages are JSON objects with the following structure:

```json
{
  "type": "message_type",
  "data": {}
}
```

### Message Types

#### Client to Server

1. **Subscribe to Entity**
   ```json
   {
     "type": "subscribe",
     "entity_id": "uuid-of-entity"
   }
   ```

2. **Unsubscribe from Entity**
   ```json
   {
     "type": "unsubscribe",
     "entity_id": "uuid-of-entity"
   }
   ```

#### Server to Client

1. **Connection Established**
   ```json
   {
     "type": "connection_established",
     "client_id": "client-id",
     "message": "Connected to WebSocket server"
   }
   ```

2. **Subscription Success**
   ```json
   {
     "type": "subscription_success",
     "entity_id": "uuid-of-entity"
   }
   ```

3. **Unsubscription Success**
   ```json
   {
     "type": "unsubscription_success",
     "entity_id": "uuid-of-entity"
   }
   ```

4. **Entity Update**
   ```json
   {
     "type": "entity_update",
     "entity_id": "uuid-of-entity",
     "entity_type": "user",
     "operation": "create|update|delete",
     "data": {}
   }
   ```

5. **Error**
   ```json
   {
     "type": "error",
     "message": "Error message"
   }
   ```

## Kafka Integration

### Topics

- `{entity_name}.create` - Entity creation events
- `{entity_name}.update` - Entity update events
- `{entity_name}.delete` - Entity deletion events

### Message Format

```json
{
  "entity_id": "uuid-of-entity",
  "entity_type": "user",
  "operation": "create|update|delete",
  "timestamp": "2023-01-01T00:00:00Z",
  "data": {}
}
```

## Security Considerations

1. Authentication is required for WebSocket connections
2. Entity-level permissions are enforced for subscriptions
3. Data is filtered based on user permissions before sending

## Implementation Guidelines

1. Use the `is_streamable` flag on models to determine if they should be streamed
2. Implement event handlers in services to publish events to Kafka
3. Use the WebSocket manager to broadcast events to subscribed clients
4. Implement permission checks before allowing subscriptions
