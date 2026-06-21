// Minimal datepicker (no "today/clear" browser buttons)
// Attaches to inputs with attribute data-datepicker="1"
(function () {
  function pad(n) {
    return String(n).padStart(2, '0');
  }

  function formatDate(d) {
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }

  function parseDate(s) {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '');
    if (!m) return null;
    const y = Number(m[1]);
    const mo = Number(m[2]) - 1;
    const da = Number(m[3]);
    const d = new Date(y, mo, da);
    if (d.getFullYear() !== y || d.getMonth() !== mo || d.getDate() !== da) return null;
    return d;
  }

  function buildPicker(input) {
    const popup = document.createElement('div');
    popup.className = 'dp-popup';
    popup.tabIndex = -1;

    const header = document.createElement('div');
    header.className = 'dp-header';

    const prev = document.createElement('button');
    prev.type = 'button';
    prev.className = 'dp-nav';
    prev.textContent = '‹';

    const title = document.createElement('div');
    title.className = 'dp-title';

    const next = document.createElement('button');
    next.type = 'button';
    next.className = 'dp-nav';
    next.textContent = '›';

    header.appendChild(prev);
    header.appendChild(title);
    header.appendChild(next);

    const grid = document.createElement('div');
    grid.className = 'dp-grid';

    popup.appendChild(header);
    popup.appendChild(grid);

    document.body.appendChild(popup);

    const state = {
      current: parseDate(input.value) || new Date(),
      open: false,
    };

    function render() {
      const d = new Date(state.current.getFullYear(), state.current.getMonth(), 1);
      const month = d.getMonth();
      const year = d.getFullYear();

      const monthNames = [
        'Январь','Февраль','Март','Апрель','Май','Июнь',
        'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'
      ];
      title.textContent = `${monthNames[month]} ${year}`;

      grid.innerHTML = '';
      const week = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
      week.forEach(w => {
        const el = document.createElement('div');
        el.className = 'dp-dow';
        el.textContent = w;
        grid.appendChild(el);
      });

      // JS: 0=Sun..6=Sat, we want Mon=0..Sun=6
      const firstDay = (d.getDay() + 6) % 7;
      for (let i = 0; i < firstDay; i++) {
        const empty = document.createElement('div');
        empty.className = 'dp-cell dp-empty';
        grid.appendChild(empty);
      }

      const selected = parseDate(input.value);
      const now = new Date();
      const todayStr = formatDate(now);

      while (d.getMonth() === month) {
        const cell = document.createElement('button');
        cell.type = 'button';
        cell.className = 'dp-cell';
        const ds = formatDate(d);
        cell.textContent = String(d.getDate());

        if (selected && ds === formatDate(selected)) cell.classList.add('dp-selected');
        if (ds === todayStr) cell.classList.add('dp-today');

        cell.addEventListener('click', () => {
          input.value = ds;
          input.dispatchEvent(new Event('change', { bubbles: true }));
          close();
        });

        grid.appendChild(cell);
        d.setDate(d.getDate() + 1);
      }
    }

    function position() {
      const r = input.getBoundingClientRect();
      popup.style.left = `${Math.round(r.left + window.scrollX)}px`;
      popup.style.top = `${Math.round(r.bottom + window.scrollY + 6)}px`;
      popup.style.minWidth = `${Math.max(260, Math.round(r.width))}px`;
    }

    function open() {
      if (state.open) return;
      state.open = true;
      popup.style.display = 'block';
      state.current = parseDate(input.value) || new Date();
      render();
      position();
    }

    function close() {
      state.open = false;
      popup.style.display = 'none';
    }

    prev.addEventListener('click', () => {
      state.current = new Date(state.current.getFullYear(), state.current.getMonth() - 1, 1);
      render();
    });
    next.addEventListener('click', () => {
      state.current = new Date(state.current.getFullYear(), state.current.getMonth() + 1, 1);
      render();
    });

    input.addEventListener('focus', open);
    input.addEventListener('click', open);
    window.addEventListener('resize', () => state.open && position());
    window.addEventListener('scroll', () => state.open && position(), true);

    document.addEventListener('mousedown', (e) => {
      if (!state.open) return;
      if (e.target === input) return;
      if (popup.contains(e.target)) return;
      close();
    });
    document.addEventListener('keydown', (e) => {
      if (!state.open) return;
      if (e.key === 'Escape') close();
    });

    return { open, close };
  }

  function init() {
    const inputs = document.querySelectorAll('input[data-datepicker="1"]');
    inputs.forEach((input) => {
      if (input.__dp_inited) return;
      input.__dp_inited = true;
      if (!input.value) input.value = formatDate(new Date());
      buildPicker(input);
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();


