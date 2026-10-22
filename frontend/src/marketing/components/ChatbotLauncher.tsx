import { useEffect, useRef, useState } from 'react';
import { MessageCircle, X } from 'lucide-react';
import type { DotLottie } from '@lottiefiles/dotlottie-web';
import { ChatPanel } from './ChatPanel';
import './ChatbotLauncher.css';

export function ChatbotLauncher() {
  const canvas = useRef<HTMLCanvasElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const greetingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [animated, setAnimated] = useState(false);
  const [showGreeting, setShowGreeting] = useState(false);
  useEffect(() => {
    try { if (sessionStorage.getItem('helm-greeting-dismissed') === 'yes') return; } catch { /* Storage may be unavailable. */ }
    greetingTimer.current = setTimeout(() => setShowGreeting(true), 3000);
    return () => { if (greetingTimer.current) clearTimeout(greetingTimer.current); };
  }, []);

  useEffect(() => {
    if (!showGreeting) return;
    const timeout = window.setTimeout(dismissGreeting, 8000);
    return () => window.clearTimeout(timeout);
  }, [showGreeting]);

  useEffect(() => {
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    let player: DotLottie | undefined;
    let cancelled = false;
    const update = () => {
      const play = !motion.matches && !document.hidden;
      setAnimated(play && !!player);
      if (play) player?.play(); else player?.pause();
    };
    // Load the optional mascot after the page; assistant controls work immediately.
    const timer = window.setTimeout(() => {
      if (motion.matches) return;
      void import('@lottiefiles/dotlottie-web').then(({ DotLottie }) => {
        if (cancelled || !canvas.current) return;
        DotLottie.setWasmUrl('/assets/uk/dotlottie-player.wasm');
        player = new DotLottie({ canvas: canvas.current, src: '/assets/robot.json', autoplay: false, loop: true });
        update();
      }).catch(() => setAnimated(false));
    }, 1500);
    motion.addEventListener('change', update);
    document.addEventListener('visibilitychange', update);
    return () => {
      cancelled = true; clearTimeout(timer); player?.destroy();
      motion.removeEventListener('change', update);
      document.removeEventListener('visibilitychange', update);
    };
  }, []);

  function dismissGreeting() {
    if (greetingTimer.current) clearTimeout(greetingTimer.current);
    setShowGreeting(false);
    try { sessionStorage.setItem('helm-greeting-dismissed', 'yes'); } catch { /* Session memory is optional. */ }
  }
  function open() { dismissGreeting(); setIsOpen(true); }
  function close() { setIsOpen(false); trigger.current?.focus(); }

  return <div className="chatbot-launcher-root">
    {isOpen && <ChatPanel onClose={close}/>}
    <div className="chatbot-launcher">
      {showGreeting && !isOpen && <div className="chatbot-greeting-card">
        <button type="button" className="chatbot-greeting-card__open" onClick={open}>
          <span className="chatbot-greeting-card__eyebrow">Helm AI Assistant</span>
          <strong>Welcome to Helm Ai</strong>
          <span>Your guide to UK private health cover. Ask a question.</span>
        </button>
        <button type="button" className="chatbot-greeting-card__close" onClick={dismissGreeting} aria-label="Dismiss message"><X size={16}/></button>
      </div>}
      <button ref={trigger} type="button" className="chatbot-launcher__button" aria-label="Open the Helm AI assistant" aria-expanded={isOpen} aria-controls={isOpen ? 'helm-public-assistant' : undefined} onClick={open}>
        {!animated && <MessageCircle size={28} aria-hidden="true"/>}
        <canvas ref={canvas} width={96} height={96} className="chatbot-launcher__canvas" hidden={!animated} aria-hidden="true"/>
      </button>
    </div>
  </div>;
}
