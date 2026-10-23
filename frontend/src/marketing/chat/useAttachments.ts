import { useEffect, useRef, useState } from 'react';
import type { Attachment } from './types';

export function useAttachments(error: (text: string) => void, tooMany: string) {
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const controllers = useRef(new Map<string, AbortController>());
  const urls = useRef(new Set<string>());
  useEffect(() => () => { controllers.current.forEach(c => c.abort()); urls.current.forEach(url => URL.revokeObjectURL(url)); }, []);
  async function upload(item: Attachment) {
    const controller = new AbortController(); controllers.current.set(item.id, controller);
    const form = new FormData(); if (!item.file) return; form.append('file', item.file); form.append('consent', 'true');
    setAttachments(items => items.map(a => a.id === item.id ? { ...a, status: 'uploading', error: undefined, progress: 20 } : a));
    try {
      const response = await fetch('/api/public/assistant/upload', { method: 'POST', body: form, signal: controller.signal });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || 'Upload failed');
      setAttachments(items => items.map(a => a.id === item.id ? { ...a, id: data.attachment_id, status: 'ready', progress: 100 } : a));
    } catch (e) { if (!controller.signal.aborted) setAttachments(items => items.map(a => a.id === item.id ? { ...a, status: 'error', error: e instanceof Error ? e.message : 'Upload failed' } : a)); }
    finally { controllers.current.delete(item.id); }
  }
  function add(files: FileList | File[], consent: boolean) {
    if (!consent) { error('Please confirm temporary file processing first.'); return; }
    const selected = Array.from(files);
    if (selected.length+attachments.length > 5 || selected.some(f => f.size > 10*1024*1024)) { error(tooMany); return; }
    const fresh = selected.map(file => {
      const url = file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined;
      if (url) urls.current.add(url);
      return { id: crypto.randomUUID(), file, name: file.name, size: file.size, mime: file.type, url, status: 'uploading' as const, progress: 0 };
    });
    setAttachments(items => [...items, ...fresh]); fresh.forEach(item => void upload(item));
  }
  function remove(id: string) {
    controllers.current.get(id)?.abort();
    setAttachments(items => items.filter(item => item.id !== id));
    void fetch(`/api/public/assistant/upload/${encodeURIComponent(id)}`, { method: 'DELETE' }).catch(() => {});
  }
  function clear() { attachments.forEach(a => remove(a.id)); setAttachments([]); }
  function consume() { const ready = attachments.map(item => ({ id: item.id, name: item.name, mime: item.mime, size: item.size, url: item.url, status: item.status, progress: item.progress })); setAttachments([]); return ready; }
  return { attachments, add, remove, clear, consume, retry: upload };
}
