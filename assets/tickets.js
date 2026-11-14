const form = document.querySelector('#unlock');
const password = document.querySelector('#password');
const status = document.querySelector('#status');
const wallet = document.querySelector('#wallet');
const list = document.querySelector('#tickets');
const lock = document.querySelector('#lock');
const urls = [];
const decode = (base64) => Uint8Array.from(atob(base64), (character) => character.charCodeAt(0));

async function decrypt(bundle, secret) {
  const material = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret), 'PBKDF2', false, ['deriveKey'],
  );
  const key = await crypto.subtle.deriveKey(
    { name: 'PBKDF2', hash: 'SHA-256', salt: decode(bundle.salt), iterations: 600000 },
    material, { name: 'AES-GCM', length: 256 }, false, ['decrypt'],
  );
  const plaintext = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: decode(bundle.iv) }, key, decode(bundle.encrypted),
  );
  return JSON.parse(new TextDecoder().decode(plaintext));
}

function ticketLink(text, url) {
  const link = document.createElement('a');
  link.className = 'ticket-link';
  link.href = url;
  link.textContent = text;
  return link;
}

function show(tickets) {
  for (const ticket of tickets) {
    const article = document.createElement('article');
    const date = document.createElement('p');
    date.textContent = ticket.date;
    const title = document.createElement('h2');
    title.textContent = ticket.title;
    const detail = document.createElement('p');
    detail.textContent = ticket.detail;
    article.append(date, title, detail);
    for (const file of ticket.files) {
      const url = URL.createObjectURL(new Blob([decode(file.bytes)], { type: file.type }));
      urls.push(url);
      const actions = document.createElement('div');
      actions.className = 'ticket-actions';
      const open = ticketLink(file.label, url);
      open.target = '_blank';
      open.rel = 'noopener noreferrer';
      const download = ticketLink('下載', url);
      download.download = file.name;
      download.setAttribute('aria-label', '下載 ' + file.label);
      actions.append(open, download);
      article.append(actions);
    }
    list.append(article);
  }
}

function clearTickets() {
  for (const url of urls.splice(0)) URL.revokeObjectURL(url);
  list.replaceChildren();
  wallet.hidden = true;
  form.hidden = false;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = form.querySelector('button');
  button.disabled = true;
  status.textContent = '正在解鎖…';
  const secret = password.value.trim();
  password.value = '';
  try {
    const response = await fetch('assets/tickets.enc.json', { cache: 'no-store' });
    if (!response.ok) throw new Error('Could not load the encrypted tickets');
    show(await decrypt(await response.json(), secret));
    form.hidden = true;
    wallet.hidden = false;
    status.textContent = '票夾已解鎖。';
    lock.focus();
  } catch (error) {
    clearTickets();
    status.textContent = error.name === 'OperationError'
      ? '密碼不正確，請再試一次。'
      : '無法開啟票夾，請確認網路連線後再試。';
    password.focus();
  } finally {
    button.disabled = false;
  }
});

lock.addEventListener('click', () => {
  clearTickets();
  status.textContent = '票夾已鎖定。';
  password.focus();
});
window.addEventListener('pagehide', clearTickets);
