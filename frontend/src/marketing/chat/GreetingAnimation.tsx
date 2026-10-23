import { useEffect, useRef, useState } from 'react';
import type { DotLottie } from '@lottiefiles/dotlottie-web';
import { Bot } from 'lucide-react';

export function GreetingAnimation() {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    let player: DotLottie | undefined; let cancelled = false;
    const update = () => { if (motion.matches || document.hidden) player?.pause(); else player?.play(); };
    if (!motion.matches) void import('@lottiefiles/dotlottie-web').then(({ DotLottie }) => {
      if (cancelled || !canvas.current) return;
      DotLottie.setWasmUrl('/assets/uk/dotlottie-player.wasm');
      player = new DotLottie({ canvas: canvas.current, src: '/assets/robot.json', loop: true, autoplay: !document.hidden });
      player.addEventListener('load', () => { if (!cancelled) setReady(true); });
    }).catch(() => {});
    motion.addEventListener('change', update); document.addEventListener('visibilitychange', update);
    return () => { cancelled = true; player?.destroy(); motion.removeEventListener('change', update); document.removeEventListener('visibilitychange', update); };
  }, []);
  return <span className="hc-welcome-avatar" aria-hidden="true">{!ready && <Bot size={40}/>}<canvas ref={canvas} width={96} height={96} hidden={!ready} style={{ width: 76, height: 76 }}/></span>;
}
