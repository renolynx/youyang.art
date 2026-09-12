/* youyang.art — nav, back-to-top, masthead arrow, lightbox. No dependencies. */
(function () {
  'use strict';
  var d = document;

  /* mobile nav */
  var toggle = d.querySelector('.nav-toggle'), nav = d.querySelector('.site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      nav.setAttribute('data-open', String(!open));
      d.body.style.overflow = open ? '' : 'hidden';
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        toggle.setAttribute('aria-expanded', 'false');
        nav.setAttribute('data-open', 'false');
        d.body.style.overflow = '';
      }
    });
  }

  /* masthead arrow scrolls past the masthead */
  var arrow = d.querySelector('.masthead-arrow'), wrap = d.querySelector('.site-wrap');
  if (arrow && wrap) {
    arrow.addEventListener('click', function () {
      window.scrollTo({ top: wrap.offsetTop, behavior: 'smooth' });
    });
  }

  /* back to top */
  var top = d.querySelector('.to-top');
  if (top) {
    var onScroll = function () { top.classList.toggle('is-on', window.scrollY > 600); };
    addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    top.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* contact form with no backend: hand the message to the visitor's mail app */
  var form = d.querySelector('.contact-form[data-mailto]');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = new FormData(form);
      var body = 'From: ' + (f.get('name') || '') + ' <' + (f.get('email') || '') + '>\n\n'
               + (f.get('message') || '');
      location.href = 'mailto:' + form.dataset.mailto
        + '?subject=' + encodeURIComponent('Hello from youyang.art')
        + '&body=' + encodeURIComponent(body);
    });
  }

  /* lightbox */
  var box = d.querySelector('.lightbox');
  if (box) {
    var img = box.querySelector('img'), last = null;
    var open = function (src, alt) {
      img.src = src; img.alt = alt || '';
      box.setAttribute('open', ''); d.body.style.overflow = 'hidden';
      box.querySelector('.lightbox-close').focus();
    };
    var close = function () {
      box.removeAttribute('open'); img.removeAttribute('src');
      d.body.style.overflow = '';
      if (last) last.focus();
    };
    d.addEventListener('click', function (e) {
      var z = e.target.closest('.zoomable');
      if (z) { last = z; open(z.dataset.full || z.currentSrc || z.src, z.alt); return; }
      if (e.target.closest('.lightbox')) close();
    });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && box.hasAttribute('open')) close();
    });
  }
})();
