import { randomBytes, pbkdf2Sync, createCipheriv } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const [source, passwordFile, destination] = process.argv.slice(2);
if (!source || !passwordFile || !destination) {
  throw new Error('Usage: node src/pack-tickets.mjs <ticket folder> <password file> <output>');
}

const manifest = [
  ['12/06', '安妮之家', '16:45–17:00 · 兩張', [['開啟入場票', '12-06 安妮之家.pdf']]],
  ['12/07', 'Rijksmuseum 國家博物館', '15:00–16:00 · 兩張', [['開啟入場票', '12-07 Rijksmuseum 國家博物館.pdf']]],
  ['12/13', '鹿特丹 → 布魯日', '08:41 鹿特丹出發 · 兩人共四張', [
    ['鹿特丹 → 安特衛普 · Yuhan', 'train-rotterdam-3.png'],
    ['鹿特丹 → 安特衛普 · Mengchun', 'train-rotterdam-4.png'],
    ['安特衛普 → 布魯日 · Yuhan', 'train-rotterdam-1.png'],
    ['安特衛普 → 布魯日 · Mengchun', 'train-rotterdam-2.png'],
  ]],
  ['12/14', '布魯日鐘樓', '10:00–10:20 入場 · 兩張', [['開啟入場票', '12-14 布魯日鐘樓.pdf']]],
  ['12/15', '布魯塞爾 → 科隆', '16:22 布魯塞爾出發 · ICE 317', [['開啟火車票', 'train-cologne.pdf']]],
];
const tickets = manifest.map(([date, title, detail, files]) => ({
  date, title, detail,
  files: files.map(([label, name]) => ({
    label, name,
    type: name.endsWith('.pdf') ? 'application/pdf' : 'image/png',
    bytes: readFileSync(join(source, name)).toString('base64'),
  })),
}));
const password = readFileSync(passwordFile, 'utf8').trim();
if (password.length < 24) throw new Error('Use a randomly generated password of at least 24 characters.');
const salt = randomBytes(16);
const iv = randomBytes(12);
const key = pbkdf2Sync(password, salt, 600000, 32, 'sha256');
const cipher = createCipheriv('aes-256-gcm', key, iv);
const encrypted = Buffer.concat([cipher.update(JSON.stringify(tickets), 'utf8'), cipher.final(), cipher.getAuthTag()]);
writeFileSync(destination, JSON.stringify({
  salt: salt.toString('base64'), iv: iv.toString('base64'), encrypted: encrypted.toString('base64'),
}));
