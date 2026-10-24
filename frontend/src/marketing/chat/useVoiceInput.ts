import { useCallback, useEffect, useRef, useState } from 'react';

type SpeechResult = { isFinal: boolean; 0: { transcript: string } };
type Recognition = { lang: string; interimResults: boolean; continuous: boolean; onresult: ((event: { results: ArrayLike<SpeechResult> }) => void) | null; onerror: (() => void) | null; onend: (() => void) | null; start: () => void; stop: () => void; abort: () => void };
type SpeechWindow = Window & { SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition };
export function useVoiceInput(language: string, onText: (text: string) => void, onError: (text: string) => void, denied: string) {
  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const recognition = useRef<Recognition | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const media = useRef<MediaStream | null>(null);
  const cancelled = useRef(false);
  const uploadController = useRef<AbortController | null>(null);
  const stop = useCallback((cancel = false) => {
    cancelled.current = cancel;
    if (cancel) recognition.current?.abort(); else recognition.current?.stop();
    if (recorder.current?.state === 'recording') recorder.current.stop();
    media.current?.getTracks().forEach(track => track.stop()); media.current = null;
    if (cancel) uploadController.current?.abort();
    setRecording(false);
  }, []);
  useEffect(() => () => { stop(true); }, [stop]);
  useEffect(() => {
    if (!recording) return;
    const timer = window.setInterval(() => setSeconds(s => s+1), 1000);
    return () => clearInterval(timer);
  }, [recording]);
  useEffect(() => { if (seconds >= 60 && recording) stop(); }, [seconds, recording, stop]);
  async function start() {
    if (!window.isSecureContext) { onError(denied); return; }
    cancelled.current = false; setSeconds(0);
    const Constructor = (window as SpeechWindow).SpeechRecognition || (window as SpeechWindow).webkitSpeechRecognition;
    try {
      if (Constructor) {
        const instance = new Constructor(); recognition.current = instance;
        instance.lang = 'en-GB'; instance.interimResults = true; instance.continuous = true;
        instance.onresult = event => onText(Array.from(event.results).map(result => result[0].transcript).join(' ').slice(0, 2000));
        instance.onerror = () => { onError(denied); stop(true); };
        instance.onend = () => setRecording(false);
        instance.start(); setRecording(true);
      } else {
        if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { onError(denied); return; }
        media.current = await navigator.mediaDevices.getUserMedia({ audio: true });
        if (cancelled.current) { media.current.getTracks().forEach(track => track.stop()); return; }
        const instance = new MediaRecorder(media.current); recorder.current = instance;
        const chunks: BlobPart[] = [];
        instance.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
        instance.onstop = async () => {
          media.current?.getTracks().forEach(track => track.stop());
          if (cancelled.current) return;
          const form = new FormData(); form.append('file', new Blob(chunks, { type: instance.mimeType }), 'recording.webm'); form.append('consent', 'true'); form.append('language', language);
          uploadController.current = new AbortController();
          try { const response = await fetch('/api/public/assistant/transcribe', { method: 'POST', body: form, signal: uploadController.current.signal }); const data = await response.json(); if (!response.ok) throw new Error(data.message || denied); onText(data.text); }
          catch (e) { if (!cancelled.current) onError(e instanceof Error ? e.message : denied); }
        };
        instance.start(); setRecording(true);
      }
    } catch { onError(denied); stop(true); }
  }
  return { recording, seconds, start, stop };
}
