export type Attachment = { id: string; name: string; mime: string; size: number; url?: string; status: 'uploading' | 'ready' | 'error'; error?: string; file?: File; progress: number };
export type Message = { id: string; role: 'user' | 'assistant'; text: string; at: number; status?: 'sending' | 'sent' | 'failed' | 'stopped'; feedback?: 'up' | 'down'; attachments?: Attachment[]; actions?: { label: string; href: string }[] };
export type StreamEvent = { text?: string; items?: string[]; ticket_ref?: string; intent?: string; actions?: { label: string; href: string }[]; message?: string };
