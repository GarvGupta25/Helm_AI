import type { StreamEvent } from './types';

export async function streamChat(body: { message: string; attachments: string[]; language: string }, signal: AbortSignal, event: (type: string, data: StreamEvent) => void) {
  const response = await fetch('/api/public/assistant/stream', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal });
  if ([404, 405, 501].includes(response.status) || !response.body) {
    if (body.attachments.length) throw new Error('Attachments need the streaming service. Remove the files and try text only.');
    const fallback = await fetch('/api/public/assistant/messages', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: body.message.slice(0, 500) }), signal });
    if (!fallback.ok) throw new Error(fallback.status === 429 ? 'RATE_LIMIT' : 'Assistant unavailable');
    const data = await fallback.json();
    event('token', { text: data.reply }); event('done', {}); return;
  }
  if (!response.ok) {
    if (response.status === 429) throw new Error('RATE_LIMIT');
    const data = await response.json(); throw new Error(data.message || 'Assistant unavailable');
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let doneEvent = false;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replaceAll('\r\n', '\n');
    let end: number;
    while ((end = buffer.indexOf('\n\n')) >= 0) {
      const block = buffer.slice(0, end); buffer = buffer.slice(end+2);
      const type = block.split('\n').find(line => line.startsWith('event:'))?.slice(6).trim() || 'message';
      const data = block.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trim()).join('\n');
      if (data) { event(type, JSON.parse(data) as StreamEvent); if (type === 'done') doneEvent = true; }
    }
  }
  if (!doneEvent) throw new Error('The connection ended early. Retry to receive the complete answer.');
}
