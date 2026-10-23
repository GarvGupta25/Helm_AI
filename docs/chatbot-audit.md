# Public chatbot audit (before implementation)

Inspected `ChatbotLauncher.tsx`, `ChatPanel.tsx`, their CSS and `public_assistant.py`.

The current panel is a non-modal dialog with a working guarded POST endpoint, six starter prompts, privacy copy and a demo support-ticket path. It already handles loading/errors and IME-safe Enter. The launcher retains the robot dotLottie with reduced-motion/visibility handling and delayed greeting. Keep these safeguards.

The panel lacks voice, attachments, stop/regenerate, streaming, timestamps, avatars, markdown, feedback, expand, transcript export, persistence and language controls. It replaces visitor text with a generic receipt, making conversation hard to follow. Scroll always jumps to the end; no new-message affordance exists. It has no offline recovery, rate-limit countdown or upload states. Header/composer styling is cramped, and focus goes to Close rather than the composer.

Implement a lazy, feature-flagged replacement using existing React/plain CSS/lucide conventions. Use scoped semantic light/dark tokens, a 400px panel and mobile viewport sheet, visible keyboard focus and 15/22px body type. Keep UK copy: the supplied chat brief's UAE examples conflict with the current market and new synthetic UK brief. No live adviser, model streaming, OCR or speech capability will be falsely advertised. Preserve the legacy component as the flag-off fallback and leave authenticated widgets unchanged.

Backend currently uses reviewed deterministic answers, not Groq generation. Stream that same guarded result through SSE, preserving non-stream fallback. Reuse support references without claiming delivery. Temporary uploads must be consented, bounded and removed; extracted untrusted text cannot override guidance rules. Speech-provider submission must be disclosed before recording fallback. Real-device microphone/screen-reader validation remains a separate manual QA item.
