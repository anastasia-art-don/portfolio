const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const root = __dirname;
const port = Number(process.env.PORT || 4174);
const types = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.mp4':'video/mp4'};
http.createServer((req, res) => {
  let pathname;
  try { pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname); } catch { res.writeHead(400).end(); return; }
  const file = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
  if (!file.startsWith(root + path.sep) || !types[path.extname(file)]) { res.writeHead(403).end(); return; }
  fs.readFile(file, (error, data) => { if (error) { res.writeHead(404).end('Not found'); return; }
  // Safari plays a video only when the server answers requests for part of the file.
  const range = /bytes=(\d*)-(\d*)/.exec(req.headers.range || '');
  if (range) { const start = Number(range[1] || 0), end = range[2] ? Number(range[2]) : data.length - 1; res.writeHead(206, {'Content-Type':types[path.extname(file)],'Content-Range':`bytes ${start}-${end}/${data.length}`,'Accept-Ranges':'bytes','Cache-Control':'no-cache'}); res.end(data.subarray(start, end + 1)); return; }
  res.writeHead(200, {'Content-Type':types[path.extname(file)] || 'application/octet-stream','Cache-Control':'no-cache'}); res.end(req.method === 'HEAD' ? undefined : data); });
}).listen(port, '127.0.0.1', () => console.log(`Portfolio: http://127.0.0.1:${port}`));
