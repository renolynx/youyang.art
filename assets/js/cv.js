/* youyang.art — CV unlock. The CV ships encrypted (AES-256-CBC + HMAC-SHA256, PBKDF2 keys);
   the password never leaves the browser. */
(function () {
  'use strict';
  var form = document.getElementById('cv-form'), blobEl = document.getElementById('cv-blob');
  if (!form || !blobEl || !window.crypto || !crypto.subtle) return;
  var blob = JSON.parse(blobEl.textContent);
  var out = document.getElementById('cv-content'), lock = document.getElementById('cv-lock');
  var err = document.getElementById('cv-error'), button = form.querySelector('button');
  var b64 = function (s) { return Uint8Array.from(atob(s), function (c) { return c.charCodeAt(0); }); };
  var equal = function (a, b) { if (a.length !== b.length) return false; var d = 0; for (var i = 0; i < a.length; i++) d |= a[i] ^ b[i]; return d === 0; };

  function unlock(password) {
    var enc = new TextEncoder();
    return crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveBits'])
      .then(function (base) {
        return crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt: b64(blob.salt), iterations: blob.iter }, base, 80 * 8);
      })
      .then(function (bits) {
        var k = new Uint8Array(bits), key = k.slice(0, 32), iv = k.slice(32, 48), mac = k.slice(48);
        var ct = b64(blob.ct);
        return crypto.subtle.importKey('raw', mac, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
          .then(function (mk) { return crypto.subtle.sign('HMAC', mk, ct); })
          .then(function (tag) {
            if (!equal(new Uint8Array(tag), b64(blob.tag))) throw new Error('bad password');
            return crypto.subtle.importKey('raw', key, 'AES-CBC', false, ['decrypt']);
          })
          .then(function (ak) { return crypto.subtle.decrypt({ name: 'AES-CBC', iv: iv }, ak, ct); })
          .then(function (plain) { return new TextDecoder().decode(plain); });
      });
  }
  function show(htmlText) {
    out.innerHTML = htmlText;
    out.hidden = false;
    lock.hidden = true;
    out.setAttribute('tabindex', '-1');
    out.focus();
  }
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var pass = form.querySelector('input').value;
    err.hidden = true; button.disabled = true;
    unlock(pass).then(function (text) {
      try { sessionStorage.setItem('cv-pass', pass); } catch (_) {}
      show(text);
    }).catch(function () {
      err.hidden = false; button.disabled = false; form.querySelector('input').select();
    });
  });
  try {
    var saved = sessionStorage.getItem('cv-pass');
    if (saved) unlock(saved).then(show).catch(function () {});
  } catch (_) {}
})();
