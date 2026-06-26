// ============================================================
// MelodyHub Meting Node.js 微服务
// 封装 @meting/core，为 Python 后端提供 HTTP API
// 端口：3000（可通过环境变量 METING_PORT 修改）
// 支持：网易云(netease) / QQ(tencent) / 酷狗(kugou) / 百度(baidu) / 酷我(kuwo)
// ============================================================

import http from 'http';
import https from 'https';
import { URL } from 'url';
import Meting from '@meting/core';

const PORT = process.env.METING_PORT || 3000;
const SOURCES = ['netease', 'tencent', 'kugou', 'baidu', 'kuwo'];

function getMeting(source) {
  if (!SOURCES.includes(source)) {
    throw new Error(`Invalid source: ${source}. Supported: ${SOURCES.join(', ')}`);
  }
  const meting = new Meting(source);
  meting.format(true);
  return meting;
}

async function handleSearch(keyword, source, limit) {
  const meting = getMeting(source);
  const result = await meting.search(keyword, { limit: limit || 10 });
  return JSON.parse(result);
}

async function handleUrl(id, source, bitrate) {
  const meting = getMeting(source);
  const result = await meting.url(id, bitrate || 320);
  return JSON.parse(result);
}

async function handleLyric(id, source) {
  const meting = getMeting(source);
  const result = await meting.lyric(id);
  return JSON.parse(result);
}

async function handlePic(id, source, size) {
  const meting = getMeting(source);
  const result = await meting.pic(id, size || 300);
  return JSON.parse(result);
}

const server = http.createServer(async (req, res) => {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Access-Control-Allow-Origin', '*');

  try {
    const parsedUrl = new URL(req.url, `http://${req.headers.host}`);
    const pathname = parsedUrl.pathname;
    const params = parsedUrl.searchParams;

    if (pathname === '/health') {
      res.writeHead(200);
      res.end(JSON.stringify({ status: 'ok', sources: SOURCES }));
      return;
    }

    if (pathname === '/search') {
      const keyword = params.get('keyword');
      const source = params.get('source') || 'netease';
      const limit = parseInt(params.get('limit') || '10', 10);
      if (!keyword) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'keyword is required' }));
        return;
      }
      const result = await handleSearch(keyword, source, limit);
      res.writeHead(200);
      res.end(JSON.stringify(result));
      return;
    }

    if (pathname === '/url') {
      const id = params.get('id');
      const source = params.get('source') || 'netease';
      const bitrate = parseInt(params.get('bitrate') || '320', 10);
      if (!id) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'id is required' }));
        return;
      }
      const result = await handleUrl(id, source, bitrate);
      res.writeHead(200);
      res.end(JSON.stringify(result));
      return;
    }

    if (pathname === '/lyric') {
      const id = params.get('id');
      const source = params.get('source') || 'netease';
      if (!id) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'id is required' }));
        return;
      }
      const result = await handleLyric(id, source);
      res.writeHead(200);
      res.end(JSON.stringify(result));
      return;
    }

    if (pathname === '/pic') {
      const id = params.get('id');
      const source = params.get('source') || 'netease';
      const size = parseInt(params.get('size') || '300', 10);
      if (!id) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'id is required' }));
        return;
      }
      const result = await handlePic(id, source, size);
      res.writeHead(200);
      res.end(JSON.stringify(result));
      return;
    }

    // /pic_proxy — 下载封面图片并以二进制返回，解决 CDN 防盗链问题
    if (pathname === '/pic_proxy') {
      const id = params.get('id');
      const source = params.get('source') || 'netease';
      const size = parseInt(params.get('size') || '500', 10);
      if (!id) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'id is required' }));
        return;
      }
      try {
        const picResult = await handlePic(id, source, size);
        const picUrl = picResult.url;
        if (!picUrl) throw new Error('No URL');

        // 下载图片
        const picData = await new Promise((resolve, reject) => {
          const parsed = new URL(picUrl);
          const mod = parsed.protocol === 'https:' ? https : http;
          const opts = {
            hostname: parsed.hostname,
            path: parsed.pathname + parsed.search,
            headers: {
              'Referer': 'https://music.163.com/',
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
          };
          mod.get(opts, (picRes) => {
            if (picRes.statusCode !== 200) {
              reject(new Error(`HTTP ${picRes.statusCode}`));
              return;
            }
            const chunks = [];
            picRes.on('data', (c) => chunks.push(c));
            picRes.on('end', () => resolve(Buffer.concat(chunks)));
          }).on('error', reject);
        });

        res.writeHead(200, { 'Content-Type': 'image/jpeg', 'Cache-Control': 'max-age=86400' });
        res.end(picData);
      } catch (e) {
        // 失败时返回 1x1 透明 PNG
        const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'base64');
        res.writeHead(200, { 'Content-Type': 'image/png' });
        res.end(png);
      }
      return;
    }

    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not found' }));
  } catch (error) {
    console.error('❌ Meting service error:', error.message);
    res.writeHead(500);
    res.end(JSON.stringify({ error: error.message }));
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`🎵 Meting Node.js service running on http://127.0.0.1:${PORT}`);
  console.log(`   Supported sources: ${SOURCES.join(', ')}`);
});
