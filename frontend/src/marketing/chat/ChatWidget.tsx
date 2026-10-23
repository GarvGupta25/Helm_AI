import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowUp, Bot, Check, FileText, Maximize2, Mic, Minimize2, MoreHorizontal, Plus, Square, X } from 'lucide-react';
import { chatStrings, type ChatLanguage } from './chatStrings';
import { MessageBubble } from './MessageBubble';
import { GreetingAnimation } from './GreetingAnimation';
import { streamChat } from './useChatStream';
import { useAttachments } from './useAttachments';
import { useVoiceInput } from './useVoiceInput';
import type { Message } from './types';
import './chat.tokens.css';
import './chat.css';

function restored(): Message[] { try { const stored = JSON.parse(sessionStorage.getItem('helm-chat-v2') || '[]') as Message[]; return Array.isArray(stored) ? stored.filter(m => ['user', 'assistant'].includes(m.role) && typeof m.text === 'string' && Number.isFinite(m.at)).slice(-200) : []; } catch { return []; } }
const makeMessage = (role: Message['role'], text: string): Message => ({ id: crypto.randomUUID(), role, text, at: Date.now(), status: 'sent' });
export default function ChatWidget({ open, onClose, onUnread }: { open: boolean; onClose: () => void; onUnread: () => void }) {
  const [messages, setMessages] = useState<Message[]>(restored);
  const [input, setInput] = useState('');
  const [language, setLanguage] = useState<ChatLanguage>('en');
  const [expanded, setExpanded] = useState(false);
  const [menu, setMenu] = useState(false);
  const [attachMenu, setAttachMenu] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [handoff, setHandoff] = useState(false);
  const [topic, setTopic] = useState(0);
  const [pendingHandoff, setPendingHandoff] = useState(false);
  const [fileConsent, setFileConsent] = useState(false);
  const [voiceConsent, setVoiceConsent] = useState(false);
  const [preview, setPreview] = useState('');
  const [offline, setOffline] = useState(!navigator.onLine);
  const [rateSeconds, setRateSeconds] = useState(0);
  const [newMessages, setNewMessages] = useState(false);
  const [backup, setBackup] = useState<Message[]>();
  const [confirmNew, setConfirmNew] = useState(false);
  const panel = useRef<HTMLDivElement>(null);
  const textarea = useRef<HTMLTextAreaElement>(null);
  const log = useRef<HTMLDivElement>(null);
  const file = useRef<HTMLInputElement>(null);
  const controller = useRef<AbortController | null>(null);
  const nearBottom = useRef(true);
  const openRef = useRef(open);
  const lastQuestion = useRef('');
  const t = chatStrings[language];
  const attachments = useAttachments(setError, t.tooMany);
  const voice = useVoiceInput(language, setInput, setError, t.denied);
  useEffect(() => { openRef.current = open; if (open) textarea.current?.focus(); else voice.stop(true); }, [open, voice.stop]);
  useEffect(() => () => controller.current?.abort(), []);
  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    window.addEventListener('online', update); window.addEventListener('offline', update);
    return () => { window.removeEventListener('online', update); window.removeEventListener('offline', update); };
  }, []);
  useEffect(() => {
    const viewport = window.visualViewport;
    const update = () => { panel.current?.style.setProperty('--hc-viewport', `${viewport?.height || window.innerHeight}px`); panel.current?.style.setProperty('--hc-offset', `${viewport?.offsetTop || 0}px`); };
    update(); viewport?.addEventListener('resize', update); viewport?.addEventListener('scroll', update);
    return () => { viewport?.removeEventListener('resize', update); viewport?.removeEventListener('scroll', update); };
  }, []);
  useEffect(() => {
    // Session-only storage. Raw user content is not sent to analytics or durable storage.
    try { sessionStorage.setItem('helm-chat-v2', JSON.stringify(messages.slice(-200).map(({ attachments: files, ...m }) => ({ ...m, attachments: files?.map(a => ({ id: a.id, name: a.name, mime: a.mime, size: a.size, status: a.status, progress: a.progress })) })))); } catch { /* Quota/private browsing: in-memory only. */ }
    if (nearBottom.current) { if (log.current) log.current.scrollTop = log.current.scrollHeight; } else setNewMessages(true);
  }, [messages]);
  useEffect(() => { if (textarea.current) { textarea.current.style.height = 'auto'; textarea.current.style.height = `${Math.min(textarea.current.scrollHeight, 132)}px`; } }, [input]);
  useEffect(() => { if (rateSeconds <= 0) return; const id = setInterval(() => setRateSeconds(s => Math.max(0, s-1)), 1000); return () => clearInterval(id); }, [rateSeconds]);
  useEffect(() => {
    if (!open) return;
    function escape(event: KeyboardEvent) {
      if (event.key !== 'Escape') return;
      event.stopPropagation();
      if (preview) setPreview(''); else if (voice.recording) voice.stop(true); else if (menu || attachMenu) { setMenu(false); setAttachMenu(false); } else if (handoff) setHandoff(false); else onClose();
    }
    document.addEventListener('keydown', escape);
    return () => document.removeEventListener('keydown', escape);
  }, [open, preview, menu, attachMenu, handoff, onClose, voice.recording, voice.stop]);
  const feedback = useCallback((id: string, value: 'up' | 'down') => { setMessages(items => items.map(m => m.id === id ? { ...m, feedback: value } : m)); }, []);
  async function send(text: string, regenerate = false) {
    if (generating || rateSeconds || offline || (!text.trim() && !attachments.attachments.length)) return;
    if (attachments.attachments.some(a => a.status !== 'ready')) { setError(t.failed); return; }
    const question = text.trim() || (language === 'ar' ? 'اشرح مصطلحات التأمين في المرفق' : 'Explain an insurance term from my attachment');
    lastQuestion.current = question; setBackup(undefined); setError(''); setNotice(''); setSuggestions([]); setInput(''); setGenerating(true); voice.stop(true);
    const files = regenerate ? [] : attachments.consume();
    const user = { ...makeMessage('user', question), status: 'sending' as const, attachments: files };
    const bot = makeMessage('assistant', '');
    setMessages(items => [...(regenerate ? items.filter((_, i) => i !== items.length-1 || items[i].role !== 'assistant') : [...items, user]), bot].slice(-200));
    controller.current = new AbortController(); let content = ''; let frame = 0;
    const updateText = () => { setMessages(items => items.map(m => m.id === bot.id ? { ...m, text: content } : m)); frame = 0; };
    try {
      await streamChat({ message: question, attachments: files.map(a => a.id), language }, controller.current.signal, (type, data) => {
        if (type === 'token') { content += data.text || ''; if (!frame) frame = requestAnimationFrame(updateText); }
        if (type === 'suggestions') setSuggestions((data.items || []).filter(s => s.length <= 40).slice(0, 3));
        if (type === 'handoff' && data.ticket_ref) { content += `\n\n${language === 'ar' ? 'مرجع دعم تجريبي' : 'Demo support reference'}: ${data.ticket_ref}`; updateText(); }
        if (type === 'error') throw new Error(data.message || t.failed);
        if (type === 'done') setMessages(items => items.map(m => m.id === bot.id ? { ...m, actions: data.actions } : m));
      });
      setMessages(items => items.map(m => m.id === user.id ? { ...m, status: 'sent' } : m));
      if (!openRef.current) onUnread();
    } catch (e) {
      if (controller.current.signal.aborted) { setMessages(items => items.map(m => m.id === bot.id ? { ...m, status: 'stopped' } : m.id === user.id ? { ...m, status: 'sent' } : m)); }
      else { const message = e instanceof Error ? e.message : t.failed; if (message === 'RATE_LIMIT') setRateSeconds(3600); else setError(message); setMessages(items => items.map(m => m.id === user.id ? { ...m, status: 'failed' } : m)); }
    } finally { if (frame) cancelAnimationFrame(frame); updateText(); setGenerating(false); }
  }
  function download() { const url = URL.createObjectURL(new Blob([messages.map(m => `${new Date(m.at).toISOString()} ${m.role}: ${m.text}`).join('\n\n')], { type: 'text/plain;charset=utf-8' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'helm-conversation.txt'; anchor.click(); URL.revokeObjectURL(url); setMenu(false); }
  async function requestHandoff() { setPendingHandoff(true); setError(''); try { const response = await fetch('/api/public/assistant/handoff', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic: ['General question', 'Complaint', 'Extra support'][topic] }) }); const data = await response.json(); if (!response.ok) throw new Error(data.message || t.failed); setMessages(items => [...items, makeMessage('assistant', `${data.reply}\n\nDemo support reference: ${data.ticket_ref}`)]); setHandoff(false); } catch (e) { setError(e instanceof Error ? e.message : t.failed); } finally { setPendingHandoff(false); } }
  function chooseFile(accept: string, capture = false) { if (!file.current) return; file.current.accept = accept; if (capture) file.current.setAttribute('capture', 'environment'); else file.current.removeAttribute('capture'); file.current.click(); setAttachMenu(false); }
  return <div ref={panel} id="helm-public-assistant" className={`hc-panel${expanded ? ' hc-panel--expanded' : ''}`} role="dialog" aria-label="Helm AI assistant" dir={language === 'ar' ? 'rtl' : 'ltr'} lang={language} data-drop-label={t.drop} hidden={!open} onDragOver={e => { e.preventDefault(); panel.current?.classList.add('hc-drag'); }} onDragLeave={() => panel.current?.classList.remove('hc-drag')} onDrop={e => { e.preventDefault(); panel.current?.classList.remove('hc-drag'); attachments.add(e.dataTransfer.files, fileConsent); }}>
    <header className="hc-header" role="presentation"><span className="hc-header-avatar" aria-hidden="true"><Bot size={23}/></span><div className="hc-heading"><strong>{t.title}</strong><span><i/>{generating ? t.thinking : t.online}</span></div><button aria-label={t.menu} aria-expanded={menu} onClick={() => setMenu(!menu)}><MoreHorizontal size={20}/></button><button aria-label={expanded ? t.collapse : t.expand} onClick={() => setExpanded(!expanded)}>{expanded ? <Minimize2 size={18}/> : <Maximize2 size={18}/>}</button><button aria-label={t.close} onClick={onClose}><X size={20}/></button></header>
    {menu && <div className="hc-menu"><button onClick={() => { setConfirmNew(true); setMenu(false); }}>{t.newChat}</button><button onClick={() => { setHandoff(true); setMenu(false); }}>{t.human}</button><button onClick={download}>{t.transcript}</button><button onClick={() => { setLanguage(language === 'en' ? 'ar' : 'en'); setMenu(false); }}>English / العربية</button><a href="/legal/privacy">{t.privacy}</a></div>}
    {offline && <div role="status" className="hc-banner">{t.offline}</div>}
    {confirmNew && <div className="hc-banner"><p>{t.clearQuestion}</p><button onClick={() => { controller.current?.abort(); setBackup(messages); setMessages([]); setConfirmNew(false); attachments.clear(); setNotice(t.cleared); }}>{t.newChat}</button><button onClick={() => setConfirmNew(false)}>{t.cancel}</button></div>}
    <div className="hc-scroll" ref={log} onScroll={() => { if (!log.current) return; nearBottom.current = log.current.scrollHeight-log.current.scrollTop-log.current.clientHeight < 70; if (nearBottom.current) setNewMessages(false); }}>
      {!messages.length && <section className="hc-empty">{open && <GreetingAnimation/>}<p className="hc-eyebrow">{t.subtitle}</p><h2>{t.welcome}</h2><p>{t.intro}</p><div className="hc-starters">{t.starters.map((prompt, index) => <button key={prompt} disabled={generating || offline} onClick={() => index === 3 ? setHandoff(true) : void send(language === 'ar' ? chatStrings.en.starters[index] : prompt)}>{prompt}</button>)}</div><small>{t.sensitive}</small></section>}
      {messages.length > 0 && <p className="hc-date">{t.date}</p>}
      <div role="log" aria-label={language === 'ar' ? 'سجل المحادثة' : 'Chat conversation'} aria-live={generating ? 'off' : 'polite'} aria-relevant="additions">{messages.map((m, i) => <MessageBubble key={m.id} message={m} language={language} last={i === messages.length-1} generating={generating && i === messages.length-1} onFeedback={feedback} onRegenerate={() => void send([...messages].reverse().find(m => m.role === 'user')?.text || lastQuestion.current, true)} onPreview={setPreview} onNotice={setNotice}/>)}</div>
      {generating && !messages.at(-1)?.text && <div className="hc-typing" role="status" aria-label={t.thinking}><span/><span/><span/></div>}
      {handoff && <form className="hc-handoff" onSubmit={e => { e.preventDefault(); void requestHandoff(); }}><h3>{t.handoff}</h3><p>{t.noDelivery}</p><label>{t.topic}<select value={topic} onChange={e => setTopic(+e.target.value)}>{t.topics.map((name, i) => <option value={i} key={name}>{name}</option>)}</select></label><button disabled={pendingHandoff}>{pendingHandoff ? t.thinking : t.handoff}</button><button type="button" onClick={() => setHandoff(false)}>{t.cancel}</button></form>}
    </div>
    {newMessages && <button className="hc-latest" onClick={() => { nearBottom.current = true; log.current?.scrollTo({ top: log.current.scrollHeight }); setNewMessages(false); }}>{t.latest}</button>}
    {notice && <div className="hc-notice" role="status">{notice}{backup && <button onClick={() => { setMessages(backup); setBackup(undefined); setNotice(''); }}>{t.undo}</button>}</div>}
    {error && <div className="hc-error" role="alert">{error}<button disabled={generating || offline} onClick={() => void send(lastQuestion.current, true)}>{t.retry}</button><button onClick={() => setHandoff(true)}>{t.human}</button></div>}
    {rateSeconds > 0 && <div className="hc-error" role="timer">{t.rate} {Math.floor(rateSeconds/60)}:{String(rateSeconds%60).padStart(2, '0')}</div>}
    {!!suggestions.length && !input && !generating && <div className="hc-suggestions">{suggestions.map((s, i) => <button key={s} onClick={() => i === 2 ? setHandoff(true) : void send(s)}>{language === 'ar' ? chatStrings.ar.starters[i] : s}</button>)}</div>}
    <div className="hc-composer-wrap">
      {attachments.attachments.length > 0 && <div className="hc-attachments">{attachments.attachments.map(a => <div className="hc-attachment" key={a.id}>{a.url ? <img src={a.url} alt=""/> : <FileText size={24}/>}<span>{a.name}<small>{Math.round(a.size/1024)} KB · {a.status === 'uploading' ? t.upload : a.status === 'error' ? a.error : <Check size={12}/>}</small></span>{a.status === 'uploading' && <progress value={a.progress} max="100" aria-label={t.upload}/>}<button aria-label={`${t.remove}: ${a.name}`} onClick={() => attachments.remove(a.id)}><X size={14}/></button>{a.status === 'error' && <button onClick={() => void attachments.retry(a)}>{t.retry}</button>}</div>)}</div>}
      {attachMenu && <div className="hc-attach-menu"><p>{t.uploadConsent}</p><label><input type="checkbox" checked={fileConsent} onChange={e => setFileConsent(e.target.checked)}/>{t.consent}</label><button disabled={!fileConsent} onClick={() => chooseFile('image/jpeg,image/png,image/webp,image/heic,image/heif')}>{t.photo}</button><button disabled={!fileConsent} onClick={() => chooseFile('application/pdf')}>{t.pdf}</button><button disabled={!fileConsent} onClick={() => chooseFile('image/*', true)}>{t.camera}</button></div>}
      {voiceConsent && <div className="hc-attach-menu"><p>{t.voiceConsent}</p><button onClick={() => { setVoiceConsent(false); void voice.start(); }}>{t.done}</button><button onClick={() => setVoiceConsent(false)}>{t.cancel}</button></div>}
      <form className="hc-composer" onSubmit={e => { e.preventDefault(); void send(input); }}>
        <button type="button" aria-label={t.attach} aria-expanded={attachMenu} disabled={generating} onClick={() => setAttachMenu(!attachMenu)}><Plus size={20}/></button>
        <textarea ref={textarea} value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(input); } }} onPaste={e => { const files = Array.from(e.clipboardData.files); if (files.length) { e.preventDefault(); if (!fileConsent) setAttachMenu(true); attachments.add(files, fileConsent); } }} placeholder={voice.recording ? t.recording : t.placeholder} aria-label={t.message} rows={1} maxLength={2000}/>
        {generating ? <button type="button" className="hc-primary" aria-label={t.stop} onClick={() => controller.current?.abort()}><Square size={16}/></button> : voice.recording ? <><span className="hc-recording" role="timer">{voice.seconds}s</span><button type="button" aria-label={t.cancel} onClick={() => voice.stop(true)}><X size={18}/></button><button type="button" aria-label={t.done} onClick={() => voice.stop()}><Check size={18}/></button></> : input.trim() || attachments.attachments.length ? <button className="hc-primary" aria-label={t.send} disabled={offline || rateSeconds > 0}><ArrowUp size={20}/></button> : <button type="button" aria-label={t.mic} onClick={() => setVoiceConsent(true)}><Mic size={20}/></button>}
      </form>
      {input.length >= 1800 && <span className="hc-counter">{input.length}/2000</span>}
      <input ref={file} type="file" hidden multiple onChange={e => { if (e.target.files) attachments.add(e.target.files, fileConsent); e.target.value = ''; }}/>
      <p className="hc-disclosure">{t.disclosure} <a href="/legal/privacy">{language === 'ar' ? 'الخصوصية' : 'Privacy'}</a> · <button onClick={() => setHandoff(true)}>{t.human}</button><span>{t.temporary}</span></p>
    </div>
    {preview && <div className="hc-lightbox" role="dialog" aria-label={t.preview}><button autoFocus aria-label={t.lightbox} onClick={() => setPreview('')}><X/></button><img src={preview} alt={t.preview}/></div>}
  </div>;
}
