/* youyang.art — nav, back-to-top, masthead arrow, lightbox. No dependencies. */
(function () {
  'use strict';
  var d = document;
  var mobile = window.matchMedia('(max-width: 768px)');
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var box = d.querySelector('.lightbox');
  var syncScrollLock = function () {
    var menuOpen = nav && mobile.matches && nav.getAttribute('data-open') === 'true';
    d.body.style.overflow = menuOpen || (box && box.hasAttribute('open')) ? 'hidden' : '';
  };

  /* mobile nav */
  var toggle = d.querySelector('.nav-toggle'), nav = d.querySelector('.site-nav');
  if (toggle && nav) {
    var setNavOpen = function (open) {
      open = mobile.matches && open;
      toggle.setAttribute('aria-expanded', String(open));
      nav.setAttribute('data-open', String(open));
      nav.inert = mobile.matches && !open;
      if (nav.inert) nav.setAttribute('aria-hidden', 'true');
      else nav.removeAttribute('aria-hidden');
      syncScrollLock();
    };
    toggle.addEventListener('click', function () {
      setNavOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setNavOpen(false);
    });
    d.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setNavOpen(false);
        toggle.focus();
      }
    });
    var resetNav = function () {
      var hadFocus = nav.contains(d.activeElement);
      setNavOpen(false);
      if (hadFocus && mobile.matches) toggle.focus();
    };
    if (mobile.addEventListener) mobile.addEventListener('change', resetNav);
    else mobile.addListener(resetNav);
    setNavOpen(false);
  }

  /* masthead arrow scrolls past the masthead */
  var arrow = d.querySelector('.masthead-arrow'), wrap = d.querySelector('.site-wrap');
  if (arrow && wrap) {
    arrow.addEventListener('click', function () {
      window.scrollTo({ top: wrap.offsetTop, behavior: reducedMotion.matches ? 'auto' : 'smooth' });
    });
  }

  /* back to top */
  var top = d.querySelector('.to-top');
  if (top) {
    var onScroll = function () { top.classList.toggle('is-on', window.scrollY > 600); };
    addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    top.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: reducedMotion.matches ? 'auto' : 'smooth' });
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
  if (box) {
    var img = box.querySelector('img'), closeButton = box.querySelector('.lightbox-close'), last = null;
    var enlargeLabel = d.documentElement.lang.indexOf('zh') === 0 ? '\u653e\u5927\u56fe\u7247' : 'Enlarge image';
    d.querySelectorAll('.zoomable').forEach(function (z) {
      if (!z.matches('button, a[href]')) {
        z.setAttribute('role', 'button');
        z.setAttribute('tabindex', '0');
      }
      if (!z.hasAttribute('aria-label')) {
        z.setAttribute('aria-label', enlargeLabel + (z.alt ? ': ' + z.alt : ''));
      }
      z.setAttribute('aria-haspopup', 'dialog');
    });
    var open = function (z) {
      last = z;
      img.src = z.dataset.full || z.currentSrc || z.src;
      img.alt = z.alt || '';
      box.setAttribute('open', '');
      syncScrollLock();
      closeButton.focus();
    };
    var close = function () {
      if (!box.hasAttribute('open')) return;
      box.removeAttribute('open'); img.removeAttribute('src');
      syncScrollLock();
      if (last && last.isConnected) last.focus();
    };
    d.addEventListener('click', function (e) {
      var z = e.target.closest('.zoomable');
      if (z && !box.hasAttribute('open')) { open(z); return; }
      if (e.target === box || e.target.closest('.lightbox-close')) close();
    });
    d.addEventListener('keydown', function (e) {
      if (box.hasAttribute('open')) {
        if (e.key === 'Escape') { e.preventDefault(); close(); }
        /* The close button is the dialog's only interactive element. */
        else if (e.key === 'Tab') { e.preventDefault(); closeButton.focus(); }
        return;
      }
      var z = e.target.closest('.zoomable');
      if (z && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        open(z);
      }
    });
    d.addEventListener('focusin', function (e) {
      if (box.hasAttribute('open') && !box.contains(e.target)) closeButton.focus();
    });
  }
})();
