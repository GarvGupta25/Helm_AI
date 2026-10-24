import { useCallback, useEffect, useRef, useState } from 'react';

export function useReadAloud(open: boolean, onNotice: (text: string) => void) {
  const [speakingId, setSpeakingId] = useState('');
  const generation = useRef(0);
  const supported = typeof window.speechSynthesis !== 'undefined' && typeof window.SpeechSynthesisUtterance !== 'undefined';
  const stop = useCallback(() => { generation.current++; window.speechSynthesis?.cancel(); setSpeakingId(''); }, []);
  useEffect(() => { if (!open) stop(); return () => { generation.current++; window.speechSynthesis?.cancel(); }; }, [open, stop]);
  function read(id: string, text: string) {
    if (!supported) { onNotice('Read aloud is unavailable in this browser. You can copy the answer instead.'); return; }
    const same = speakingId === id;
    stop();
    if (same) return;
    const current = generation.current;
    const plain = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/[*#`|]/g, '').trim();
    const chunks = plain.match(/.{1,170}(?:\s|$)|\S{1,170}/gs) || [];
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(v => v.localService && v.lang.startsWith('en')) || voices.find(v => v.lang.startsWith('en'));
    setSpeakingId(id);
    chunks.forEach((chunk, index) => {
      const speech = new SpeechSynthesisUtterance(chunk);
      speech.lang = 'en-GB'; if (voice) speech.voice = voice;
      speech.onend = () => { if (generation.current === current && index === chunks.length-1) setSpeakingId(''); };
      speech.onerror = () => { if (generation.current === current) { stop(); onNotice('Reading stopped. Try again or choose another browser voice.'); } };
      window.speechSynthesis.speak(speech);
    });
  }
  return { read, stop, speakingId, supported };
}
