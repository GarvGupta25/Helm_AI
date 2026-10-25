import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type PointerEvent, type ReactNode } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { project, rubberband, spring } from './spring';

export function SheetModal({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  const [present, setPresent] = useState(open); const [closing, setClosing] = useState(false);
  const content = useRef<HTMLDivElement>(null); const overlay = useRef<HTMLDivElement>(null);
  const [mountedNode,setMountedNode] = useState<HTMLDivElement|null>(null);
  const setContent=useCallback((node:HTMLDivElement|null)=>{content.current=node;setMountedNode(node);},[]);
  const motion = useRef<ReturnType<typeof spring> | null>(null); const fade = useRef<ReturnType<typeof spring> | null>(null);
  const latest = useRef({ open, onClose, closing, reduced: false }); latest.current = { ...latest.current, open, onClose, closing };
  const drag = useRef<{ id: number; start: number; origin: number; active: boolean; samples: { y: number; time: number }[] } | null>(null);
  const closingByUser = useRef(false);
  useEffect(() => { if (open) { setPresent(true); setClosing(false); closingByUser.current = false; } }, [open]);
  useLayoutEffect(() => {
    if (!present || !content.current) return;
    const node = content.current; const scrim = overlay.current;
    node.dataset.sheetReady='true';
    const media = typeof matchMedia==='function' ? matchMedia('(prefers-reduced-motion: reduce)') : { matches: false, addEventListener() {}, removeEventListener() {} }; latest.current.reduced = media.matches;
    const transparency = typeof matchMedia==='function' ? matchMedia('(prefers-reduced-transparency: reduce)') : null;
    const contrast = typeof matchMedia==='function' ? matchMedia('(prefers-contrast: more)') : null;
    const distance = () => window.innerHeight + 32;
    function finish() {
      if (!latest.current.open || latest.current.closing) {
        setPresent(false);
        if (closingByUser.current) { closingByUser.current = false; latest.current.onClose(); }
      }
    }
    motion.current ||= spring(media.matches ? 0 : distance(), value => { node.style.setProperty('--sheet-y', `${value}px`); }, finish);
    fade.current ||= spring(0, value => {
      const alpha = Math.max(0, Math.min(1, value)); if (scrim) scrim.style.opacity = String(alpha);
      node.style.opacity = latest.current.reduced ? String(alpha) : '1';
    }, () => { if (latest.current.reduced) finish(); }, .002);
    function update() {
      latest.current.reduced = media.matches;
      node.dataset.reducedMotion=String(media.matches);
      node.dataset.reducedTransparency=String(Boolean(transparency?.matches));
      node.dataset.moreContrast=String(Boolean(contrast?.matches));
      const show = latest.current.open && !latest.current.closing;
      if (drag.current && !media.matches && show) return;
      if (media.matches) { drag.current = null; motion.current?.jump(0); }
      else motion.current?.to(show ? 0 : distance(), { damping: closingByUser.current && Math.abs(motion.current.velocity)>80 ? .8 : 1, response: .3 });
      fade.current?.to(show ? 1 : 0, { damping: 1, response: media.matches ? .12 : .3 });
    }
    update(); for(const signal of [media,transparency,contrast])signal?.addEventListener('change',update);
    return () => { for(const signal of [media,transparency,contrast])signal?.removeEventListener('change',update); motion.current?.pause(); fade.current?.pause(); };
  }, [present, open, closing, mountedNode]);
  useEffect(() => { if (!present) { motion.current?.pause(); fade.current?.pause(); motion.current = null; fade.current = null; } }, [present]);
  function requestClose() { closingByUser.current = true; setClosing(true); }
  function down(event: PointerEvent<HTMLDivElement>) {
    if (event.button !== 0 || !event.isPrimary || latest.current.reduced || !motion.current) return;
    motion.current.pause(); fade.current?.pause();
    event.currentTarget.setPointerCapture(event.pointerId);
    drag.current = { id: event.pointerId, start: event.clientY, origin: motion.current.value, active: false, samples: [{ y: event.clientY, time: event.timeStamp }] };
    closingByUser.current = false; setClosing(false);
  }
  function move(event: PointerEvent<HTMLDivElement>) {
    const d = drag.current; if (!d || d.id !== event.pointerId || !motion.current) return;
    const delta = event.clientY - d.start;
    d.samples.push({ y: event.clientY, time: event.timeStamp }); d.samples = d.samples.filter(s => event.timeStamp - s.time <= 80);
    if (!d.active && Math.abs(delta) < 10) return;
    d.active = true; const raw = d.origin + delta;
    motion.current.jump(raw < 0 ? rubberband(raw, content.current?.offsetHeight || 600) : raw);
  }
  function release(event: PointerEvent<HTMLDivElement>, canceled = false) {
    const d = drag.current; if (!d || d.id !== event.pointerId || !motion.current) return;
    drag.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    const first = d.samples[0]; const elapsed = event.timeStamp - first.time;
    const velocity = !canceled && elapsed > 0 && elapsed < 150 ? (event.clientY - first.y) / elapsed * 1000 : 0;
    const height = content.current?.offsetHeight || 600;
    const dismiss = !canceled && d.active && velocity >= -80 && motion.current.value + project(velocity) > height * .4;
    if (dismiss) { closingByUser.current = true; setClosing(true); }
    motion.current.to(dismiss ? window.innerHeight + 32 : 0, { velocity, damping: Math.abs(velocity) > 80 ? .8 : 1, response: .3 });
    fade.current?.to(dismiss ? 0 : 1, { damping: 1, response: .3 });
  }
  return <Dialog.Root open={present} onOpenChange={value => { if (!value) requestClose(); }}><Dialog.Portal>
    <Dialog.Overlay ref={overlay} className="uk-overlay apple-sheet-overlay"/>
    <Dialog.Content ref={setContent} className="uk-modal apple-sheet" data-closing={closing || !open || undefined} style={{ '--sheet-y': '0px' } as CSSProperties}>
      <div className="apple-sheet-grab" aria-hidden="true" onPointerDown={down} onPointerMove={move} onPointerUp={event => release(event)} onPointerCancel={event => release(event, true)} onLostPointerCapture={event => { if (drag.current) release(event, true); }}><span/></div>
      <Dialog.Title>{title}</Dialog.Title><Dialog.Description className="uk-sr">{title}. Press Escape or the close button to return.</Dialog.Description>
      <button type="button" className="uk-icon uk-close" aria-label="Close dialog" onClick={requestClose}><X/></button>{children}
    </Dialog.Content>
  </Dialog.Portal></Dialog.Root>;
}
