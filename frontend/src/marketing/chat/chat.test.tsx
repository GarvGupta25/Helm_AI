import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MarkdownReply } from './MarkdownReply';
import { streamChat } from './useChatStream';

afterEach(() => vi.restoreAllMocks());
describe('untrusted message rendering', () => {
  it('renders useful formatting without executable HTML or unsafe links', () => {
    const { container } = render(<MarkdownReply text={'**Excess**\n\n- A contribution\n\n<script>bad()</script>\n\n[bad](javascript:alert(1))\n\n[Guide](/guides)\n\n![tracking](https://example.invalid/pixel)'}/>);
    expect(screen.getByText('Excess').tagName).toBe('STRONG');
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('img')).toBeNull();
    expect(container.querySelector('[href^="javascript"]')).toBeNull();
    expect(screen.getByRole('link', { name: 'Guide' }).getAttribute('rel')).toBe('noopener noreferrer');
  });
  it('renders bounded pipe tables with text cells', () => {
    render(<MarkdownReply text={'| Benefit | Limit |\n| --- | --- |\n| Outpatient | £500 |\n'}/>);
    expect(screen.getByRole('columnheader', { name: 'Benefit' })).toBeTruthy();
    expect(screen.getByRole('cell', { name: '£500' })).toBeTruthy();
  });
});

describe('SSE transport', () => {
  it('buffers fragmented UTF-8 frames and emits done once', async () => {
    const bytes = new TextEncoder().encode('event: token\ndata: {"text":"£500"}\n\nevent: done\ndata: {}\n\n');
    const body = new ReadableStream({ start(controller) { controller.enqueue(bytes.slice(0, bytes.indexOf(0xc2)+1)); controller.enqueue(bytes.slice(bytes.indexOf(0xc2)+1)); controller.close(); } });
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(body, { status: 200 }));
    const events: string[] = [];
    await streamChat({ message: 'excess', attachments: [], language: 'en' }, new AbortController().signal, (type, data) => events.push(`${type}:${data.text || ''}`));
    expect(events).toEqual(['token:£500', 'done:']);
  });
  it('reports interrupted streams instead of silently claiming completion', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('event: token\ndata: {"text":"partial"}\n\n'));
    await expect(streamChat({ message: 'excess', attachments: [], language: 'en' }, new AbortController().signal, () => {})).rejects.toThrow('ended early');
  });
  it('does not silently discard attachments during fallback', async () => {
    const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 404 }));
    await expect(streamChat({ message: 'excess', attachments: ['secret'], language: 'en' }, new AbortController().signal, () => {})).rejects.toThrow('Remove the files');
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});
