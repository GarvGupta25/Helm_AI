export function Loading() { return <div className="loading" role="status">Loading your workspace…</div>; }
export function ErrorView({ error }: { error: unknown }) { return <div className="error" role="alert">{error instanceof Error ? error.message : 'This page could not load. Please try again.'}</div>; }
