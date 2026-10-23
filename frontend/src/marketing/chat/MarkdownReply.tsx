import Markdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';

// Small bounded pipe tables, with text-only cells. CommonMark handles the rest.
// Avoid the much larger GFM autolink/footnote pipeline in a small public widget.
export function MarkdownReply({ text }: { text: string }) {
  const blocks = text.split(/(\n?\|[^\n]+\|\n\|[\s:|\-]+\|\n(?:\|[^\n]+\|\n?){1,20})/g);
  return <>{blocks.map((block, i) => {
    if (/^\n?\|[^\n]+\|\n\|[\s:|\-]+\|/.test(block)) {
      const rows = block.trim().split('\n').map(row => row.split('|').slice(1, -1).map(cell => cell.trim()));
      return <table key={i}><thead><tr>{rows[0].map((cell, j) => <th key={j}>{cell}</th>)}</tr></thead><tbody>{rows.slice(2).map((row, r) => <tr key={r}>{row.map((cell, c) => <td key={c}>{cell}</td>)}</tr>)}</tbody></table>;
    }
    return <Markdown key={i} rehypePlugins={[rehypeSanitize]} components={{ a: ({ href, children }) => href && /^(https?:\/\/|\/[^/])/.test(href) ? <a href={href} target="_blank" rel="noopener noreferrer">{children}</a> : <span>{children}</span> }}>{block}</Markdown>;
  })}</>;
}
