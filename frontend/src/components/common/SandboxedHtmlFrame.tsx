interface SandboxedHtmlFrameProps {
  title: string
  html: string
  height?: string | number
  className?: string
}

const DEFAULT_CSP = [
  "default-src 'none'",
  "script-src 'unsafe-inline' https://cdn.internal.company.com",
  "style-src 'unsafe-inline'",
  "img-src data: blob:",
  "font-src https://cdn.internal.company.com",
  "connect-src 'none'",
  "frame-src 'none'",
  "form-action 'none'",
  "base-uri 'none'",
].join('; ')

export default function SandboxedHtmlFrame({
  title,
  html,
  height = '100%',
  className,
}: SandboxedHtmlFrameProps): JSX.Element {
  const srcDoc = `<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="Content-Security-Policy" content="${DEFAULT_CSP}" />
    <style>
      body { margin: 0; padding: 16px; font-family: sans-serif; }
    </style>
  </head>
  <body>
    ${html}
  </body>
</html>`

  return (
    <iframe
      title={title}
      sandbox="allow-scripts"
      srcDoc={srcDoc}
      className={className}
      style={{
        width: '100%',
        height,
        border: 'none',
      }}
    />
  )
}
