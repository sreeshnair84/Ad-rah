import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: unknown;
}

interface UseWebSocketOptions {
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onMessage?: (message: WebSocketMessage) => void;
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const {
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
    onConnect,
    onDisconnect,
    onMessage,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);

  const connect = () => {
    try {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectCount.current = 0;
        onConnect?.();
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          setLastMessage(message);
          onMessage?.(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        onDisconnect?.();
        
        // Attempt to reconnect
        if (reconnectCount.current < maxReconnectAttempts) {
          reconnectCount.current++;
          console.log(`Attempting to reconnect (${reconnectCount.current}/${maxReconnectAttempts})`);
          
          reconnectTimer.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        } else {
          setError('Max reconnection attempts reached');
        }
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to create connection');
    }
  };

  const disconnect = () => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    
    setIsConnected(false);
  };

  const sendMessage = (message: unknown) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  };

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [url, connect]);

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    reconnect: connect,
    disconnect,
  };
}

// Real-time content notifications hook
export function useContentNotifications() {
  const [notifications, setNotifications] = useState<WebSocketMessage[]>([]);
  
  const wsUrl = process.env.NODE_ENV === 'production' 
    ? `wss://${window.location.host}/ws/admin`
    : 'ws://localhost:8000/ws/admin';

  const { isConnected, lastMessage, error, sendMessage } = useWebSocket(wsUrl, {
    onMessage: (message) => {
      // Add notification to list
      setNotifications(prev => [...prev.slice(-9), message]); // Keep last 10
    },
  });

  const clearNotifications = () => {
    setNotifications([]);
  };

  const markAsRead = (index: number) => {
    setNotifications(prev => prev.filter((_, i) => i !== index));
  };

  return {
    notifications,
    isConnected,
    error,
    clearNotifications,
    markAsRead,
    sendMessage,
    lastMessage,
  };
}

// Specific hooks for different notification types
export function useContentUploadNotifications() {
  const { notifications, ...rest } = useContentNotifications();
  
  const uploadNotifications = notifications.filter(
    n => ['content_uploaded', 'ai_analysis_complete', 'content_approved', 'content_rejected'].includes(n.type)
  );

  return {
    uploadNotifications,
    ...rest,
  };
}

export function useDeviceNotifications() {
  const { notifications, ...rest } = useContentNotifications();
  
  const deviceNotifications = notifications.filter(
    n => ['device_connected', 'device_disconnected', 'content_status_update'].includes(n.type)
  );

  return {
    deviceNotifications,
    ...rest,
  };
}
