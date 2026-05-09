#!/usr/bin/env bun
/**
 * Smoke test that exercises the real Sloppy consumer/provider boundary against
 * a running SloppyTron SLOP provider.
 */

import { existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

type SlopNode = {
  id: string;
  type: string;
  properties?: Record<string, unknown>;
  children?: SlopNode[];
  affordances?: Array<{ action: string; dangerous?: boolean }>;
};

type InvokeResult = {
  status: "ok" | "error" | "accepted";
  data?: unknown;
  error?: { code: string; message: string };
};

type Args = {
  providerId: string;
  pan: number;
  tilt: number;
  sloppyRepo: string;
};

function usage(): string {
  return [
    "Usage: bun run docker/sloppy-consumer-smoke.ts [options]",
    "",
    "Options:",
    "  --provider-id <id>   Sloppy provider id to exercise; default: body",
    "  --pan <deg>          look_at_angles pan target; default: 10",
    "  --tilt <deg>         look_at_angles tilt target; default: -5",
    "  --sloppy-repo <dir>  Sloppy source repo; default: $SLOPPY_REPO or /opt/sloppy",
    "  -h, --help           show this help",
    "",
  ].join("\n");
}

function takeValue(args: string[], index: number, flag: string): string {
  const value = args[index + 1];
  if (!value || value.startsWith("--")) {
    throw new Error(`${flag} requires a value.`);
  }
  return value;
}

function parseArgs(argv: string[]): Args & { help: boolean } {
  const parsed: Args & { help: boolean } = {
    providerId: process.env.SLOPPY_CONSUMER_PROVIDER_ID ?? "body",
    pan: Number.parseFloat(process.env.SLOPPY_CONSUMER_PAN ?? "10"),
    tilt: Number.parseFloat(process.env.SLOPPY_CONSUMER_TILT ?? "-5"),
    sloppyRepo: resolve(process.env.SLOPPY_REPO ?? "/opt/sloppy"),
    help: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    switch (arg) {
      case "-h":
      case "--help":
        parsed.help = true;
        break;
      case "--provider-id":
        parsed.providerId = takeValue(argv, index, arg);
        index += 1;
        break;
      case "--pan":
        parsed.pan = Number.parseFloat(takeValue(argv, index, arg));
        index += 1;
        break;
      case "--tilt":
        parsed.tilt = Number.parseFloat(takeValue(argv, index, arg));
        index += 1;
        break;
      case "--sloppy-repo":
        parsed.sloppyRepo = resolve(takeValue(argv, index, arg));
        index += 1;
        break;
      default:
        throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!Number.isFinite(parsed.pan) || !Number.isFinite(parsed.tilt)) {
    throw new Error("--pan and --tilt must be finite numbers.");
  }

  return parsed;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function hasAffordance(node: SlopNode, action: string): boolean {
  return node.affordances?.some((affordance) => affordance.action === action) ?? false;
}

function requireCondition(condition: unknown, message: string, payload?: unknown): void {
  if (condition) {
    return;
  }
  const suffix = payload === undefined ? "" : `\n${JSON.stringify(payload, null, 2)}`;
  throw new Error(`${message}${suffix}`);
}

function requireOk(result: InvokeResult, label: string): InvokeResult {
  if (result.status === "error") {
    throw new Error(`${label} failed: ${result.error?.message ?? "unknown error"}`);
  }
  return result;
}

function providerDirs(): string[] {
  const configured = process.env.SLOPPY_PROVIDER_DIRS ?? process.env.SLOPPY_PROVIDER_DIR;
  const entries = configured?.split(":") ?? ["/root/.slop/providers", "/tmp/slop/providers"];
  return [...new Set(entries.filter(Boolean).map((entry) => resolve(entry)))];
}

async function loadSloppyModules(sloppyRepo: string): Promise<{
  sloppyConfigSchema: { parse(value: unknown): unknown };
  createRegisteredProviders: (config: unknown) => Promise<unknown[]>;
  ConsumerHub: new (providers: unknown[], config: unknown) => {
    connect(): Promise<void>;
    shutdown(): void;
    getExternalProviderStates(): Array<Record<string, unknown>>;
    queryState(options: Record<string, unknown>): Promise<SlopNode>;
    invoke(
      providerId: string,
      path: string,
      action: string,
      params?: Record<string, unknown>,
    ): Promise<InvokeResult>;
  };
}> {
  const schemaPath = join(sloppyRepo, "src/config/schema.ts");
  const registryPath = join(sloppyRepo, "src/providers/registry.ts");
  const consumerPath = join(sloppyRepo, "src/core/consumer.ts");

  for (const path of [schemaPath, registryPath, consumerPath]) {
    if (!existsSync(path)) {
      throw new Error(
        `Missing Sloppy source file: ${path}. Mount the Sloppy repo at /opt/sloppy or set SLOPPY_REPO.`,
      );
    }
  }

  const schemaModule = await import(pathToFileURL(schemaPath).href);
  const registryModule = await import(pathToFileURL(registryPath).href);
  const consumerModule = await import(pathToFileURL(consumerPath).href);

  return {
    sloppyConfigSchema: schemaModule.sloppyConfigSchema,
    createRegisteredProviders: registryModule.createRegisteredProviders,
    ConsumerHub: consumerModule.ConsumerHub,
  };
}

function buildSmokeConfig(sloppyConfigSchema: { parse(value: unknown): unknown }): unknown {
  return sloppyConfigSchema.parse({
    llm: {
      provider: "openai",
      model: "smoke-no-llm",
      profiles: [],
      maxTokens: 4096,
    },
    agent: {
      maxIterations: 4,
      minSalience: 0,
      overviewDepth: 2,
      overviewMaxNodes: 300,
      detailDepth: 4,
      detailMaxNodes: 300,
      historyTurns: 2,
      toolResultMaxChars: 16000,
    },
    plugins: {
      "persistent-goal": { enabled: false },
      terminal: { enabled: false },
      filesystem: { enabled: false },
      memory: { enabled: false },
      skills: { enabled: false },
      "meta-runtime": { enabled: false },
      web: { enabled: false },
      browser: { enabled: false },
      cron: { enabled: false },
      messaging: { enabled: false },
      delegation: { enabled: false },
      spec: { enabled: false },
      vision: { enabled: false },
      mcp: { enabled: false },
      workspaces: { enabled: false },
      a2a: { enabled: false },
    },
    providers: {
      discovery: {
        enabled: true,
        paths: providerDirs(),
      },
    },
  });
}

async function main(): Promise<void> {
  const args = parseArgs(Bun.argv.slice(2));
  if (args.help) {
    process.stdout.write(usage());
    return;
  }

  const { sloppyConfigSchema, createRegisteredProviders, ConsumerHub } = await loadSloppyModules(
    args.sloppyRepo,
  );
  const config = buildSmokeConfig(sloppyConfigSchema);
  const providers = await createRegisteredProviders(config);
  const provider = providers.find((candidate) => asRecord(candidate).id === args.providerId);
  requireCondition(provider, `Provider ${args.providerId} was not discovered.`, {
    providerDirs: providerDirs(),
    discoveredProviders: providers.map((candidate) => asRecord(candidate).id),
  });

  const hub = new ConsumerHub(providers, config);
  try {
    await hub.connect();
    const externalStates = hub.getExternalProviderStates();
    const bodyState = externalStates.find((state) => state.id === args.providerId);
    requireCondition(bodyState?.status === "connected", `Provider ${args.providerId} did not connect.`, {
      externalStates,
    });

    const root = await hub.queryState({ providerId: args.providerId, path: "/", depth: 2 });
    requireCondition(
      root.children?.some((child) => child.id === "body"),
      "Provider root does not expose /body.",
      root,
    );

    const body = await hub.queryState({ providerId: args.providerId, path: "/body", depth: 1 });
    requireCondition(body.properties?.name === "Reachy Mini", "Unexpected /body identity.", body);

    let safety = await hub.queryState({ providerId: args.providerId, path: "/safety", depth: 1 });
    let enableResult: InvokeResult | { status: "skipped"; reason: string } = {
      status: "skipped",
      reason: "motion already enabled",
    };
    if (safety.properties?.motionEnabled !== true) {
      requireCondition(
        hasAffordance(safety, "enable_motion"),
        "/safety does not expose enable_motion while motion is disabled.",
        safety,
      );
      enableResult = requireOk(
        await hub.invoke(args.providerId, "/safety", "enable_motion", {}),
        "enable_motion",
      );
      safety = await hub.queryState({ providerId: args.providerId, path: "/safety", depth: 1 });
      requireCondition(safety.properties?.motionEnabled === true, "Motion did not become enabled.", safety);
    }

    const poseBefore = await hub.queryState({ providerId: args.providerId, path: "/pose", depth: 1 });
    requireCondition(
      hasAffordance(poseBefore, "look_at_angles"),
      "/pose does not expose look_at_angles after motion enablement.",
      poseBefore,
    );
    const lookResult = requireOk(
      await hub.invoke(args.providerId, "/pose", "look_at_angles", {
        pan: args.pan,
        tilt: args.tilt,
      }),
      "look_at_angles",
    );

    const tasks = await hub.queryState({ providerId: args.providerId, path: "/tasks", depth: 3 });
    const taskIds = tasks.children?.map((child) => child.id) ?? [];
    const lookTaskId = asRecord(lookResult.data).taskId;
    requireCondition(
      typeof lookTaskId === "string" || taskIds.length > 0,
      "look_at_angles returned no task id and /tasks is empty.",
      { lookResult, tasks },
    );

    const poseAfter = await hub.queryState({ providerId: args.providerId, path: "/pose", depth: 1 });
    requireCondition(
      typeof asRecord(poseAfter.properties?.head).pan === "number" &&
        typeof asRecord(poseAfter.properties?.head).tilt === "number",
      "Final /pose does not expose numeric head pan/tilt.",
      poseAfter,
    );

    process.stdout.write(
      `${JSON.stringify(
        {
          provider: bodyState,
          body: body.properties,
          rootChildren: root.children?.map((child) => child.id) ?? [],
          enableResult,
          lookResult,
          taskIds,
          finalPose: poseAfter.properties,
        },
        null,
        2,
      )}\n`,
    );
  } finally {
    hub.shutdown();
  }
}

try {
  await main();
} catch (error) {
  process.stderr.write(`[sloppy-consumer-smoke] ${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 1;
}
