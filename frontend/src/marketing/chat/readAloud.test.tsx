import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useReadAloud } from './useReadAloud';

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });
describe('response read aloud', () => {
  it('reads only on request, switches/stops replies and cancels on close', () => {
    class Utterance { lang = ''; voice: unknown; onend?: () => void; onerror?: () => void; constructor(public text: string) {} }
    const speech = { speak: vi.fn(), cancel: vi.fn(), getVoices: () => [] };
    vi.stubGlobal('SpeechSynthesisUtterance', Utterance);
    vi.stubGlobal('speechSynthesis', speech);
    const { result, rerender, unmount } = renderHook(({ open }) => useReadAloud(open, vi.fn()), { initialProps: { open: true } });
    expect(speech.speak).not.toHaveBeenCalled();
    act(() => result.current.read('first', '**A fictional answer.**'));
    expect(result.current.speakingId).toBe('first');
    expect(speech.speak.mock.calls[0][0].text).toBe('A fictional answer.');
    act(() => result.current.read('second', 'Another response.'));
    expect(result.current.speakingId).toBe('second');
    act(() => result.current.read('second', 'Another response.'));
    expect(result.current.speakingId).toBe('');
    act(() => result.current.read('first', 'Read again.'));
    rerender({ open: false });
    expect(result.current.speakingId).toBe('');
    unmount();
    expect(speech.cancel).toHaveBeenCalled();
  });
  it('gives a useful fallback when browser voices are unavailable', () => {
    vi.stubGlobal('speechSynthesis', undefined);
    const notice = vi.fn();
    const { result } = renderHook(() => useReadAloud(true, notice));
    expect(result.current.supported).toBe(false);
    act(() => result.current.read('first', 'A response.'));
    expect(notice).toHaveBeenCalledWith(expect.stringContaining('unavailable'));
  });
});
