import { useEffect, useMemo, useRef } from 'react';
import type { AgentEvent, AgentTrace, RagRuntimeStatus, VoiceTurn } from '../services/api';

type Props = {
  turn: VoiceTurn | null;
  status: RagRuntimeStatus | null;
  events?: AgentEvent[];
};

type FlowNode = {
  id: string;
  label: string;
  kind: 'user' | 'agent' | 'provider' | 'store' | 'output';
  x: number;
  y: number;
};

const nodes: FlowNode[] = [
  { id: 'user', label: 'User', kind: 'user', x: 0.08, y: 0.48 },
  { id: 'lead', label: 'Lead', kind: 'agent', x: 0.22, y: 0.22 },
  { id: 'search', label: 'Search', kind: 'agent', x: 0.38, y: 0.22 },
  { id: 'vector-db', label: 'Vector DB', kind: 'store', x: 0.38, y: 0.68 },
  { id: 'rerank', label: 'Rerank', kind: 'provider', x: 0.54, y: 0.22 },
  { id: 'review', label: 'Review', kind: 'agent', x: 0.68, y: 0.42 },
  { id: 'teacher', label: 'Teacher', kind: 'agent', x: 0.82, y: 0.22 },
  { id: 'riva', label: 'Riva TTS', kind: 'provider', x: 0.82, y: 0.68 },
  { id: 'avatar', label: 'Avatar', kind: 'output', x: 0.94, y: 0.48 },
];

const edges: [string, string][] = [
  ['user', 'lead'],
  ['lead', 'search'],
  ['search', 'vector-db'],
  ['vector-db', 'search'],
  ['search', 'rerank'],
  ['rerank', 'review'],
  ['review', 'search'],
  ['review', 'teacher'],
  ['teacher', 'riva'],
  ['riva', 'avatar'],
  ['teacher', 'avatar'],
];

const colors = {
  user: '#67e8f9',
  agent: '#4ade80',
  provider: '#facc15',
  store: '#60a5fa',
  output: '#f472b6',
};

export function AgentTraceCanvas({ turn, status, events = [] }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const traceByAgent = useMemo(() => {
    const map = new Map<string, AgentTrace>();
    turn?.agentTrace.forEach((trace) => map.set(trace.agent, trace));
    return map;
  }, [turn]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext('2d');
    if (!canvas || !context) {
      return;
    }

    let frameId = 0;
    const render = (time: number) => {
      const rect = canvas.getBoundingClientRect();
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      const width = Math.max(640, Math.floor(rect.width * dpr));
      const height = Math.max(320, Math.floor(rect.height * dpr));
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }

      context.clearRect(0, 0, width, height);
      drawGrid(context, width, height, time);
      drawEdges(context, width, height, time, events);
      drawNodes(context, width, height, time, traceByAgent, status);
      frameId = requestAnimationFrame(render);
    };

    frameId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(frameId);
  }, [events, status, traceByAgent]);

  return (
    <div className="agentCanvasShell">
      <canvas ref={canvasRef} aria-label="Animated agent flow canvas" />
      <div className="agentCanvasLegend" aria-label="Agent flow status">
        <span>User question</span>
        <span>Lead intent</span>
        <span>Search + vector DB</span>
        <span>Review loop</span>
        <span>Teacher + Riva + avatar</span>
      </div>
    </div>
  );
}

function drawGrid(context: CanvasRenderingContext2D, width: number, height: number, time: number) {
  context.fillStyle = '#050a11';
  context.fillRect(0, 0, width, height);
  context.strokeStyle = 'rgba(74, 222, 128, 0.08)';
  context.lineWidth = 1;
  for (let x = 0; x < width; x += 72) {
    context.beginPath();
    context.moveTo(x, 0);
    context.lineTo(x, height);
    context.stroke();
  }
  for (let y = 0; y < height; y += 72) {
    context.beginPath();
    context.moveTo(0, y);
    context.lineTo(width, y);
    context.stroke();
  }

  for (let i = 0; i < 26; i += 1) {
    const x = (i * 127 + time * 0.018) % width;
    const y = (i * 61 + Math.sin(time * 0.001 + i) * 18 + height) % height;
    context.fillStyle = i % 3 === 0 ? 'rgba(103, 232, 249, 0.48)' : 'rgba(74, 222, 128, 0.34)';
    context.beginPath();
    context.arc(x, y, 1.7, 0, Math.PI * 2);
    context.fill();
  }
}

function drawEdges(context: CanvasRenderingContext2D, width: number, height: number, time: number, events: AgentEvent[]) {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const activeKeys = new Set(events.map((event) => `${event.agent}:${event.target ?? ''}`));
  edges.forEach(([fromId, toId], index) => {
    const from = byId.get(fromId);
    const to = byId.get(toId);
    if (!from || !to) {
      return;
    }
    const start = point(from, width, height);
    const end = point(to, width, height);
    const isLoop = fromId === 'review' && toId === 'search';
    const active = activeKeys.size === 0 || activeKeys.has(`${fromId}:${toId}`);
    const midX = (start.x + end.x) / 2;
    const midY = (start.y + end.y) / 2 + (isLoop ? 120 : 0);

    context.strokeStyle = active ? (isLoop ? 'rgba(250, 204, 21, 0.42)' : 'rgba(103, 232, 249, 0.28)') : 'rgba(148, 163, 184, 0.1)';
    context.lineWidth = active ? (isLoop ? 2 : 1.4) : 1;
    context.setLineDash([7, 10]);
    context.lineDashOffset = -(time * 0.035 + index * 7);
    context.beginPath();
    context.moveTo(start.x, start.y);
    context.quadraticCurveTo(midX, midY, end.x, end.y);
    context.stroke();
    context.setLineDash([]);

    const particleCount = active ? 3 : 1;
    for (let particle = 0; particle < particleCount; particle += 1) {
      const progress = (time * 0.00018 + particle / 3 + index * 0.07) % 1;
      const dot = quadratic(start, { x: midX, y: midY }, end, progress);
      context.fillStyle = active ? (isLoop ? 'rgba(250, 204, 21, 0.9)' : 'rgba(74, 222, 128, 0.9)') : 'rgba(148, 163, 184, 0.25)';
      context.beginPath();
      context.arc(dot.x, dot.y, isLoop ? 3.2 : 2.6, 0, Math.PI * 2);
      context.fill();
    }
  });
}

function drawNodes(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  time: number,
  traceByAgent: Map<string, AgentTrace>,
  status: RagRuntimeStatus | null,
) {
  nodes.forEach((node) => {
    const { x, y } = point(node, width, height);
    const color = colors[node.kind];
    const trace = traceByAgent.get(node.id);
    const active = node.id === 'user' || node.id === 'avatar' || Boolean(trace) || node.id === 'vector-db' || node.id === 'riva';
    const pulse = active ? 4 + Math.sin(time * 0.004 + x) * 2 : 0;
    const radius = node.kind === 'store' ? 42 : 34;

    context.fillStyle = active ? `${color}22` : 'rgba(148, 163, 184, 0.08)';
    context.strokeStyle = active ? color : 'rgba(148, 163, 184, 0.24)';
    context.lineWidth = active ? 2 : 1;
    context.beginPath();
    context.roundRect(x - radius - pulse, y - 25 - pulse, (radius + pulse) * 2, 50 + pulse * 2, 12);
    context.fill();
    context.stroke();

    context.fillStyle = active ? '#f8fafc' : '#94a3b8';
    context.font = `700 ${Math.max(12, width * 0.014)}px Inter, system-ui, sans-serif`;
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(node.label, x, y - 6);

    context.fillStyle = active ? color : '#64748b';
    context.font = `600 ${Math.max(10, width * 0.011)}px Inter, system-ui, sans-serif`;
    context.fillText(labelForNode(node, trace, status), x, y + 14);
  });
}

function labelForNode(node: FlowNode, trace: AgentTrace | undefined, status: RagRuntimeStatus | null): string {
  if (trace) {
    return trace.status;
  }
  if (node.id === 'vector-db') {
    return `${status?.chunkCount ?? 0} chunks`;
  }
  if (node.id === 'riva') {
    return 'tts';
  }
  if (node.id === 'avatar') {
    return 'timeline';
  }
  return node.kind;
}

function point(node: FlowNode, width: number, height: number) {
  return { x: node.x * width, y: node.y * height };
}

function quadratic(start: { x: number; y: number }, control: { x: number; y: number }, end: { x: number; y: number }, t: number) {
  const oneMinus = 1 - t;
  return {
    x: oneMinus * oneMinus * start.x + 2 * oneMinus * t * control.x + t * t * end.x,
    y: oneMinus * oneMinus * start.y + 2 * oneMinus * t * control.y + t * t * end.y,
  };
}
