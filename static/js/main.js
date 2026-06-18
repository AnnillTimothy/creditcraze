(function () {
  'use strict';

  function onReady(callback) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', callback);
    } else {
      callback();
    }
  }

  function withGSAP(callback) {
    if (typeof window.gsap !== 'undefined') {
      callback(window.gsap, window.ScrollTrigger);
    } else {
      window.addEventListener('load', function () {
        callback(window.gsap, window.ScrollTrigger);
      });
    }
  }

  function readConsent() {
    try {
      return JSON.parse(localStorage.getItem(window.CREDIT_COMPASS.consentKey) || 'null');
    } catch (error) {
      return null;
    }
  }

  function writeConsent(consent) {
    localStorage.setItem(window.CREDIT_COMPASS.consentKey, JSON.stringify(consent));
    window.dataLayer.push({ event: 'consent_update', consent: consent });
  }

  function syncCookieInputs(consent) {
    document.querySelectorAll('[data-cookie-key]').forEach(function (input) {
      if (input.disabled) return;
      input.checked = Boolean(consent[input.dataset.cookieKey]);
    });
  }

  function saveConsent(mode) {
    var consent = { essential: true, analytics: false, personalization: false };

    if (mode === 'accept') {
      consent.analytics = true;
      consent.personalization = true;
    }

    if (mode === 'custom') {
      document.querySelectorAll('[data-cookie-key]').forEach(function (input) {
        consent[input.dataset.cookieKey] = input.disabled ? true : Boolean(input.checked);
      });
    }

    writeConsent(consent);
    var banner = document.getElementById('cookieBanner');
    var panel = document.getElementById('cookiePanel');
    if (banner) banner.hidden = true;
    if (panel) panel.hidden = true;
  }

  onReady(function () {
    var progressBar = document.getElementById('scroll-progress');
    var navbar = document.querySelector('.navbar');
    var scrollTop = document.querySelector('.scroll-top');
    var yearEl = document.getElementById('copy-year');
    var preloader = document.getElementById('preloader');
    var banner = document.getElementById('cookieBanner');
    var panel = document.getElementById('cookiePanel');
    var cookieCopy = document.getElementById('cookieBannerCopy');

    if (yearEl) yearEl.textContent = new Date().getFullYear();
    if (cookieCopy && window.CREDIT_COMPASS) cookieCopy.textContent = window.CREDIT_COMPASS.cookieCopy;

    var storedConsent = readConsent();
    if (banner && !storedConsent) banner.hidden = false;
    if (storedConsent) syncCookieInputs(storedConsent);

    document.querySelectorAll('[data-cookie-action]').forEach(function (button) {
      button.addEventListener('click', function () {
        var action = button.dataset.cookieAction;
        if (action === 'essential') {
          saveConsent('essential');
        } else if (action === 'accept') {
          saveConsent('accept');
        } else if (panel) {
          panel.hidden = false;
          if (banner) banner.hidden = true;
          syncCookieInputs(storedConsent || { essential: true, analytics: false, personalization: false });
        }
      });
    });

    document.querySelectorAll('[data-cookie-save]').forEach(function (button) {
      button.addEventListener('click', function () {
        saveConsent(button.dataset.cookieSave);
      });
    });

    var panelClose = document.querySelector('.cookie-panel__close');
    if (panelClose) {
      panelClose.addEventListener('click', function () {
        if (panel) panel.hidden = true;
        if (!readConsent() && banner) banner.hidden = false;
      });
    }

    window.addEventListener('scroll', function () {
      var scrolled = window.scrollY;
      var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      if (progressBar) progressBar.style.width = (maxScroll > 0 ? (scrolled / maxScroll) * 100 : 0) + '%';
      if (navbar) navbar.classList.toggle('scrolled', scrolled > 48);
      if (scrollTop) scrollTop.classList.toggle('visible', scrolled > 400);
    }, { passive: true });

    if (scrollTop) {
      scrollTop.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    if (preloader) {
      window.addEventListener('load', function () {
        preloader.classList.add('hidden');
      });
      setTimeout(function () {
        preloader.classList.add('hidden');
      }, 2400);
    }

    document.querySelectorAll('.cc-card[data-tilt]').forEach(function (card) {
      card.addEventListener('mousemove', function (event) {
        var rect = card.getBoundingClientRect();
        var x = (event.clientX - rect.left) / rect.width - 0.5;
        var y = (event.clientY - rect.top) / rect.height - 0.5;
        if (window.gsap) {
          window.gsap.to(card, {
            rotateY: x * 16,
            rotateX: -y * 12,
            scale: 1.03,
            transformPerspective: 900,
            duration: 0.32,
            ease: 'power2.out'
          });
        }
      });
      card.addEventListener('mouseleave', function () {
        if (window.gsap) {
          window.gsap.to(card, {
            rotateY: 0,
            rotateX: 0,
            scale: 1,
            duration: 0.45,
            ease: 'power2.out'
          });
        }
      });
    });

    var chatMsgs = document.querySelector('.chat-messages');
    if (chatMsgs) chatMsgs.scrollTop = chatMsgs.scrollHeight;

    document.querySelectorAll('.chip-btn[data-prompt]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var input = document.querySelector('.chat-input');
        if (input) {
          input.value = btn.dataset.prompt;
          input.focus();
        }
      });
    });

    document.querySelectorAll('.filter-auto-submit input[type="checkbox"]').forEach(function (checkbox) {
      checkbox.addEventListener('change', function () {
        checkbox.closest('form').submit();
      });
    });

    var aiBox = document.querySelector('[data-ai-card-id]');
    if (aiBox) {
      var cardId = aiBox.dataset.aiCardId;
      var content = aiBox.querySelector('.ai-summary-content');
      if (content) {
        content.innerHTML = '<div class="ai-loading"><span></span><span></span><span></span></div>';
        fetch('/ai_card_summary/' + cardId)
          .then(function (response) { return response.json(); })
          .then(function (data) {
            content.textContent = data.summary || 'Summary not available.';
          })
          .catch(function () {
            content.textContent = 'AI summary temporarily unavailable.';
          });
      }
    }

    document.querySelectorAll('.comp-row-numeric').forEach(function (row) {
      var cells = Array.from(row.querySelectorAll('td.comp-cell'));
      var values = cells.map(function (cell) {
        var number = parseFloat(cell.textContent.replace(/[^0-9.]/g, ''));
        return Number.isNaN(number) ? null : number;
      });
      var valid = values.filter(function (value) { return value !== null; });
      if (!valid.length) return;
      var prefersHigh = row.dataset.better === 'high';
      var best = prefersHigh ? Math.max.apply(Math, valid) : Math.min.apply(Math, valid);
      var worst = prefersHigh ? Math.min.apply(Math, valid) : Math.max.apply(Math, valid);
      cells.forEach(function (cell, index) {
        if (values[index] === null) return;
        if (values[index] === best) cell.classList.add('cell-best');
        if (values[index] === worst) cell.classList.add('cell-worst');
      });
    });

    document.querySelectorAll('.alert-auto').forEach(function (alert) {
      setTimeout(function () {
        alert.remove();
      }, 3600);
    });

    withGSAP(function (gsap, ScrollTrigger) {
      if (!gsap) return;
      if (ScrollTrigger) gsap.registerPlugin(ScrollTrigger);

      var heroTimeline = gsap.timeline({ delay: 0.25 });
      if (document.querySelector('.hero__eyebrow')) heroTimeline.from('.hero__eyebrow', { y: 18, opacity: 0, duration: 0.55, ease: 'power3.out' });
      if (document.querySelector('.hero__title')) heroTimeline.from('.hero__title', { y: 28, opacity: 0, duration: 0.75, ease: 'power3.out' }, '-=0.2');
      if (document.querySelector('.hero__desc')) heroTimeline.from('.hero__desc', { y: 20, opacity: 0, duration: 0.65, ease: 'power3.out' }, '-=0.35');
      if (document.querySelector('.hero__actions')) heroTimeline.from('.hero__actions', { y: 20, opacity: 0, duration: 0.55, ease: 'power3.out' }, '-=0.35');
      if (document.querySelector('.compass-visual')) heroTimeline.from('.compass-visual', { x: 26, opacity: 0, duration: 0.85, ease: 'power3.out' }, '-=0.55');

      gsap.to('.orbit--major', { rotate: 360, duration: 28, ease: 'none', repeat: -1, transformOrigin: '50% 50%' });
      gsap.to('.orbit--alt', { rotate: -360, duration: 32, ease: 'none', repeat: -1, transformOrigin: '50% 50%' });
      gsap.to('.orbit--minor', { rotate: 360, duration: 24, ease: 'none', repeat: -1, transformOrigin: '50% 50%' });
      gsap.to('.compass-needle', { rotate: 6, duration: 2.6, yoyo: true, repeat: -1, ease: 'sine.inOut', transformOrigin: '50% 50%' });
      gsap.to('.orbit-node', { scale: 1.18, opacity: 0.82, duration: 1.8, yoyo: true, repeat: -1, stagger: 0.18, ease: 'sine.inOut' });

      document.querySelectorAll('.fade-up').forEach(function (element) {
        gsap.fromTo(element, { y: 28, opacity: 0 }, {
          y: 0,
          opacity: 1,
          duration: 0.75,
          ease: 'power3.out',
          scrollTrigger: ScrollTrigger ? { trigger: element, start: 'top 86%' } : undefined
        });
      });

      document.querySelectorAll('.fade-in').forEach(function (element) {
        gsap.fromTo(element, { opacity: 0 }, {
          opacity: 1,
          duration: 0.85,
          ease: 'power2.out',
          scrollTrigger: ScrollTrigger ? { trigger: element, start: 'top 90%' } : undefined
        });
      });

      document.querySelectorAll('.stagger-group').forEach(function (group) {
        var items = group.querySelectorAll('.stagger-item');
        if (!items.length) return;
        gsap.fromTo(items, { y: 26, opacity: 0 }, {
          y: 0,
          opacity: 1,
          duration: 0.7,
          stagger: 0.12,
          ease: 'power3.out',
          scrollTrigger: ScrollTrigger ? { trigger: group, start: 'top 84%' } : undefined
        });
      });

      document.querySelectorAll('[data-count]').forEach(function (element) {
        var target = parseFloat(element.dataset.count);
        var suffix = element.dataset.suffix || '';
        if (Number.isNaN(target)) return;
        gsap.fromTo({ value: 0 }, { value: 0 }, {
          value: target,
          duration: 1.8,
          ease: 'power2.out',
          paused: true,
          onUpdate: function () {
            element.textContent = Math.floor(this.targets()[0].value).toLocaleString() + suffix;
          },
          scrollTrigger: ScrollTrigger ? {
            trigger: element,
            start: 'top 88%',
            once: true,
            onEnter: function (self) {
              self.animation.play();
            }
          } : undefined
        });
      });
    });
  });
})();
