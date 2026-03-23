// ===================================================================
// Luke J. Evans - Academic Website Scripts
// ===================================================================

document.addEventListener('DOMContentLoaded', () => {

  // --- Navbar scroll behavior ---
  const nav = document.getElementById('nav');
  const handleScroll = () => {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  };
  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();

  // --- Mobile menu toggle ---
  const navToggle = document.getElementById('nav-toggle');
  const navLinks = document.getElementById('nav-links');

  navToggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
    document.body.style.overflow = navLinks.classList.contains('active') ? 'hidden' : '';
  });

  // Close mobile menu on link click
  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('active');
      document.body.style.overflow = '';
    });
  });

  // --- Smooth scroll for anchor links ---
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        const offset = nav.offsetHeight + 16;
        const top = target.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  // --- Scroll-triggered fade-in animations ---
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -40px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Add fade-in to key elements
  const animateSelectors = [
    '.about-image-wrapper',
    '.about-text-col',
    '.timeline-item',
    '.research-card',
    '.pub-item',
    '.tool-card',
    '.grant-card',
    '.teaching-card',
    '.media-card',
    '.deforestation-text',
    '.deforestation-image',
    '.contact-info',
    '.contact-map',
    '.pub-book',
    '.management-plans',
    '.funders-section'
  ];

  animateSelectors.forEach(selector => {
    document.querySelectorAll(selector).forEach((el, i) => {
      el.classList.add('fade-in');
      el.style.transitionDelay = `${Math.min(i * 0.08, 0.4)}s`;
      observer.observe(el);
    });
  });

  // --- Gallery infinite scroll duplication ---
  const galleryTrack = document.querySelector('.gallery-track');
  if (galleryTrack) {
    const items = galleryTrack.innerHTML;
    galleryTrack.innerHTML = items + items;
  }

  // --- Active nav highlighting ---
  const sections = document.querySelectorAll('section[id]');
  const navLinksAll = document.querySelectorAll('.nav-links a');

  const highlightNav = () => {
    const scrollPos = window.scrollY + nav.offsetHeight + 100;

    sections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute('id');

      if (scrollPos >= top && scrollPos < top + height) {
        navLinksAll.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${id}`) {
            link.classList.add('active');
          }
        });
      }
    });
  };

  window.addEventListener('scroll', highlightNav, { passive: true });

  // --- Counter animation for hero stats ---
  const animateCounters = () => {
    const stats = document.querySelectorAll('.stat-num');
    stats.forEach(stat => {
      const text = stat.textContent;
      const hasPlus = text.includes('+');
      const hasDollar = text.includes('$');
      const hasK = text.includes('K');

      let target;
      if (hasDollar) {
        target = parseInt(text.replace(/[$K+,]/g, ''));
      } else {
        target = parseInt(text.replace(/[^0-9]/g, ''));
      }

      if (isNaN(target)) return;

      let current = 0;
      const increment = target / 40;
      const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
          current = target;
          clearInterval(timer);
        }

        let display = Math.round(current);
        if (hasDollar) display = '$' + display + (hasK ? 'K' : '');
        if (hasPlus) display += '+';
        if (!hasDollar && !hasPlus && text === '5') display = Math.round(current);

        stat.textContent = display;
      }, 40);
    });
  };

  // Run counter animation when hero is visible
  const heroObserver = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      animateCounters();
      heroObserver.disconnect();
    }
  });

  const heroStats = document.querySelector('.hero-stats');
  if (heroStats) {
    heroObserver.observe(heroStats);
  }


  // --- Dynamic publication loading from Google Scholar JSON ---
  fetch('publications.json?' + Date.now())
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(data => {
      const container = document.getElementById('pub-list-container');
      if (!container || !data.publications || data.publications.length === 0) return;

      const pubs = data.publications
        .filter(p => p.year > 0)
        .sort((a, b) => b.year - a.year);

      container.innerHTML = pubs.map(pub => {
        const journal = pub.journal
          ? pub.journal + (pub.volume_info ? ', ' + pub.volume_info : '')
          : '';
        return `
          <div class="pub-item">
            <span class="pub-year">${pub.year}</span>
            <div class="pub-details">
              <p class="pub-authors">${pub.authors}</p>
              <p class="pub-title">${pub.title}</p>
              ${journal ? `<p class="pub-journal">${journal}</p>` : ''}
            </div>
          </div>`;
      }).join('');

      const statsEl = document.getElementById('scholar-stats');
      if (statsEl && data.profile) {
        statsEl.innerHTML = '<i class="fas fa-graduation-cap"></i> Google Scholar: '
          + data.profile.citations + '+ citations &middot; h-index '
          + data.profile.h_index;
      }

      // Update hero stats with latest Scholar data
      if (data.profile) {
        const pubCount = document.getElementById('stat-publications');
        const citCount = document.getElementById('stat-citations');
        if (pubCount) pubCount.textContent = data.publications.length + '+';
        if (citCount) citCount.textContent = data.profile.citations + '+';
      }

      container.querySelectorAll('.pub-item').forEach((el, i) => {
        el.classList.add('fade-in');
        el.style.transitionDelay = `${Math.min(i * 0.08, 0.4)}s`;
        observer.observe(el);
      });
    })
    .catch(() => { /* Silent fail — hardcoded publications remain visible */ });

});