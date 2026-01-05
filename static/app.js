document.addEventListener('DOMContentLoaded', () => {
  const startBtn = document.getElementById('startBtn');
  const urlInput = document.getElementById('urlInput');
  const depthInput = document.getElementById('depthInput');
  const statusEl = document.getElementById('status');
  const resultCard = document.getElementById('resultCard');
  const resultPre = document.getElementById('resultPre');
  const downloadLink = document.getElementById('downloadLink');
  const tips = document.getElementById('tips');
  const progressBar = document.createElement('div');

  progressBar.className = 'progress my-2 d-none';
  progressBar.innerHTML = '<div id="progressInner" class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width:0%"></div>';
  statusEl.after(progressBar);

  function setProgress(p) {
    const inner = document.getElementById('progressInner');
    if (inner) inner.style.width = Math.min(100, Math.max(0, p)) + '%';
  }

  async function pollStatus(job_id) {
    try {
      const resp = await fetch(`/status/${job_id}`);
      if (!resp.ok) throw new Error('Status request failed');
      const data = await resp.json();
      statusEl.textContent = data.message || data.status;

      if (data.status === 'running') {
        progressBar.classList.remove('d-none');
        // rough heuristic for visual progress
        setProgress(30);
        setTimeout(() => pollStatus(job_id), 1500);
      } else if (data.status === 'queued') {
        progressBar.classList.remove('d-none');
        setProgress(10);
        setTimeout(() => pollStatus(job_id), 1000);
      } else if (data.status === 'done') {
        progressBar.classList.add('d-none');
        setProgress(100);
        resultCard.classList.remove('d-none');
        resultPre.textContent = JSON.stringify(data, null, 2);
        if (data.file) {
          downloadLink.href = `/result/${job_id}`;
          downloadLink.classList.remove('d-none');
        }
        // show categorized lists if present
        renderCategories(data);
        startBtn.disabled = false;
      } else if (data.status === 'error') {
        progressBar.classList.add('d-none');
        statusEl.textContent = 'Error: ' + (data.message || 'unknown');
        startBtn.disabled = false;
      } else {
        // unknown state
        setTimeout(() => pollStatus(job_id), 2000);
      }
    } catch (err) {
      statusEl.textContent = 'Error checking status';
      startBtn.disabled = false;
    }
  }

  function renderCategories(data) {
    const container = document.getElementById('categories');
    container.innerHTML = '';
    if (data.departamentos && data.departamentos.length) {
      container.appendChild(renderList('Departamentos', data.departamentos));
    }
    if (data.provincias && data.provincias.length) {
      container.appendChild(renderList('Provincias', data.provincias));
    }
    if (data.distritos && data.distritos.length) {
      container.appendChild(renderList('Distritos', data.distritos));
    }
    if (data.otras && data.otras.length) {
      container.appendChild(renderList('Otras administrativas', data.otras));
    }
    if (data.urls && data.urls.length) {
      container.appendChild(renderList('Todas las URLs encontradas', data.urls));
    }
  }

  function renderList(title, items) {
    const card = document.createElement('div');
    card.className = 'card my-2';
    const body = document.createElement('div');
    body.className = 'card-body p-2';
    const h = document.createElement('h6');
    h.textContent = title;
    h.className = 'card-title';
    body.appendChild(h);
    const ul = document.createElement('ul');
    ul.className = 'small';
    items.slice(0, 200).forEach(it => {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = it;
      a.textContent = it;
      a.target = '_blank';
      li.appendChild(a);
      ul.appendChild(li);
    });
    body.appendChild(ul);
    card.appendChild(body);
    return card;
  }

  startBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    const depth = depthInput.value;
    if (!url) { alert('Por favor ingresa una URL válida'); return; }

    statusEl.textContent = 'Encolando...';
    startBtn.disabled = true;
    resultCard.classList.add('d-none');
    resultPre.textContent = '';
    document.getElementById('categories').innerHTML = '';

    try {
      const resp = await fetch('/extract', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ url, depth })
      });

      if (resp.status === 202) {
        const data = await resp.json();
        statusEl.textContent = 'Trabajo creado. Iniciando...';
        pollStatus(data.job_id);
      } else {
        const data = await resp.json();
        statusEl.textContent = 'Error: ' + (data.error || resp.statusText);
        startBtn.disabled = false;
      }
    } catch (err) {
      statusEl.textContent = 'Error: ' + err.message;
      startBtn.disabled = false;
    }
  });
});
