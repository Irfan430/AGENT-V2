import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { Activity, Brain, Zap, Database, Clock, AlertCircle } from 'lucide-react';

interface AgentStats {
  status: 'healthy' | 'degraded' | 'error';
  uptime: number;
  totalConversations: number;
  totalTokensUsed: number;
  averageResponseTime: number;
  successRate: number;
  memoryUsage: number;
}

interface ToolUsage {
  name: string;
  count: number;
  successRate: number;
}

export default function AgentDashboard() {
  const [stats, setStats] = useState<AgentStats>({
    status: 'healthy',
    uptime: 24,
    totalConversations: 42,
    totalTokensUsed: 125000,
    averageResponseTime: 2.5,
    successRate: 96.5,
    memoryUsage: 45,
  });

  const [toolUsage, setToolUsage] = useState<ToolUsage[]>([
    { name: 'execute_command', count: 28, successRate: 94 },
    { name: 'read_file', count: 45, successRate: 100 },
    { name: 'write_file', count: 12, successRate: 92 },
    { name: 'git_clone', count: 8, successRate: 100 },
    { name: 'navigate_web', count: 15, successRate: 87 },
  ]);

  const [performanceData] = useState([
    { time: '00:00', responseTime: 2.1, tokens: 1200 },
    { time: '04:00', responseTime: 2.3, tokens: 1400 },
    { time: '08:00', responseTime: 2.5, tokens: 1600 },
    { time: '12:00', responseTime: 2.2, tokens: 1300 },
    { time: '16:00', responseTime: 2.6, tokens: 1700 },
    { time: '20:00', responseTime: 2.4, tokens: 1500 },
  ]);

  useEffect(() => {
    // Fetch stats from API
    const fetchStats = async () => {
      try {
        const response = await fetch('/api/health');
        const data = await response.json();
        // Update stats based on response
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Agent Dashboard</h1>
          <p className="text-muted-foreground">Monitor and manage Manus Agent Pro</p>
        </div>
        <Badge className={`${getStatusColor(stats.status)} text-white`}>
          {stats.status.toUpperCase()}
        </Badge>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Uptime</p>
              <p className="text-2xl font-bold text-foreground">{stats.uptime}h</p>
            </div>
            <Clock className="w-8 h-8 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Conversations</p>
              <p className="text-2xl font-bold text-foreground">{stats.totalConversations}</p>
            </div>
            <Brain className="w-8 h-8 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Avg Response Time</p>
              <p className="text-2xl font-bold text-foreground">{stats.averageResponseTime}s</p>
            </div>
            <Zap className="w-8 h-8 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Success Rate</p>
              <p className="text-2xl font-bold text-foreground">{stats.successRate}%</p>
            </div>
            <Activity className="w-8 h-8 text-muted-foreground" />
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="performance" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="tools">Tool Usage</TabsTrigger>
          <TabsTrigger value="memory">Memory</TabsTrigger>
        </TabsList>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Response Time & Token Usage
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="responseTime"
                  stroke="#8884d8"
                  name="Response Time (s)"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="tokens"
                  stroke="#82ca9d"
                  name="Tokens Used"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        {/* Tool Usage Tab */}
        <TabsContent value="tools" className="space-y-4">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Tool Execution Statistics
            </h3>
            <div className="space-y-4">
              {toolUsage.map((tool) => (
                <div key={tool.name} className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-foreground">{tool.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {tool.count} executions
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-32 bg-muted rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{ width: `${tool.successRate}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-foreground w-12">
                      {tool.successRate}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>

        {/* Memory Tab */}
        <TabsContent value="memory" className="space-y-4">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Memory Usage
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-foreground">System Memory</p>
                  <p className="text-sm text-muted-foreground">{stats.memoryUsage}%</p>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full"
                    style={{ width: `${stats.memoryUsage}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-6">
                <Card className="p-4 bg-muted">
                  <p className="text-xs text-muted-foreground">Total Tokens Used</p>
                  <p className="text-xl font-bold text-foreground">
                    {(stats.totalTokensUsed / 1000).toFixed(1)}K
                  </p>
                </Card>
                <Card className="p-4 bg-muted">
                  <p className="text-xs text-muted-foreground">Conversations Stored</p>
                  <p className="text-xl font-bold text-foreground">
                    {stats.totalConversations}
                  </p>
                </Card>
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Recent Activity */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">
          Recent Activity
        </h3>
        <div className="space-y-3">
          {[
            { time: '2 minutes ago', action: 'Executed command: git status', status: 'success' },
            { time: '5 minutes ago', action: 'Retrieved 5 memories for context', status: 'success' },
            { time: '8 minutes ago', action: 'Completed conversation analysis', status: 'success' },
            { time: '12 minutes ago', action: 'Failed to connect to external API', status: 'error' },
            { time: '15 minutes ago', action: 'Stored new memory: Project setup', status: 'success' },
          ].map((activity, idx) => (
            <div key={idx} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-3">
                {activity.status === 'success' ? (
                  <Activity className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                )}
                <p className="text-foreground">{activity.action}</p>
              </div>
              <p className="text-muted-foreground">{activity.time}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
