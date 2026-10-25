import { useEffect } from 'react';

const interactive = 'button,a[href],summary,[role="button"],[role="tab"],[role="menuitem"],input[type="submit"],input[type="button"]';
export function pressTarget(target: EventTarget | null) {
  const element = target instanceof Element ? target.closest<HTMLElement>(interactive) : null;
  return element && !element.closest('[disabled],[aria-disabled="true"],[inert]') ? element : null;
}

export function PressFeedback() {
  useEffect(() => {
    let active: HTMLElement | null = null;
    let pointer: number | null = null;
    function clear() { active?.removeAttribute('data-pressed'); active = null; pointer = null; }
    function down(event: PointerEvent) {
      if (event.button !== 0 || !event.isPrimary) return;
      clear(); active = pressTarget(event.target); pointer = event.pointerId;
      active?.setAttribute('data-pressed', 'true');
    }
    function move(event: PointerEvent) {
      if (!active || event.pointerId !== pointer) return;
      const rect = active.getBoundingClientRect();
      const inside = event.clientX >= rect.left - 10 && event.clientX <= rect.right + 10 && event.clientY >= rect.top - 10 && event.clientY <= rect.bottom + 10;
      active.toggleAttribute('data-pressed', inside);
    }
    function key(event: KeyboardEvent) {
      if (event.repeat || !['Enter', ' '].includes(event.key)) return;
      clear(); active = pressTarget(event.target); active?.setAttribute('data-pressed', 'true');
    }
    document.addEventListener('pointerdown', down, true);
    document.addEventListener('pointermove', move, { passive: true });
    document.addEventListener('pointerup', clear, true);
    document.addEventListener('pointercancel', clear, true);
    document.addEventListener('keydown', key, true);
    document.addEventListener('keyup', clear, true);
    window.addEventListener('blur', clear);
    document.addEventListener('scroll', clear, { capture: true, passive: true });
    return () => {
      clear(); document.removeEventListener('pointerdown', down, true); document.removeEventListener('pointermove', move);
      document.removeEventListener('pointerup', clear, true); document.removeEventListener('pointercancel', clear, true);
      document.removeEventListener('keydown', key, true); document.removeEventListener('keyup', clear, true);
      window.removeEventListener('blur', clear); document.removeEventListener('scroll', clear, true);
    };
  }, []);
  return null;
}
