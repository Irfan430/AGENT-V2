import "dotenv/config";
import express from "express";
import { createServer } from "http";
import net from "net";
import { createExpressMiddleware } from "@trpc/server/adapters/express";
import { registerOAuthRoutes } from "./oauth";
import { appRouter } from "../routers";
import { createContext } from "./context";
import { serveStatic, setupVite } from "./vite";

function isPortAvailable(port: number): Promise<boolean> {
  return new Promise(resolve => {
    const server = net.createServer();
    server.listen(port, () => {
      server.close(() => resolve(true));
    });
    server.on("error", () => resolve(false));
  });
}

async function findAvailablePort(startPort: number = 3000): Promise<number> {
  for (let port = startPort; port < startPort + 20; port++) {
    if (await isPortAvailable(port)) {
      return port;
    }
  }
  throw new Error(`No available port found starting from ${startPort}`);
}

async function startServer() {
  const app = express();
  const server = createServer(app);

  app.use(express.json({ limit: "50mb" }));
  app.use(express.urlencoded({ limit: "50mb", extended: true }));

  // 🔥 DEV MODE AUTH BYPASS
  const isDev = process.env.NODE_ENV === "development";
  const authDisabled = process.env.AUTH_DISABLED === "true";

  if (!authDisabled) {
    registerOAuthRoutes(app);
  } else {
    console.log("⚠️  AUTH DISABLED (Development Mode) — using dev-user context");
  }

  app.use(
    "/api/trpc",
    createExpressMiddleware({
      router: appRouter,
      createContext: (opts) => {
        if (authDisabled) {
          // Return complete context with mock user for dev mode
          return {
            req: opts.req,
            res: opts.res,
            user: {
              id: 1,
              openId: "dev-user",
              name: "Local Dev User",
              email: "dev@local.host",
              loginMethod: "dev",
              role: "admin" as const,
              createdAt: new Date(),
              updatedAt: new Date(),
              lastSignedIn: new Date(),
            },
          };
        }
        return createContext(opts);
      },
    })
  );

  if (isDev) {
    await setupVite(app, server);
  } else {
    serveStatic(app);
  }

  const preferredPort = parseInt(process.env.PORT || "3000");
  const port = await findAvailablePort(preferredPort);

  if (port !== preferredPort) {
    console.log(`Port ${preferredPort} is busy, using port ${port} instead`);
  }

  server.listen(port, () => {
    console.log(`\n🚀 AGENT-V2 running at http://localhost:${port}/`);
    console.log(`   Frontend  → http://localhost:${port}/`);
    console.log(`   Chat      → http://localhost:${port}/chat`);
    console.log(`   Dashboard → http://localhost:${port}/dashboard`);
    console.log(`   Settings  → http://localhost:${port}/settings`);
    console.log(`   tRPC API  → http://localhost:${port}/api/trpc`);
    console.log(`   Python Agent → http://localhost:8001 (start separately or use pnpm dev:all)\n`);
  });
}

startServer().catch(console.error);