/* ============================================================
   CreditCraze — main.js (GSAP 3 + ScrollTrigger)
   ============================================================ */

(function () {
  'use strict';

  /* ── Wait for GSAP to load ── */
  function whenReady(fn) {
    if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
      fn();
    } else {
      window.addEventListener('load', fn);
    }
  }

  whenReady(function () {
    // Register plugin
    if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
      gsap.registerPlugin(ScrollTrigger);
    }

    /* ── Preloader ── */
    const preloader = document.getElementById('preloader');
    if (preloader) {
      window.addEventListener('load', function () {
        gsap.to(preloader, {
          opacity: 0,
          duration: 0.6,
          delay: 0.3,
          onComplete: function () {
            preloader.classList.add('hidden');
          }
        });
      });
      // Fallback after 2.5s
      setTimeout(function () {
        if (preloader) preloader.classList.add('hidden');
      }, 2500);
    }

    /* ── Scroll progress bar ── */
    const progressBar = document.getElementById('scroll-progress');
    if (progressBar) {
      window.addEventListener('scroll', function () {
        const scrolled = window.scrollY;
        const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
        const pct = maxScroll > 0 ? (scrolled / maxScroll) * 100 : 0;
        progressBar.style.width = pct + '%';
      }, { passive: true });
    }

    /* ── Navbar glassmorphism on scroll ── */
    const navbar = document.querySelector('.navbar');
    if (navbar) {
      window.addEventListener('scroll', function () {
        if (window.scrollY > 60) {
          navbar.classList.add('scrolled');
        } else {
          navbar.classList.remove('scrolled');
        }
      }, { passive: true });
    }

    /* ── Scroll-to-top button ── */
    const scrollTop = document.querySelector('.scroll-top');
    if (scrollTop) {
      window.addEventListener('scroll', function () {
        if (window.scrollY > 400) {
          scrollTop.classList.add('visible');
        } else {
          scrollTop.classList.remove('visible');
        }
      }, { passive: true });
      scrollTop.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    /* ── Copyright year ── */
    const yearEl = document.getElementById('copy-year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();

    /* ── Hero animations (if hero exists) ── */
    const heroTitle = document.querySelector('.hero__title');
    if (heroTitle && typeof gsap !== 'undefined') {
      const tl = gsap.timeline({ delay: 0.5 });
      const eyebrow = document.querySelector('.hero__eyebrow');
      const desc    = document.querySelector('.hero__desc');
      const actions = document.querySelector('.hero__actions');
      const card    = document.querySelector('.hero__card-wrap');

      if (eyebrow) tl.from(eyebrow, { y: 20, opacity: 0, duration: 0.6, ease: 'power3.out' });
      tl.from(heroTitle, { y: 30, opacity: 0, duration: 0.8, ease: 'power3.out' }, '-=0.3');
      if (desc)    tl.from(desc,    { y: 20, opacity: 0, duration: 0.6, ease: 'power3.out' }, '-=0.4');
      if (actions) tl.from(actions, { y: 20, opacity: 0, duration: 0.6, ease: 'power3.out' }, '-=0.3');
      if (card)    tl.from(card,    { x: 40, opacity: 0, duration: 0.8, ease: 'power3.out' }, '-=0.6');
    }

    /* ── Fade-up on scroll ── */
    if (typeof gsap !== 'undefined') {
      document.querySelectorAll('.fade-up').forEach(function (el) {
        ScrollTrigger.create({
          trigger: el,
          start: 'top 88%',
          onEnter: function () {
            gsap.to(el, { y: 0, opacity: 1, duration: 0.7, ease: 'power3.out' });
          }
        });
      });

      /* ── Stagger items ── */
      document.querySelectorAll('.stagger-group').forEach(function (group) {
        const items = group.querySelectorAll('.stagger-item');
        if (!items.length) return;
        ScrollTrigger.create({
          trigger: group,
          start: 'top 85%',
          onEnter: function () {
            gsap.to(items, {
              y: 0, opacity: 1, duration: 0.6,
              stagger: 0.12,
              ease: 'power3.out'
            });
          }
        });
      });

      /* ── Fade-in ── */
      document.querySelectorAll('.fade-in').forEach(function (el) {
        ScrollTrigger.create({
          trigger: el,
          start: 'top 90%',
          onEnter: function () {
            gsap.to(el, { opacity: 1, duration: 0.8, ease: 'power2.out' });
          }
        });
      });
    }

    /* ── 3D credit card tilt ── */
    document.querySelectorAll('.cc-card[data-tilt]').forEach(function (card) {
      card.addEventListener('mousemove', function (e) {
        const rect = card.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width  - 0.5;
        const y = (e.clientY - rect.top)  / rect.height - 0.5;
        if (typeof gsap !== 'undefined') {
          gsap.to(card, {
            rotateY: x * 20, rotateX: -y * 14,
            transformPerspective: 800,
            scale: 1.04,
            duration: 0.4, ease: 'power2.out'
          });
        }
      });
      card.addEventListener('mouseleave', function () {
        if (typeof gsap !== 'undefined') {
          gsap.to(card, {
            rotateY: 0, rotateX: 0, scale: 1,
            duration: 0.5, ease: 'elastic.out(1,0.7)'
          });
        }
      });
    });

    /* ── Counter animation for stats-bar ── */
    document.querySelectorAll('[data-count]').forEach(function (el) {
      const target = parseFloat(el.dataset.count);
      const suffix = el.dataset.suffix || '';
      if (typeof gsap !== 'undefined') {
        ScrollTrigger.create({
          trigger: el,
          start: 'top 90%',
          once: true,
          onEnter: function () {
            gsap.from({ val: 0 }, {
              val: target,
              duration: 1.8,
              ease: 'power2.out',
              onUpdate: function () {
                el.textContent = Math.floor(this.targets()[0].val).toLocaleString() + suffix;
              }
            });
          }
        });
      }
    });

    /* ── Chat auto-scroll ── */
    const chatMsgs = document.querySelector('.chat-messages');
    if (chatMsgs) {
      chatMsgs.scrollTop = chatMsgs.scrollHeight;
    }

    /* ── Credibot quick chips ── */
    document.querySelectorAll('.chip-btn[data-prompt]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const input = document.querySelector('.chat-input');
        if (input) {
          input.value = btn.dataset.prompt;
          input.focus();
        }
      });
    });

    /* ── Card filter form auto-submit on checkbox change ── */
    document.querySelectorAll('.filter-auto-submit input[type="checkbox"]').forEach(function (cb) {
      cb.addEventListener('change', function () {
        cb.closest('form').submit();
      });
    });

    /* ── AI card summary loader ── */
    const aiBox = document.querySelector('[data-ai-card-id]');
    if (aiBox) {
      const cardId = aiBox.dataset.aiCardId;
      const content = aiBox.querySelector('.ai-summary-content');
      if (content) {
        content.innerHTML = '<div class="ai-loading"><span></span><span></span><span></span></div>';
        fetch('/ai_card_summary/' + cardId)
          .then(function (r) { return r.json(); })
          .then(function (data) {
            content.textContent = data.summary || 'Summary not available.';
            if (typeof gsap !== 'undefined') {
              gsap.from(content, { opacity: 0, y: 10, duration: 0.5 });
            }
          })
          .catch(function () {
            content.textContent = 'AI summary temporarily unavailable.';
          });
      }
    }

    /* ── Comparison table best/worst highlighting ── */
    const numericRows = document.querySelectorAll('.comp-row-numeric');
    numericRows.forEach(function (row) {
      const cells = Array.from(row.querySelectorAll('td.comp-cell'));
      const vals  = cells.map(function (c) {
        const n = parseFloat(c.textContent.replace(/[^0-9.]/g, ''));
        return isNaN(n) ? null : n;
      });
      const valid = vals.filter(function (v) { return v !== null; });
      if (!valid.length) return;
      const direction = row.dataset.better === 'high' ? 'high' : 'low';
      const best  = direction === 'low' ? Math.min(...valid) : Math.max(...valid);
      const worst = direction === 'low' ? Math.max(...valid) : Math.min(...valid);
      cells.forEach(function (c, i) {
        if (vals[i] === null) return;
        if (vals[i] === best)  c.classList.add('cell-best');
        if (vals[i] === worst) c.classList.add('cell-worst');
      });
    });

    /* ── Flash message auto-dismiss ── */
    document.querySelectorAll('.alert-auto').forEach(function (el) {
      setTimeout(function () {
        if (typeof gsap !== 'undefined') {
          gsap.to(el, { opacity: 0, height: 0, marginBottom: 0, duration: 0.4, onComplete: function () { el.remove(); } });
        } else {
          el.remove();
        }
      }, 4000);
    });

  }); // end whenReady
})();
