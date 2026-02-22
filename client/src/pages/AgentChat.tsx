import { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Loader2, Send, Copy, Download, Brain, Zap, ChevronDown, ChevronRight, Moon, Sun, Home, BarChart2, Settings } from 'lucide-react';
import { Streamdown } from 'streamdown';
import { useLocation } from 'wouter';

// Use relative URLs to leverage Vite proxy (or direct URL in production)
const PYTHON_AGENT_URL = import.meta.env.VITE_PYTHON_AGENT_URL || '';

interface ThoughtInfo {
  reasoning: string;
  plan: string[];
  next_action: string;
  confidence: number;
}

interface ActionInfo {
  type: string;
  description: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  thinking?: ThoughtInfo;
  actions?: ActionInfo[];
  timestamp: Date;
  isStreaming?: boolean;
  success?: boolean;
  iterations?: number;
}

interface ConversationState {
  conversationId: string;
  messages: Message[];
  isLoading: boolean;
  error?: string;
  isConnected: boolean;
  currentThought?: ThoughtInfo;
  currentActions?: ActionInfo[];
  statusMessage?: string;
}

export default function AgentChat() {
  const [state, setState] = useState<ConversationState>({
    conversationId: `conv_${Date.now()}`,
    messages: [],
    isLoading: false,
    isConnected: false,
  });

  const [inputValue, setInputValue] = useState('');
  const [darkMode, setDarkMode] = useState(() => {
    return document.documentElement.classList.contains('dark');
  });
  const [expandedThoughts, setExpandedThoughts] = useState<Set<string>>(new Set());
  const scrollRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [, navigate] = useLocation();

  // Dark mode toggle
  const toggleDarkMode = useCallback(() => {
    const newMode = !darkMode;
    setDarkMode(newMode);
    if (newMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Initialize WebSocket connection to Python backend
  const connectWebSocket = useCallback(() => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use relative URL (proxied by Vite/Node) or direct Python backend URL
    const baseHost = PYTHON_AGENT_URL 
      ? PYTHON_AGENT_URL.replace(/^https?:\/\//, '')
      : window.location.host;
    const wsUrl = `${wsProtocol}//${baseHost}/ws/chat/${state.conversationId}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      ws.onopen = () => {
        setState(prev => ({ ...prev, isConnected: true }));
        console.log('WebSocket connected to Python agent');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'connected') {
            setState(prev => ({ ...prev, isConnected: true }));
          } else if (data.type === 'thinking' || data.type === 'status') {
            setState(prev => ({ ...prev, statusMessage: data.message }));
          } else if (data.type === 'thought') {
            const thought: ThoughtInfo = {
              reasoning: data.reasoning,
              plan: data.plan || [],
              next_action: data.next_action,
              confidence: data.confidence
            };
            setState(prev => ({ ...prev, currentThought: thought }));
          } else if (data.type === 'actions') {
            setState(prev => ({ ...prev, currentActions: data.actions }));
          } else if (data.type === 'token') {
            // Append token to last assistant message
            setState(prev => {
              const messages = [...prev.messages];
              if (messages.length > 0) {
                const lastMsg = messages[messages.length - 1];
                if (lastMsg.role === 'assistant' && lastMsg.isStreaming) {
                  messages[messages.length - 1] = {
                    ...lastMsg,
                    content: lastMsg.content + data.content
                  };
                }
              }
              return { ...prev, messages };
            });
          } else if (data.type === 'complete') {
            setState(prev => {
              const messages = [...prev.messages];
              if (messages.length > 0) {
                const lastMsg = messages[messages.length - 1];
                if (lastMsg.role === 'assistant') {
                  messages[messages.length - 1] = {
                    ...lastMsg,
                    isStreaming: false,
                    thinking: prev.currentThought,
                    actions: prev.currentActions,
                    success: data.success,
                    iterations: data.iterations
                  };
                }
              }
              return {
                ...prev,
                messages,
                isLoading: false,
                statusMessage: undefined,
                currentThought: undefined,
                currentActions: undefined
              };
            });
          } else if (data.type === 'error') {
            setState(prev => ({
              ...prev,
              isLoading: false,
              error: data.error,
              statusMessage: undefined
            }));
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setState(prev => ({ ...prev, isConnected: false }));
      };

      ws.onclose = () => {
        setState(prev => ({ ...prev, isConnected: false }));
        // Auto-reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setState(prev => ({ ...prev, isConnected: false }));
    }
  }, [state.conversationId]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null; // Prevent auto-reconnect on unmount
        wsRef.current.close();
      }
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [state.messages, state.isLoading]);

  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || state.isLoading) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    const assistantMessage: Message = {
      id: `msg_${Date.now() + 1}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    setState(prev => ({
      ...prev,
      messages: [...prev.messages, userMessage, assistantMessage],
      isLoading: true,
      error: undefined,
      currentThought: undefined,
      currentActions: undefined,
    }));

    const messageToSend = inputValue;
    setInputValue('');

    // Send via WebSocket if connected
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message: messageToSend }));
    } else {
      // Fallback to REST API
      try {
        const response = await fetch(`${PYTHON_AGENT_URL}/agent/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_message: messageToSend,
            conversation_id: state.conversationId
          })
        });
        
        const data = await response.json();
        
        setState(prev => {
          const messages = [...prev.messages];
          const lastIdx = messages.length - 1;
          if (messages[lastIdx]?.role === 'assistant') {
            messages[lastIdx] = {
              ...messages[lastIdx],
              content: data.response || 'No response',
              isStreaming: false,
              thinking: data.thought ? {
                reasoning: data.thought.reasoning,
                plan: data.thought.plan || [],
                next_action: data.thought.next_action,
                confidence: data.thought.confidence
              } : undefined,
              actions: data.actions?.map((a: any) => ({
                type: a.type,
                description: a.description
              })),
              success: data.success,
              iterations: data.iteration
            };
          }
          return { ...prev, messages, isLoading: false };
        });
      } catch (err: any) {
        setState(prev => ({
          ...prev,
          isLoading: false,
          error: err.message || 'Failed to connect to agent'
        }));
      }
    }
  }, [inputValue, state.isLoading, state.conversationId]);

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const handleDownloadConversation = () => {
    const conversationText = state.messages
      .map(msg => `${msg.role.toUpperCase()} [${msg.timestamp.toLocaleTimeString()}]:\n${msg.content}`)
      .join('\n\n---\n\n');

    const element = document.createElement('a');
    element.setAttribute('href', `data:text/plain;charset=utf-8,${encodeURIComponent(conversationText)}`);
    element.setAttribute('download', `agent_conversation_${state.conversationId}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const toggleThought = (msgId: string) => {
    setExpandedThoughts(prev => {
      const next = new Set(prev);
      if (next.has(msgId)) {
        next.delete(msgId);
      } else {
        next.add(msgId);
      }
      return next;
    });
  };

  const handleNewConversation = () => {
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
    }
    const newId = `conv_${Date.now()}`;
    setState({
      conversationId: newId,
      messages: [],
      isLoading: false,
      isConnected: false,
    });
    setTimeout(connectWebSocket, 100);
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card px-4 py-3 flex-shrink-0">
        <div className="flex items-center justify-between max-w-5xl mx-auto">
          <div className="flex items-center gap-3">
            <Brain className="w-6 h-6 text-primary" />
            <div>
              <h1 className="text-lg font-bold text-foreground leading-none">Manus Agent Pro</h1>
              <p className="text-xs text-muted-foreground mt-0.5">
                ID: {state.conversationId.slice(-8)}
              </p>
            </div>
            <Badge
              variant={state.isConnected ? "default" : "secondary"}
              className={`text-xs ${state.isConnected ? 'bg-green-500 text-white' : 'bg-gray-400 text-white'}`}
            >
              {state.isConnected ? '● Live' : '○ Offline'}
            </Badge>
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
              <Home className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
              <BarChart2 className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => navigate('/settings')}>
              <Settings className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={toggleDarkMode}>
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
            <Button variant="outline" size="sm" onClick={handleNewConversation}>
              New Chat
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadConversation}
              disabled={state.messages.length === 0}
            >
              <Download className="w-4 h-4 mr-1" />
              Export
            </Button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto" ref={scrollRef}>
        <div className="max-w-5xl mx-auto px-4 py-4 space-y-4">
          {state.messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <Brain className="w-16 h-16 text-primary/30 mb-4" />
              <h2 className="text-xl font-semibold text-foreground mb-2">
                Welcome to Manus Agent Pro
              </h2>
              <p className="text-muted-foreground max-w-md">
                Start a conversation with the autonomous AI agent. It can execute commands,
                manage files, search the web, write code, and much more.
              </p>
              <div className="grid grid-cols-2 gap-3 mt-6 max-w-lg">
                {[
                  "List files in the current directory",
                  "Write a Python script to sort a list",
                  "Explain how neural networks work",
                  "Create a simple web server in Python"
                ].map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => setInputValue(suggestion)}
                    className="text-left text-sm p-3 rounded-lg border border-border hover:border-primary hover:bg-primary/5 transition-colors text-muted-foreground hover:text-foreground"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {state.messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-3xl w-full ${message.role === 'user' ? 'ml-12' : 'mr-12'}`}>
                {/* Role indicator */}
                <div className={`flex items-center gap-2 mb-1 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {message.role === 'assistant' && (
                    <div className="flex items-center gap-1">
                      <Brain className="w-3 h-3 text-primary" />
                      <span className="text-xs font-medium text-primary">Agent</span>
                      {message.iterations && (
                        <Badge variant="outline" className="text-xs h-4 px-1">
                          {message.iterations} iter
                        </Badge>
                      )}
                      {message.success !== undefined && (
                        <Badge
                          variant={message.success ? "default" : "destructive"}
                          className="text-xs h-4 px-1"
                        >
                          {message.success ? '✓' : '✗'}
                        </Badge>
                      )}
                    </div>
                  )}
                  {message.role === 'user' && (
                    <span className="text-xs font-medium text-muted-foreground">You</span>
                  )}
                </div>

                <Card
                  className={`p-4 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'bg-card text-foreground border-border'
                  }`}
                >
                  {/* Thought process (collapsible) */}
                  {message.thinking && message.role === 'assistant' && (
                    <div className="mb-3 border border-border/50 rounded-md overflow-hidden">
                      <button
                        onClick={() => toggleThought(message.id)}
                        className="w-full flex items-center gap-2 px-3 py-2 bg-muted/50 hover:bg-muted text-xs font-medium text-muted-foreground transition-colors"
                      >
                        {expandedThoughts.has(message.id) ? (
                          <ChevronDown className="w-3 h-3" />
                        ) : (
                          <ChevronRight className="w-3 h-3" />
                        )}
                        <Zap className="w-3 h-3" />
                        Agent Reasoning
                        <Badge variant="outline" className="ml-auto text-xs h-4 px-1">
                          {Math.round(message.thinking.confidence * 100)}% conf
                        </Badge>
                      </button>
                      {expandedThoughts.has(message.id) && (
                        <div className="px-3 py-2 space-y-2 bg-muted/20">
                          <div>
                            <p className="text-xs font-semibold text-muted-foreground mb-1">Reasoning:</p>
                            <p className="text-xs text-foreground/80">{message.thinking.reasoning}</p>
                          </div>
                          {message.thinking.plan.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-muted-foreground mb-1">Plan:</p>
                              <ol className="text-xs text-foreground/80 list-decimal list-inside space-y-0.5">
                                {message.thinking.plan.map((step, i) => (
                                  <li key={i}>{step}</li>
                                ))}
                              </ol>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Actions taken */}
                  {message.actions && message.actions.length > 0 && message.role === 'assistant' && (
                    <div className="mb-3 flex flex-wrap gap-1">
                      {message.actions.map((action, idx) => (
                        <Badge key={idx} variant="secondary" className="text-xs">
                          <Zap className="w-2 h-2 mr-1" />
                          {action.description?.replace('Calling tool: ', '') || action.type}
                        </Badge>
                      ))}
                    </div>
                  )}

                  {/* Message content */}
                  <div className={`${message.role === 'assistant' ? 'prose prose-sm dark:prose-invert max-w-none' : ''}`}>
                    {message.role === 'assistant' ? (
                      message.isStreaming ? (
                        <div>
                          <Streamdown>{message.content}</Streamdown>
                          <span className="inline-block w-1 h-4 bg-primary animate-pulse ml-0.5" />
                        </div>
                      ) : (
                        <Streamdown>{message.content || '...'}</Streamdown>
                      )
                    ) : (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>

                  {/* Footer */}
                  <div className={`flex items-center gap-2 mt-2 text-xs ${
                    message.role === 'user' ? 'text-primary-foreground/60 justify-end' : 'text-muted-foreground'
                  }`}>
                    <span>{message.timestamp.toLocaleTimeString()}</span>
                    {message.role === 'assistant' && !message.isStreaming && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-5 w-5 p-0 opacity-50 hover:opacity-100"
                        onClick={() => handleCopyMessage(message.content)}
                      >
                        <Copy className="w-3 h-3" />
                      </Button>
                    )}
                  </div>
                </Card>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {state.isLoading && (
            <div className="flex justify-start">
              <Card className="bg-card border-border p-4 max-w-sm">
                <div className="flex items-center gap-3">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  <div>
                    <p className="text-sm font-medium text-foreground">Agent is working...</p>
                    {state.statusMessage && (
                      <p className="text-xs text-muted-foreground mt-0.5">{state.statusMessage}</p>
                    )}
                    {state.currentThought && (
                      <p className="text-xs text-primary mt-0.5">
                        → {state.currentThought.next_action}
                      </p>
                    )}
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Error display */}
          {state.error && (
            <div className="flex justify-center">
              <Card className="bg-destructive/10 border-destructive p-3 max-w-lg">
                <p className="text-sm text-destructive">⚠ {state.error}</p>
              </Card>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-border bg-card px-4 py-3 flex-shrink-0">
        <div className="max-w-5xl mx-auto">
          <div className="flex gap-2">
            <Input
              ref={inputRef}
              placeholder="Ask the agent anything... (Enter to send, Shift+Enter for new line)"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              disabled={state.isLoading}
              className="flex-1 bg-background"
            />
            <Button
              onClick={handleSendMessage}
              disabled={state.isLoading || !inputValue.trim()}
              size="icon"
              className="shrink-0"
            >
              {state.isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
          <div className="flex items-center justify-between mt-1.5">
            <p className="text-xs text-muted-foreground">
              Agent can execute commands, manage files, write code, and more.
            </p>
            <p className="text-xs text-muted-foreground">
              {state.messages.filter(m => m.role === 'user').length} messages
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
