import { memo } from 'react';
import { MarkdownReply } from './MarkdownReply';
import { Bot, Check, Copy, ThumbsDown, ThumbsUp, RotateCcw, Flag, Volume2, Square } from 'lucide-react';
import type { Message } from './types';
import { chatStrings, type ChatLanguage } from './chatStrings';

export const MessageBubble = memo(function MessageBubble({ message, language, last, generating, onFeedback, onReport, onRead, speaking, canRead, onRegenerate, onPreview, onNotice }: { message: Message; language: ChatLanguage; last: boolean; generating: boolean; onFeedback: (message: Message, value: 'up' | 'down') => void; onReport: (message: Message) => void; onRead: (id: string, text: string) => void; speaking: boolean; canRead: boolean; onRegenerate: () => void; onPreview: (url: string) => void; onNotice: (text: string) => void }) {
  const t = chatStrings[language];
  return <article className={`hc-message hc-message--${message.role}`} aria-label={message.role === 'user' ? 'You' : t.title}>
    {message.role === 'assistant' && <span className="hc-avatar" aria-hidden="true"><Bot size={18}/></span>}
    <div className="hc-message-content"><div className="hc-bubble" dir="auto">
      {message.role === 'assistant' ? <MarkdownReply text={message.text}/> : <p>{message.text}</p>}
      {message.attachments?.map(a => <div className="hc-file" key={a.id}>{a.url ? <button aria-label={`${t.preview}: ${a.name}`} onClick={() => onPreview(a.url!)}><img src={a.url} alt={a.name}/></button> : <span>PDF</span>}<span>{a.name}</span></div>)}
      {message.status === 'stopped' && <small>{t.stopped}</small>}
    </div>
    <div className="hc-metadata"><time dateTime={new Date(message.at).toISOString()}>{new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit' }).format(message.at)}</time>{message.role === 'user' && <span>{message.status === 'failed' ? t.failed : message.status === 'sending' ? '…' : <Check size={12} aria-label={t.sent}/>}</span>}</div>
    {message.role === 'assistant' && message.text && !generating && <div className="hc-message-actions">
      <button title={t.copy} aria-label={t.copy} onClick={() => { void navigator.clipboard?.writeText(message.text).then(() => onNotice(t.copied)).catch(() => onNotice(t.failed)); }}><Copy size={14}/></button>
      <button title={!canRead ? 'Read aloud is unavailable in this browser' : speaking ? t.stopRead : t.read} aria-label={speaking ? t.stopRead : t.read} aria-pressed={speaking} disabled={!canRead} onClick={() => onRead(message.id, message.text)}>{speaking ? <Square size={14}/> : <Volume2 size={14}/>}</button>
      <button title={t.like} aria-label={t.like} aria-pressed={message.feedback === 'up'} onClick={() => onFeedback(message, 'up')}><ThumbsUp size={14}/></button>
      <button title={t.dislike} aria-label={t.dislike} aria-pressed={message.feedback === 'down'} onClick={() => onFeedback(message, 'down')}><ThumbsDown size={14}/></button>
      {last && <button title={t.regenerate} aria-label={t.regenerate} onClick={onRegenerate}><RotateCcw size={14}/></button>}
      <button title="Report an issue" aria-label="Report an issue with this answer" onClick={() => onReport(message)}><Flag size={14}/></button>
    </div>}
    {message.actions?.slice(0, 2).map(a => /^\/[^/]/.test(a.href) && <a className="hc-action-link" key={a.href} href={a.href}>{a.label}</a>)}
    </div>
  </article>;
});
