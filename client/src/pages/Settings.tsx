import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import {
  Settings as SettingsIcon, Brain, Key, Cpu, Save, RotateCcw,
  CheckCircle, AlertCircle, Eye, EyeOff, Home, MessageSquare,
  BarChart2, Zap, Globe, Shield
} from 'lucide-react';
import { useLocation } from 'wouter';

const PYTHON_AGENT_URL = import.meta.env.VITE_PYTHON_AGENT_URL || '';

interface LLMSettings {
  provider: string;
  apiKey: string;
  model: string;
  baseUrl: string;
  temperature: number;
  maxTokens: number;
  topP: number;
}

interface AgentSettings {
  agentName: string;
  systemPrompt: string;
  maxIterations: number;
  enableReflection: boolean;
  enableMemory: boolean;
  enableWebBrowsing: boolean;
  enableFileOps: boolean;
  enableGitHub: boolean;
}

const DEFAULT_SYSTEM_PROMPT = `You are {agent_name}, an advanced autonomous AI agent. You are designed to:

1. **Think Strategically**: Break down complex tasks into manageable steps and plan your approach.
2. **Act Autonomously**: Execute tasks using available tools without requiring constant human guidance.
3. **Learn & Adapt**: Reflect on your actions, learn from errors, and improve your approach.
4. **Communicate Clearly**: Explain your reasoning, provide updates, and ask for clarification when needed.

## Your Capabilities:
- Execute terminal commands and manage files
- Browse the web and interact with websites
- Create and manage GitHub repositories
- Analyze images and process multimedia
- Schedule tasks and execute them in parallel
- Access long-term memory for context and learning

## Your Operating Principles:
- **Safety First**: Always ask for approval before executing high-risk operations
- **Transparency**: Explain what you're doing and why
- **Error Handling**: When you encounter errors, analyze them and propose solutions
- **Continuous Learning**: Store important information in memory for future reference

## Personality:
- You are professional, efficient, and helpful.
- You speak with confidence but remain humble.
- You provide concise but comprehensive answers.`;

const LLM_PROVIDERS = [
  {
    id: 'deepseek',
    name: 'DeepSeek',
    baseUrl: 'https://api.deepseek.com',
    models: ['deepseek-chat', 'deepseek-reasoner'],
    badge: 'Recommended',
    badgeColor: 'bg-blue-500',
  },
  {
    id: 'openai',
    name: 'OpenAI (ChatGPT)',
    baseUrl: 'https://api.openai.com/v1',
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    badge: 'Popular',
    badgeColor: 'bg-green-500',
  },
  {
    id: 'gemini',
    name: 'Google Gemini',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai',
    models: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'],
    badge: 'New',
    badgeColor: 'bg-purple-500',
  },
  {
    id: 'anthropic',
    name: 'Anthropic Claude',
    baseUrl: 'https://api.anthropic.com/v1',
    models: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
    badge: '',
    badgeColor: '',
  },
  {
    id: 'groq',
    name: 'Groq (Fast)',
    baseUrl: 'https://api.groq.com/openai/v1',
    models: ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
    badge: 'Fast',
    badgeColor: 'bg-orange-500',
  },
  {
    id: 'ollama',
    name: 'Ollama (Local)',
    baseUrl: 'http://localhost:11434/v1',
    models: ['llama3.2', 'mistral', 'codellama', 'phi3'],
    badge: 'Local',
    badgeColor: 'bg-gray-500',
  },
  {
    id: 'custom',
    name: 'Custom OpenAI-Compatible',
    baseUrl: '',
    models: [],
    badge: 'Advanced',
    badgeColor: 'bg-yellow-500',
  },
];

export default function Settings() {
  const [, navigate] = useLocation();
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testMessage, setTestMessage] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [customModel, setCustomModel] = useState('');

  const [llmSettings, setLlmSettings] = useState<LLMSettings>(() => {
    const saved = localStorage.getItem('agent_llm_settings');
    if (saved) return JSON.parse(saved);
    return {
      provider: 'deepseek',
      apiKey: '',
      model: 'deepseek-chat',
      baseUrl: 'https://api.deepseek.com',
      temperature: 0.7,
      maxTokens: 4096,
      topP: 0.95,
    };
  });

  const [agentSettings, setAgentSettings] = useState<AgentSettings>(() => {
    const saved = localStorage.getItem('agent_agent_settings');
    if (saved) return JSON.parse(saved);
    return {
      agentName: 'Manus Agent Pro',
      systemPrompt: DEFAULT_SYSTEM_PROMPT,
      maxIterations: 10,
      enableReflection: true,
      enableMemory: true,
      enableWebBrowsing: true,
      enableFileOps: true,
      enableGitHub: true,
    };
  });

  const selectedProvider = LLM_PROVIDERS.find(p => p.id === llmSettings.provider);

  const handleProviderChange = (providerId: string) => {
    const provider = LLM_PROVIDERS.find(p => p.id === providerId);
    if (provider) {
      setLlmSettings(prev => ({
        ...prev,
        provider: providerId,
        baseUrl: provider.baseUrl,
        model: provider.models[0] || '',
      }));
    }
  };

  const handleSaveSettings = async () => {
    setSaveStatus('saving');
    try {
      // Save to localStorage
      localStorage.setItem('agent_llm_settings', JSON.stringify(llmSettings));
      localStorage.setItem('agent_agent_settings', JSON.stringify(agentSettings));

      // Send to backend
      const response = await fetch(`${PYTHON_AGENT_URL}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          llm: {
            provider: llmSettings.provider,
            api_key: llmSettings.apiKey,
            model: llmSettings.model,
            base_url: llmSettings.baseUrl,
            temperature: llmSettings.temperature,
            max_tokens: llmSettings.maxTokens,
            top_p: llmSettings.topP,
          },
          agent: {
            name: agentSettings.agentName,
            system_prompt: agentSettings.systemPrompt,
            max_iterations: agentSettings.maxIterations,
            enable_reflection: agentSettings.enableReflection,
            enable_memory: agentSettings.enableMemory,
            enable_web_browsing: agentSettings.enableWebBrowsing,
            enable_file_ops: agentSettings.enableFileOps,
            enable_github: agentSettings.enableGitHub,
          }
        })
      });

      if (response.ok) {
        setSaveStatus('saved');
      } else {
        // Settings saved locally even if backend fails
        setSaveStatus('saved');
      }
    } catch {
      // Save locally even if backend is unreachable
      setSaveStatus('saved');
    }
    setTimeout(() => setSaveStatus('idle'), 3000);
  };

  const handleTestConnection = async () => {
    setTestStatus('testing');
    setTestMessage('');
    try {
      const response = await fetch(`${PYTHON_AGENT_URL}/settings/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: llmSettings.provider,
          api_key: llmSettings.apiKey,
          model: llmSettings.model,
          base_url: llmSettings.baseUrl,
        })
      });

      const data = await response.json();
      if (data.success) {
        setTestStatus('success');
        setTestMessage(data.message || 'Connection successful!');
      } else {
        setTestStatus('error');
        setTestMessage(data.error || 'Connection failed');
      }
    } catch (err: any) {
      setTestStatus('error');
      setTestMessage('Cannot reach backend server. Make sure the Python server is running.');
    }
    setTimeout(() => setTestStatus('idle'), 5000);
  };

  const handleResetSystemPrompt = () => {
    setAgentSettings(prev => ({ ...prev, systemPrompt: DEFAULT_SYSTEM_PROMPT }));
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card px-4 py-3">
        <div className="flex items-center justify-between max-w-5xl mx-auto">
          <div className="flex items-center gap-3">
            <SettingsIcon className="w-6 h-6 text-primary" />
            <div>
              <h1 className="text-lg font-bold text-foreground leading-none">Agent Settings</h1>
              <p className="text-xs text-muted-foreground mt-0.5">Configure LLM provider, API keys & agent behavior</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => navigate('/')}>
              <Home className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => navigate('/chat')}>
              <MessageSquare className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
              <BarChart2 className="w-4 h-4" />
            </Button>
            <Button
              onClick={handleSaveSettings}
              disabled={saveStatus === 'saving'}
              size="sm"
              className="gap-2"
            >
              {saveStatus === 'saving' ? (
                <><Cpu className="w-4 h-4 animate-spin" /> Saving...</>
              ) : saveStatus === 'saved' ? (
                <><CheckCircle className="w-4 h-4 text-green-400" /> Saved!</>
              ) : (
                <><Save className="w-4 h-4" /> Save Settings</>
              )}
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-6">
        <Tabs defaultValue="llm" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="llm" className="gap-2">
              <Key className="w-4 h-4" /> LLM Provider
            </TabsTrigger>
            <TabsTrigger value="agent" className="gap-2">
              <Brain className="w-4 h-4" /> Agent Personality
            </TabsTrigger>
            <TabsTrigger value="tools" className="gap-2">
              <Zap className="w-4 h-4" /> Tools & Features
            </TabsTrigger>
          </TabsList>

          {/* ==================== LLM PROVIDER TAB ==================== */}
          <TabsContent value="llm" className="space-y-6">
            {/* Provider Selection */}
            <Card className="p-6">
              <h3 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
                <Globe className="w-4 h-4 text-primary" /> Select LLM Provider
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
                {LLM_PROVIDERS.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => handleProviderChange(provider.id)}
                    className={`relative text-left p-4 rounded-lg border-2 transition-all ${
                      llmSettings.provider === provider.id
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/50 hover:bg-muted/50'
                    }`}
                  >
                    {provider.badge && (
                      <span className={`absolute top-2 right-2 text-xs text-white px-1.5 py-0.5 rounded ${provider.badgeColor}`}>
                        {provider.badge}
                      </span>
                    )}
                    <p className="font-medium text-foreground text-sm">{provider.name}</p>
                    <p className="text-xs text-muted-foreground mt-1 truncate">{provider.baseUrl || 'Custom URL'}</p>
                  </button>
                ))}
              </div>
            </Card>

            {/* API Configuration */}
            <Card className="p-6">
              <h3 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
                <Key className="w-4 h-4 text-primary" /> API Configuration
              </h3>
              <div className="space-y-4">
                {/* API Key */}
                <div className="space-y-2">
                  <Label htmlFor="apiKey">
                    API Key
                    <span className="text-destructive ml-1">*</span>
                  </Label>
                  <div className="relative">
                    <Input
                      id="apiKey"
                      type={showApiKey ? 'text' : 'password'}
                      placeholder={`Enter your ${selectedProvider?.name || 'provider'} API key`}
                      value={llmSettings.apiKey}
                      onChange={(e) => setLlmSettings(prev => ({ ...prev, apiKey: e.target.value }))}
                      className="pr-10 font-mono text-sm"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {llmSettings.provider === 'deepseek' && 'Get your key at platform.deepseek.com'}
                    {llmSettings.provider === 'openai' && 'Get your key at platform.openai.com'}
                    {llmSettings.provider === 'gemini' && 'Get your key at aistudio.google.com'}
                    {llmSettings.provider === 'anthropic' && 'Get your key at console.anthropic.com'}
                    {llmSettings.provider === 'groq' && 'Get your key at console.groq.com'}
                    {llmSettings.provider === 'ollama' && 'No API key needed for local Ollama'}
                    {llmSettings.provider === 'custom' && 'Enter the API key for your custom provider'}
                  </p>
                </div>

                {/* Base URL */}
                <div className="space-y-2">
                  <Label htmlFor="baseUrl">Base URL</Label>
                  <Input
                    id="baseUrl"
                    placeholder="https://api.example.com/v1"
                    value={llmSettings.baseUrl}
                    onChange={(e) => setLlmSettings(prev => ({ ...prev, baseUrl: e.target.value }))}
                    className="font-mono text-sm"
                  />
                </div>

                {/* Model Selection */}
                <div className="space-y-2">
                  <Label htmlFor="model">Model</Label>
                  {selectedProvider && selectedProvider.models.length > 0 ? (
                    <Select
                      value={llmSettings.model}
                      onValueChange={(value) => setLlmSettings(prev => ({ ...prev, model: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                      <SelectContent>
                        {selectedProvider.models.map(model => (
                          <SelectItem key={model} value={model}>{model}</SelectItem>
                        ))}
                        <SelectItem value="__custom__">Custom model name...</SelectItem>
                      </SelectContent>
                    </Select>
                  ) : (
                    <Input
                      placeholder="Enter model name (e.g., gpt-4o, deepseek-chat)"
                      value={llmSettings.model}
                      onChange={(e) => setLlmSettings(prev => ({ ...prev, model: e.target.value }))}
                      className="font-mono text-sm"
                    />
                  )}
                  {llmSettings.model === '__custom__' && (
                    <Input
                      placeholder="Enter custom model name"
                      value={customModel}
                      onChange={(e) => {
                        setCustomModel(e.target.value);
                        setLlmSettings(prev => ({ ...prev, model: e.target.value }));
                      }}
                      className="font-mono text-sm mt-2"
                    />
                  )}
                </div>

                {/* Test Connection */}
                <div className="flex items-center gap-3 pt-2">
                  <Button
                    variant="outline"
                    onClick={handleTestConnection}
                    disabled={testStatus === 'testing' || !llmSettings.apiKey}
                    className="gap-2"
                  >
                    {testStatus === 'testing' ? (
                      <><Cpu className="w-4 h-4 animate-spin" /> Testing...</>
                    ) : testStatus === 'success' ? (
                      <><CheckCircle className="w-4 h-4 text-green-500" /> Connected!</>
                    ) : testStatus === 'error' ? (
                      <><AlertCircle className="w-4 h-4 text-destructive" /> Failed</>
                    ) : (
                      <><Zap className="w-4 h-4" /> Test Connection</>
                    )}
                  </Button>
                  {testMessage && (
                    <p className={`text-sm ${testStatus === 'success' ? 'text-green-500' : 'text-destructive'}`}>
                      {testMessage}
                    </p>
                  )}
                </div>
              </div>
            </Card>

            {/* Model Parameters */}
            <Card className="p-6">
              <h3 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-primary" /> Model Parameters
              </h3>
              <div className="space-y-6">
                {/* Temperature */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Temperature</Label>
                    <span className="text-sm font-mono text-primary">{llmSettings.temperature.toFixed(2)}</span>
                  </div>
                  <Slider
                    min={0}
                    max={2}
                    step={0.05}
                    value={[llmSettings.temperature]}
                    onValueChange={([val]) => setLlmSettings(prev => ({ ...prev, temperature: val }))}
                  />
                  <p className="text-xs text-muted-foreground">
                    Lower = more focused/deterministic, Higher = more creative/random (0.7 recommended)
                  </p>
                </div>

                {/* Max Tokens */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Max Tokens</Label>
                    <span className="text-sm font-mono text-primary">{llmSettings.maxTokens.toLocaleString()}</span>
                  </div>
                  <Slider
                    min={512}
                    max={32768}
                    step={512}
                    value={[llmSettings.maxTokens]}
                    onValueChange={([val]) => setLlmSettings(prev => ({ ...prev, maxTokens: val }))}
                  />
                  <p className="text-xs text-muted-foreground">Maximum tokens in the response (4096 recommended)</p>
                </div>

                {/* Top P */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Top P</Label>
                    <span className="text-sm font-mono text-primary">{llmSettings.topP.toFixed(2)}</span>
                  </div>
                  <Slider
                    min={0.1}
                    max={1}
                    step={0.05}
                    value={[llmSettings.topP]}
                    onValueChange={([val]) => setLlmSettings(prev => ({ ...prev, topP: val }))}
                  />
                  <p className="text-xs text-muted-foreground">Nucleus sampling parameter (0.95 recommended)</p>
                </div>
              </div>
            </Card>
          </TabsContent>

          {/* ==================== AGENT PERSONALITY TAB ==================== */}
          <TabsContent value="agent" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
                <Brain className="w-4 h-4 text-primary" /> Agent Identity
              </h3>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="agentName">Agent Name</Label>
                  <Input
                    id="agentName"
                    placeholder="e.g., Manus Agent Pro"
                    value={agentSettings.agentName}
                    onChange={(e) => setAgentSettings(prev => ({ ...prev, agentName: e.target.value }))}
                  />
                  <p className="text-xs text-muted-foreground">
                    This name will replace {'{agent_name}'} in the system prompt
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="systemPrompt">System Prompt (Agent Personality)</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleResetSystemPrompt}
                      className="gap-1 text-xs h-7"
                    >
                      <RotateCcw className="w-3 h-3" /> Reset to Default
                    </Button>
                  </div>
                  <Textarea
                    id="systemPrompt"
                    placeholder="Enter the system prompt that defines your agent's personality and behavior..."
                    value={agentSettings.systemPrompt}
                    onChange={(e) => setAgentSettings(prev => ({ ...prev, systemPrompt: e.target.value }))}
                    className="min-h-[400px] font-mono text-sm resize-y"
                  />
                  <p className="text-xs text-muted-foreground">
                    This prompt defines how your agent thinks, behaves, and responds. Use {'{agent_name}'} as a placeholder for the agent name.
                  </p>
                </div>
              </div>
            </Card>

            {/* Behavior Settings */}
            <Card className="p-6">
              <h3 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
                <Cpu className="w-4 h-4 text-primary" /> Behavior Settings
              </h3>
              <div className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label>Max Iterations per Task</Label>
                    <span className="text-sm font-mono text-primary">{agentSettings.maxIterations}</span>
                  </div>
                  <Slider
                    min={1}
                    max={20}
                    step={1}
                    value={[agentSettings.maxIterations]}
                    onValueChange={([val]) => setAgentSettings(prev => ({ ...prev, maxIterations: val }))}
                  />
                  <p className="text-xs text-muted-foreground">
                    Maximum number of think-act-observe cycles before giving a final answer
                  </p>
                </div>

                <div className="flex items-center justify-between py-2 border-t border-border">
                  <div>
                    <p className="text-sm font-medium text-foreground">Self-Reflection</p>
                    <p className="text-xs text-muted-foreground">Agent reflects on errors and adjusts its approach</p>
                  </div>
                  <Switch
                    checked={agentSettings.enableReflection}
                    onCheckedChange={(checked) => setAgentSettings(prev => ({ ...prev, enableReflection: checked }))}
                  />
                </div>

                <div className="flex items-center justify-between py-2 border-t border-border">
                  <div>
                    <p className="text-sm font-medium text-foreground">Long-term Memory</p>
                    <p className="text-xs text-muted-foreground">Store and retrieve conversation context using ChromaDB</p>
                  </div>
                  <Switch
                    checked={agentSettings.enableMemory}
                    onCheckedChange={(checked) => setAgentSettings(prev => ({ ...prev, enableMemory: checked }))}
                  />
                </div>
              </div>
            </Card>
          </TabsContent>

          {/* ==================== TOOLS & FEATURES TAB ==================== */}
          <TabsContent value="tools" className="space-y-6">
            <Card className="p-6">
              <h3 className="text-base font-semibold text-foreground mb-4 flex items-center gap-2">
                <Zap className="w-4 h-4 text-primary" /> Available Tools
              </h3>
              <div className="space-y-4">
                {[
                  {
                    key: 'enableWebBrowsing',
                    label: 'Web Browsing',
                    description: 'Navigate websites, search the web, extract content',
                    icon: Globe,
                  },
                  {
                    key: 'enableFileOps',
                    label: 'File Operations',
                    description: 'Read, write, list, and delete files on the system',
                    icon: Shield,
                  },
                  {
                    key: 'enableGitHub',
                    label: 'GitHub Integration',
                    description: 'Clone repos, create repositories, manage code',
                    icon: Cpu,
                  },
                ].map(({ key, label, description, icon: Icon }) => (
                  <div key={key} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Icon className="w-4 h-4 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-foreground">{label}</p>
                        <p className="text-xs text-muted-foreground">{description}</p>
                      </div>
                    </div>
                    <Switch
                      checked={agentSettings[key as keyof AgentSettings] as boolean}
                      onCheckedChange={(checked) => setAgentSettings(prev => ({ ...prev, [key]: checked }))}
                    />
                  </div>
                ))}
              </div>
            </Card>

            {/* Current Config Summary */}
            <Card className="p-6 bg-muted/30">
              <h3 className="text-base font-semibold text-foreground mb-4">Current Configuration Summary</h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="space-y-1">
                  <p className="text-muted-foreground">Provider</p>
                  <Badge variant="outline">{selectedProvider?.name || llmSettings.provider}</Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Model</p>
                  <Badge variant="outline" className="font-mono">{llmSettings.model}</Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Agent Name</p>
                  <Badge variant="outline">{agentSettings.agentName}</Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Max Iterations</p>
                  <Badge variant="outline">{agentSettings.maxIterations}</Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">API Key</p>
                  <Badge variant={llmSettings.apiKey ? "default" : "destructive"}>
                    {llmSettings.apiKey ? '✓ Set' : '✗ Not Set'}
                  </Badge>
                </div>
                <div className="space-y-1">
                  <p className="text-muted-foreground">Temperature</p>
                  <Badge variant="outline">{llmSettings.temperature}</Badge>
                </div>
              </div>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Save Button at Bottom */}
        <div className="flex justify-end mt-6 pt-4 border-t border-border">
          <Button
            onClick={handleSaveSettings}
            disabled={saveStatus === 'saving'}
            size="lg"
            className="gap-2 min-w-[160px]"
          >
            {saveStatus === 'saving' ? (
              <><Cpu className="w-4 h-4 animate-spin" /> Saving...</>
            ) : saveStatus === 'saved' ? (
              <><CheckCircle className="w-4 h-4" /> Settings Saved!</>
            ) : (
              <><Save className="w-4 h-4" /> Save All Settings</>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
