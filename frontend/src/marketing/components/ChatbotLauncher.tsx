import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { MessageCircle, X } from 'lucide-react';
import type { DotLottie } from '@lottiefiles/dotlottie-web';
import { ChatPanel } from './ChatPanel';
import './ChatbotLauncher.css';

const ChatWidget = lazy(() => import('../chat/ChatWidget'));
const NEXT_CHAT_UI = import.meta.env.VITE_NEXT_CHAT_UI !== 'false';
export function ChatbotLauncher({hideTrigger=false}:{hideTrigger?:boolean}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const greetingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [isOpen, setIsOpen] = useState(() => { try { return NEXT_CHAT_UI && sessionStorage.getItem('helm-chat-open') === 'yes'; } catch { return false; } });
  const [hasOpened, setHasOpened] = useState(isOpen);
  const [unread, setUnread] = useState(false);
  useEffect(() => { try { sessionStorage.setItem('helm-chat-open', isOpen ? 'yes' : 'no'); } catch { /* Optional storage. */ } }, [isOpen]);
  const [animated, setAnimated] = useState(false);
  const [showGreeting, setShowGreeting] = useState(false);
  useEffect(() => {
    try { if (sessionStorage.getItem('helm-greeting-dismissed') === 'yes') return; } catch { /* Storage may be unavailable. */ }
    greetingTimer.current = setTimeout(() => setShowGreeting(true), 4000);
    return () => { if (greetingTimer.current) clearTimeout(greetingTimer.current); };
  }, []);

  useEffect(() => {
    if (!showGreeting) return;
    const timeout = window.setTimeout(dismissGreeting, 6000);
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
    // Keep the static launcher immediate; load the optional animation on interaction.
    let loaded = false;
    const loadAnimation = () => {
      if (motion.matches || loaded) return;
      loaded = true;
      void import('@lottiefiles/dotlottie-web').then(({ DotLottie }) => {
        if (cancelled || !canvas.current) return;
        DotLottie.setWasmUrl('/assets/uk/dotlottie-player.wasm');
        player = new DotLottie({ canvas: canvas.current, src: '/assets/robot.json', autoplay: false, loop: true });
        update();
      }).catch(() => setAnimated(false));
    };
    const button = trigger.current;
    button?.addEventListener('pointerenter', loadAnimation);
    button?.addEventListener('focus', loadAnimation);
    motion.addEventListener('change', update);
    document.addEventListener('visibilitychange', update);
    return () => {
      cancelled = true; player?.destroy();
      button?.removeEventListener('pointerenter', loadAnimation);
      button?.removeEventListener('focus', loadAnimation);
      motion.removeEventListener('change', update);
      document.removeEventListener('visibilitychange', update);
    };
  }, [hideTrigger]);

  function dismissGreeting() {
    if (greetingTimer.current) clearTimeout(greetingTimer.current);
    setShowGreeting(false);
    try { sessionStorage.setItem('helm-greeting-dismissed', 'yes'); } catch { /* Session memory is optional. */ }
  }
  useEffect(() => { const show=()=>open();window.addEventListener('helm-open-assistant',show);return()=>window.removeEventListener('helm-open-assistant',show); }, []);
  function open() { returnFocus.current=document.activeElement instanceof HTMLElement?document.activeElement:null;dismissGreeting(); setIsOpen(true); setHasOpened(true); setUnread(false); }
  function close() { setIsOpen(false); (trigger.current || returnFocus.current)?.focus(); }

  return <div className="chatbot-launcher-root">
    {NEXT_CHAT_UI ? hasOpened && <Suspense fallback={null}><ChatWidget open={isOpen} onClose={close} onUnread={() => setUnread(true)}/></Suspense> : isOpen && <ChatPanel onClose={close}/>}
    {!hideTrigger && <div className="chatbot-launcher">
      {showGreeting && !isOpen && <div className="chatbot-greeting-card">
        <button type="button" className="chatbot-greeting-card__open" onClick={open}>
          <span className="chatbot-greeting-card__eyebrow">Helm AI Assistant</span>
          <strong>Welcome to Helm Ai</strong>
          <span>Your guide to UK private health cover. Ask a question.</span>
        </button>
        <button type="button" className="chatbot-greeting-card__close" onClick={dismissGreeting} aria-label="Dismiss message"><X size={16}/></button>
      </div>}
      <button ref={trigger} type="button" className="chatbot-launcher__button" aria-label={isOpen ? "Minimize the Helm AI assistant" : "Open the Helm AI assistant"} aria-expanded={isOpen} aria-controls={isOpen ? 'helm-public-assistant' : undefined} onClick={isOpen ? close : open}>
        {unread && <span className="chatbot-unread" aria-label="New assistant message"/>}
        {!animated && <MessageCircle size={28} aria-hidden="true"/>}
        <canvas ref={canvas} width={96} height={96} className="chatbot-launcher__canvas" hidden={!animated} aria-hidden="true"/>
      </button>
    </div>}
  </div>;
}
