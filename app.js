(function () {
  const MAX_DAYS = 90;
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const minDate = new Date(today);
  minDate.setDate(minDate.getDate() - MAX_DAYS);

  let currentMonth = today.getFullYear();
  let currentMonthIdx = today.getMonth();
  let selectedDate = formatDate(today);
  let availableDates = [];

  // ========== 工具函数 ==========

  function formatDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  function parseDate(str) {
    const [y, m, d] = str.split('-').map(Number);
    return new Date(y, m - 1, d);
  }

  function formatChineseDate(str) {
    const d = parseDate(str);
    const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
    return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 星期${weekdays[d.getDay()]}`;
  }

  function isInRange(d) {
    return d >= minDate && d <= today;
  }

  // ========== 扫描可用日期（每天缓存一次）==========

  async function scanAvailableDates() {
    const cacheKey = 'ai_daily_dates_' + formatDate(today);
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) return JSON.parse(cached);
    } catch (e) {}

    const dates = [];
    const d = new Date(today);
    for (let i = 0; i <= MAX_DAYS; i++) {
      const dateStr = formatDate(d);
      try {
        const resp = await fetch(`data/${dateStr}.json`, { method: 'HEAD' });
        if (resp.ok) dates.push(dateStr);
      } catch (e) {}
      d.setDate(d.getDate() - 1);
    }

    try {
      // 清理旧缓存，只保留今天的
      Object.keys(localStorage)
        .filter(k => k.startsWith('ai_daily_dates_') && k !== cacheKey)
        .forEach(k => localStorage.removeItem(k));
      localStorage.setItem(cacheKey, JSON.stringify(dates));
    } catch (e) {}

    return dates;
  }

  // ========== 日历渲染 ==========

  function renderCalendar() {
    const grid = document.getElementById('calendarGrid');
    const label = document.getElementById('calMonthLabel');
    grid.innerHTML = '';
    label.textContent = `${currentMonth}年${currentMonthIdx + 1}月`;

    const firstDay = new Date(currentMonth, currentMonthIdx, 1);
    let startWeekday = firstDay.getDay();
    if (startWeekday === 0) startWeekday = 7;
    startWeekday -= 1;

    const daysInMonth = new Date(currentMonth, currentMonthIdx + 1, 0).getDate();
    const prevMonthDays = new Date(currentMonth, currentMonthIdx, 0).getDate();

    // 上月填充
    for (let i = startWeekday - 1; i >= 0; i--) {
      const el = document.createElement('div');
      el.className = 'cal-day other-month disabled';
      el.textContent = prevMonthDays - i;
      grid.appendChild(el);
    }

    // 当月日期
    for (let day = 1; day <= daysInMonth; day++) {
      const el = document.createElement('div');
      el.className = 'cal-day';
      el.textContent = day;

      const d = new Date(currentMonth, currentMonthIdx, day);
      const dateStr = formatDate(d);

      if (!isInRange(d)) {
        el.classList.add('disabled');
      } else {
        if (dateStr === formatDate(today)) {
          el.classList.add('today');
        }
        if (dateStr === selectedDate) {
          el.classList.add('selected');
        }
        if (availableDates.includes(dateStr)) {
          el.classList.add('has-data');
        }
        el.addEventListener('click', function () {
          selectedDate = dateStr;
          renderCalendar();
          loadDayData(dateStr);
        });
      }

      grid.appendChild(el);
    }

    // 下月填充
    const totalCells = startWeekday + daysInMonth;
    const remaining = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
    for (let i = 1; i <= remaining; i++) {
      const el = document.createElement('div');
      el.className = 'cal-day other-month disabled';
      el.textContent = i;
      grid.appendChild(el);
    }

    updateNavButtons();
  }

  function updateNavButtons() {
    const prevBtn = document.getElementById('calPrev');
    const nextBtn = document.getElementById('calNext');

    const prevMonth = new Date(currentMonth, currentMonthIdx - 1, 1);
    const prevMonthEnd = new Date(currentMonth, currentMonthIdx, 0);
    prevBtn.disabled = prevMonthEnd < minDate;

    const nextMonthStart = new Date(currentMonth, currentMonthIdx + 1, 1);
    nextBtn.disabled = nextMonthStart > today;
  }

  document.getElementById('calPrev').addEventListener('click', function () {
    currentMonthIdx--;
    if (currentMonthIdx < 0) {
      currentMonthIdx = 11;
      currentMonth--;
    }
    renderCalendar();
  });

  document.getElementById('calNext').addEventListener('click', function () {
    currentMonthIdx++;
    if (currentMonthIdx > 11) {
      currentMonthIdx = 0;
      currentMonth++;
    }
    renderCalendar();
  });

  // ========== 数据加载 ==========

  async function loadDayData(dateStr) {
    updateHeader(dateStr);

    const contentArea = document.getElementById('contentArea');
    const noDataMsg = document.getElementById('noDataMsg');

    document.querySelectorAll('.news-section').forEach(function (s) {
      s.style.display = 'none';
    });
    noDataMsg.style.display = 'none';

    try {
      const resp = await fetch(`data/${dateStr}.json`);
      if (!resp.ok) throw new Error('no data');
      const data = await resp.json();
      renderSections(data);
      syncNavVisibility();
    } catch (e) {
      noDataMsg.style.display = 'block';
    }
  }

  function updateHeader(dateStr) {
    document.getElementById('headerDate').textContent = formatChineseDate(dateStr);

    const d = parseDate(dateStr);
    const prevDay = new Date(d);
    prevDay.setDate(prevDay.getDate() - 1);
    const prevStr = formatDate(prevDay);
    document.getElementById('headerTimeRange').textContent =
      `覆盖时段：${prevStr} 09:00 ~ ${dateStr} 09:00`;
  }

  // ========== 新闻渲染 ==========

  function renderSections(data) {
    const sectionMap = {};
    data.sections.forEach(function (sec) {
      sectionMap[sec.id] = sec;
    });

    document.querySelectorAll('.news-section').forEach(function (el) {
      const sectionId = el.dataset.section;
      const sec = sectionMap[sectionId];
      const body = document.getElementById('body-' + sectionId);
      const count = document.getElementById('count-' + sectionId);

      if (!sec || sec.items.length === 0) {
        el.style.display = 'none';
        return;
      }

      el.style.display = 'block';
      body.innerHTML = '';

      // 热点头条单独渲染
      if (sectionId === 'hot_topics') {
        sec.items.forEach(function (topic) {
          body.appendChild(renderHotTopic(topic, data.date));
        });
        count.textContent = sec.items.length + ' 条';
        return;
      }

      // 按 eventId 分组
      const eventGroups = {};
      const standalone = [];

      sec.items.forEach(function (item) {
        if (item.eventId) {
          if (!eventGroups[item.eventId]) eventGroups[item.eventId] = [];
          eventGroups[item.eventId].push(item);
        } else {
          standalone.push(item);
        }
      });

      // 处理 eventId 组
      Object.keys(eventGroups).forEach(function (eventId) {
        const items = eventGroups[eventId];
        if (items.length > 1) {
          standalone.unshift({ _eventGroup: items });
        } else {
          standalone.push(items[0]);
        }
      });

      // 按 source 合并
      const sourceGroups = {};
      const sourceOrder = [];
      standalone.forEach(function (item) {
        if (item._eventGroup) {
          sourceOrder.push({ _eventGroup: item._eventGroup });
          return;
        }
        const src = item.source || '';
        if (!sourceGroups[src]) {
          sourceGroups[src] = [];
          sourceOrder.push(src);
        }
        sourceGroups[src].push(item);
      });

      let totalCount = 0;
      sourceOrder.forEach(function (entry) {
        if (entry && entry._eventGroup) {
          body.appendChild(renderEventGroup(entry._eventGroup, data.date));
          totalCount++;
          return;
        }
        const items = sourceGroups[entry];
        if (!items) return;
        if (items.length === 1) {
          body.appendChild(renderNewsItem(items[0], data.date));
        } else {
          body.appendChild(renderSourceGroup(entry, items, data.date));
        }
        totalCount++;
      });

      count.textContent = totalCount + ' 条';
    });
  }

  function renderHotTopic(topic, currentDate) {
    const el = document.createElement('div');
    el.className = 'hot-topic-item';

    const headline = document.createElement('div');
    headline.className = 'hot-topic-headline';
    headline.textContent = topic.headline;
    el.appendChild(headline);

    (topic.coverage || []).forEach(function (cov) {
      const row = document.createElement('div');
      row.className = 'hot-topic-source';
      row.innerHTML = `
        <span class="news-source">${escapeHtml(cov.source)}</span>
        <span class="hot-topic-summary">${escapeHtml(cov.summary)}</span>
        <a class="news-link" href="${escapeHtml(cov.url)}" target="_blank" rel="noopener">↗</a>
      `;
      el.appendChild(row);
    });

    return el;
  }

  function renderSourceGroup(source, items, currentDate) {
    const group = document.createElement('div');
    group.className = 'source-group';

    const header = document.createElement('div');
    header.className = 'source-group-header';
    header.innerHTML = `
      <span class="news-source">${escapeHtml(source)}</span>
      <span class="event-tag">${items.length} 篇</span>
    `;
    group.appendChild(header);

    const list = document.createElement('ol');
    list.className = 'source-group-list';
    items.forEach(function (item) {
      const li = document.createElement('li');
      li.className = 'source-group-item';
      li.innerHTML = `
        <a class="source-item-title" href="${escapeHtml(item.url)}" target="_blank" rel="noopener">${escapeHtml(item.title)}</a>
        <span class="source-item-summary">${escapeHtml(item.summary)}</span>
      `;
      list.appendChild(li);
    });
    group.appendChild(list);

    return group;
  }

  function renderEventGroup(items, currentDate) {
    const group = document.createElement('div');
    group.className = 'event-group';

    const header = document.createElement('div');
    header.className = 'event-group-header';
    header.innerHTML = `
      <span>${items[0].title}</span>
      <span class="event-tag">${items.length} 源报道</span>
    `;
    group.appendChild(header);

    items.forEach(function (item) {
      group.appendChild(renderNewsItem(item, currentDate, true));
    });

    return group;
  }

  function renderNewsItem(item, currentDate, inGroup) {
    const el = document.createElement('div');
    el.className = 'news-item';

    let titleHtml = inGroup
      ? ''
      : `<div class="news-title">${escapeHtml(item.title)}</div>`;

    let relatedHtml = '';
    if (item.relatedDate) {
      const relatedChinese = formatChineseDate(item.relatedDate).replace(/ 星期.*/, '');
      relatedHtml = `<span class="news-related">关联前报：<a href="#" data-date="${item.relatedDate}">${relatedChinese}</a></span>`;
    }

    el.innerHTML = `
      <div class="news-item-header">
        <span class="news-source">${escapeHtml(item.source)}</span>
        <span class="news-time">${item.time || ''}</span>
      </div>
      ${titleHtml}
      <div class="news-summary">${escapeHtml(item.summary)}</div>
      <div class="news-footer">
        <a class="news-link" href="${escapeHtml(item.url)}" target="_blank" rel="noopener">查看原文 ↗</a>
        ${relatedHtml}
      </div>
    `;

    // 关联日期跳转
    const relatedLink = el.querySelector('.news-related a');
    if (relatedLink) {
      relatedLink.addEventListener('click', function (e) {
        e.preventDefault();
        const targetDate = this.dataset.date;
        selectedDate = targetDate;
        const d = parseDate(targetDate);
        currentMonth = d.getFullYear();
        currentMonthIdx = d.getMonth();
        renderCalendar();
        loadDayData(targetDate);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    return el;
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ========== 折叠/展开 ==========

  document.querySelectorAll('.section-header').forEach(function (header) {
    header.addEventListener('click', function () {
      const sectionId = this.dataset.toggle;
      const body = document.getElementById('body-' + sectionId);
      const isCollapsed = body.classList.contains('collapsed');

      if (isCollapsed) {
        body.classList.remove('collapsed');
        this.classList.remove('collapsed');
        this.classList.add('active');
      } else {
        body.classList.add('collapsed');
        this.classList.add('collapsed');
        this.classList.remove('active');
      }
    });
  });

  // ========== 板块导航 ==========

  function initSectionNav() {
    const navItems = document.querySelectorAll('.nav-item');

    // 点击跳转（修正 sticky header 偏移）
    navItems.forEach(function (item) {
      item.addEventListener('click', function (e) {
        e.preventDefault();
        const target = this.dataset.target;
        const section = document.querySelector('[data-section="' + target + '"]');
        if (!section || section.style.display === 'none') return;
        const headerH = document.querySelector('.site-header')
          ? document.querySelector('.site-header').offsetHeight : 0;
        const top = section.getBoundingClientRect().top + window.pageYOffset - headerH - 12;
        window.scrollTo({ top: top, behavior: 'smooth' });
      });
    });

    // 滚动高亮
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          const id = entry.target.dataset.section;
          navItems.forEach(function (item) {
            item.classList.toggle('active', item.dataset.target === id);
          });
        }
      });
    }, { rootMargin: '-10% 0px -75% 0px' });

    document.querySelectorAll('.news-section').forEach(function (sec) {
      observer.observe(sec);
    });
  }

  // 数据加载后同步导航项和分组标签的显示/隐藏
  function syncNavVisibility() {
    document.querySelectorAll('.nav-item').forEach(function (item) {
      const target = item.dataset.target;
      const section = document.querySelector('[data-section="' + target + '"]');
      if (section) {
        item.classList.toggle('hidden', section.style.display === 'none');
      }
    });

    // 若某分组下所有 nav-item 都隐藏，则隐藏分组标签
    document.querySelectorAll('.nav-group-label').forEach(function (label) {
      let next = label.nextElementSibling;
      let allHidden = true;
      while (next && !next.classList.contains('nav-group-label')) {
        if (next.classList.contains('nav-item') && !next.classList.contains('hidden')) {
          allHidden = false;
          break;
        }
        next = next.nextElementSibling;
      }
      label.style.display = allHidden ? 'none' : '';
    });
  }

  // ========== 初始化 ==========

  async function init() {
    availableDates = await scanAvailableDates();
    renderCalendar();
    initSectionNav();
    loadDayData(selectedDate);
  }

  init();
})();
