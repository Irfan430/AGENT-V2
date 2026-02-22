import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, Send, Copy, Download } from 'lucide-react';
import { Streamdown } from 'streamdown';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  thinking?: string;
  actions?: string[];
  timestamp: Date;
}

interface ConversationState {
  conversationId: string;
  messages: Message[];
  isLoading: boolean;
  error?: string;
}

export default function AgentChat() {
  const [state, setState] = useState<ConversationState>({
    conversationId: '',
    messages: [],
    isLoading: false,
  });

  const [inputValue, setInputValue] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const conversationId = state.conversationId || `conv_${Date.now()}`;
    
    if (!state.conversationId) {
      setState(prev => ({ ...prev, conversationId }));
    }

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/chat/${conversationId}`;
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'token') {
          // Append token to last message
          setState(prev => {
            const messages = [...prev.messages];
            if (messages.length > 0) {
              const lastMsg = messages[messages.length - 1];
              if (lastMsg.role === 'assistant') {
                lastMsg.content += data.content;
              }
            }
            return { ...prev, messages };
          });
        } else if (data.type === 'complete') {
          setState(prev => ({ ...prev, isLoading: false }));
        } else if (data.type === 'error') {
          setState(prev => ({ ...prev, isLoading: false, error: data.error }));
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ ...prev, error: 'Connection error' }));
      };

      return () => {
        if (wsRef.current) {
          wsRef.current.close();
        }
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
    }
  }, [state.conversationId]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [state.messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || state.isLoading) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: undefined,
    }));

    setInputValue('');

    // Add assistant message placeholder
    const assistantMessage: Message = {
      id: `msg_${Date.now() + 1}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, assistantMessage],
    }));

    // Send message via WebSocket
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: inputValue }));
    }
  };

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const handleDownloadConversation = () => {
    const conversationText = state.messages
      .map(msg => `${msg.role.toUpperCase()}: ${msg.content}`)
      .join('\n\n');

    const element = document.createElement('a');
    element.setAttribute('href', `data:text/plain;charset=utf-8,${encodeURIComponent(conversationText)}`);
    element.setAttribute('download', `conversation_${state.conversationId}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Manus Agent Pro</h1>
            <p className="text-sm text-muted-foreground">
              Autonomous AI Agent - Conversation ID: {state.conversationId}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownloadConversation}
            disabled={state.messages.length === 0}
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4 max-w-4xl mx-auto">
          {state.messages.length === 0 && (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <h2 className="text-xl font-semibold text-foreground mb-2">
                  Welcome to Manus Agent Pro
                </h2>
                <p className="text-muted-foreground">
                  Start a conversation with the autonomous AI agent
                </p>
              </div>
            </div>
          )}

          {state.messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <Card
                className={`max-w-2xl p-4 ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                }`}
              >
                <div className="space-y-2">
                  {message.thinking && (
                    <div className="text-xs opacity-75 border-l-2 pl-2">
                      <strong>Thinking:</strong> {message.thinking}
                    </div>
                  )}

                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    {message.role === 'assistant' ? (
                      <Streamdown>{message.content}</Streamdown>
                    ) : (
                      <p>{message.content}</p>
                    )}
                  </div>

                  {message.actions && message.actions.length > 0 && (
                    <div className="text-xs opacity-75 border-t pt-2">
                      <strong>Actions:</strong>
                      <ul className="list-disc list-inside">
                        {message.actions.map((action, idx) => (
                          <li key={idx}>{action}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="flex items-center gap-2 text-xs opacity-50">
                    <span>
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    {message.role === 'assistant' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => handleCopyMessage(message.content)}
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            </div>
          ))}

          {state.isLoading && (
            <div className="flex justify-start">
              <Card className="bg-muted p-4">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">
                    Agent is thinking...
                  </span>
                </div>
              </Card>
            </div>
          )}

          {state.error && (
            <div className="flex justify-start">
              <Card className="bg-destructive/10 border-destructive p-4">
                <p className="text-sm text-destructive">{state.error}</p>
              </Card>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-border p-4 bg-background">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-2">
            <Input
              placeholder="Ask the agent anything..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              disabled={state.isLoading}
              className="flex-1"
            />
            <Button
              onClick={handleSendMessage}
              disabled={state.isLoading || !inputValue.trim()}
              size="icon"
            >
              {state.isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            The agent can execute commands, read files, browse the web, and more.
            Press Shift+Enter for new line.
          </p>
        </div>
      </div>
    </div>
  );
}
