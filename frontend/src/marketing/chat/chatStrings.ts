export const chatStrings = {
  en: {
    title: 'Helm AI Assistant', subtitle: 'UK health-insurance guide', online: 'Ready · general information', thinking: 'Preparing guidance…',
    welcome: 'Welcome to Helm Ai', intro: 'Make sense of UK private health cover. Start with what matters to you.',
    starters: ['How does private cover work?', 'How do I compare plans?', "What isn’t covered?", 'Talk to an adviser'],
    placeholder: 'Ask about plans, costs, coverage…', message: 'Type your message', send: 'Send message', stop: 'Stop response',
    close: 'Close assistant', expand: 'Expand assistant', collapse: 'Collapse assistant', menu: 'Conversation options',
    newChat: 'New conversation', undo: 'Undo', cleared: 'Conversation cleared.', transcript: 'Download transcript', human: 'Talk to a human', privacy: 'Privacy & AI disclosure',
    disclosure: 'General information only. This demo has no live adviser service. AI can make mistakes.',
    sensitive: 'Don’t share health, identity, bank or card details.', attach: 'Attach a file', photo: 'Upload photo', pdf: 'Upload PDF', camera: 'Take photo',
    uploadConsent: 'Use only sample documents. Raw files are discarded after reading; extracted text is deleted within 24 hours. Never attach identity or payment documents.',
    consent: 'I agree to temporary file processing', remove: 'Remove file', retry: 'Retry', failed: 'Couldn’t send. Please try again.',
    offline: 'You’re offline. Keep typing; send when connected.', latest: '↓ New message', copy: 'Copy message', copied: 'Copied', like: 'Helpful', dislike: 'Not helpful', regenerate: 'Regenerate response',
    mic: 'Dictate a message', cancel: 'Cancel', done: 'Done', recording: 'Listening', voiceConsent: 'Voice may be processed by your browser speech provider or Groq. No recording is stored by Helm. Review the transcript before sending.',
    denied: 'Microphone access is blocked or unavailable. Check site permissions, or type your message.', stopped: 'Stopped',
    handoff: 'Create a demo support reference', topic: 'Topic', topics: ['General question', 'Complaint', 'Extra support'],
    noDelivery: 'No callback or email service is connected. No contact details are collected here.',
    temporary: 'Conversation stays in this tab. Feedback is saved separately.', clearQuestion: 'Start again? You can undo until you send another message.',
    drop: 'Drop up to 5 sample files to attach', tooMany: 'Use up to 5 files, each below 10 MB.', preview: 'Attachment preview', lightbox: 'Close attachment preview',
    rate: 'Message limit reached. Try again in', read: 'Read message aloud', stopRead: 'Stop reading', upload: 'Uploading…', date: 'Today', sent: 'Sent',
  },
} as const;
export type ChatLanguage = keyof typeof chatStrings;
