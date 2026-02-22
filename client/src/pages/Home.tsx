import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Brain, Zap, Database, Code2, MessageSquare, Settings } from "lucide-react";
import { useLocation } from "wouter";

export default function Home() {
  const { user, isAuthenticated } = useAuth();
  const [, navigate] = useLocation();

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted">
      {/* Navigation */}
      <nav className="border-b border-border">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-primary" />
            <h1 className="text-xl font-bold text-foreground">Manus Agent Pro</h1>
          </div>
          <div className="flex items-center gap-4">
            {isAuthenticated && (
              <span className="text-sm text-muted-foreground">Welcome, {user?.name}</span>
            )}
            <Button variant="ghost" size="sm" onClick={() => navigate('/settings')}>
              <Settings className="w-4 h-4 mr-1" /> Settings
            </Button>
            <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard')}>
              Dashboard
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 py-20">
        <div className="text-center space-y-6 mb-16">
          <Badge className="mx-auto">Autonomous AI Agent</Badge>
          <h2 className="text-5xl font-bold text-foreground">
            Meet Your Autonomous AI Agent
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            A powerful, self-correcting AI agent that can think, act, and learn from its actions.
            Execute commands, manage files, browse the web, and more autonomously.
          </p>
          <div className="flex gap-4 justify-center pt-4">
            <Button size="lg" onClick={() => navigate("/chat")}>
              Start Chatting
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate("/dashboard")}>
              View Dashboard
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <h3 className="text-3xl font-bold text-foreground mb-12 text-center">
          Powerful Capabilities
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="text-primary mb-4">
              <Brain className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-semibold text-foreground mb-2">
              Autonomous Thinking
            </h4>
            <p className="text-muted-foreground">
              Thought-Action-Observation-Reflection workflow for intelligent decision-making
            </p>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="text-primary mb-4">
              <Zap className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-semibold text-foreground mb-2">
              Tool Execution
            </h4>
            <p className="text-muted-foreground">
              Execute shell commands, manage files, and interact with external systems
            </p>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="text-primary mb-4">
              <Code2 className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-semibold text-foreground mb-2">
              Code Generation
            </h4>
            <p className="text-muted-foreground">
              Generate, analyze, and execute code with built-in error handling
            </p>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="text-primary mb-4">
              <Database className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-semibold text-foreground mb-2">
              Long-term Memory
            </h4>
            <p className="text-muted-foreground">
              ChromaDB-powered vector memory with RAG for context-aware responses
            </p>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="text-primary mb-4">
              <MessageSquare className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-semibold text-foreground mb-2">
              Natural Conversation
            </h4>
            <p className="text-muted-foreground">
              Real-time streaming responses with markdown rendering and code highlighting
            </p>
          </Card>

          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="text-primary mb-4">
              <Zap className="w-6 h-6" />
            </div>
            <h4 className="text-lg font-semibold text-foreground mb-2">
              Self-Correction
            </h4>
            <p className="text-muted-foreground">
              Automatic error detection and recovery with reflection-based learning
            </p>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-6xl mx-auto px-4 py-16 text-center">
        <Card className="p-12 bg-primary/5 border-primary/20">
          <h3 className="text-2xl font-bold text-foreground mb-4">
            Ready to experience autonomous AI?
          </h3>
          <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
            Start a conversation with the agent and watch it solve problems, execute tasks,
            and learn from its actions in real-time.
          </p>
          <Button size="lg" onClick={() => navigate("/chat")}>
            Launch Agent Chat
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t border-border mt-20">
        <div className="max-w-6xl mx-auto px-4 py-8 text-center text-muted-foreground">
          <p>Manus Agent Pro v1.0.0 | Powered by DeepSeek-V3 and ChromaDB</p>
        </div>
      </footer>
    </div>
  );
}
