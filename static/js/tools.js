async function postFormAsJson(form, resultEl) {
  resultEl.textContent = 'Processing...';
  try {
    const fd = new FormData(form);
    const res = await fetch(form.action, { method: 'POST', body: fd });
    const json = await res.json();
    if (!res.ok) throw new Error(json.error || JSON.stringify(json));
    resultEl.innerHTML = `<pre>${JSON.stringify(json, null, 2)}</pre>`;
  } catch (err) {
    resultEl.innerHTML = `<div style="color:#b00">Error: ${err.message}</div>`;
  }
}

async function postFormAndDownload(form, resultEl) {
  resultEl.textContent = 'Processing...';
  try {
    const fd = new FormData(form);
    const res = await fetch(form.action, { method: 'POST', body: fd });
    if (!res.ok) {
      // try parse JSON error
      let txt = await res.text();
      try { const j = JSON.parse(txt); txt = j.error || JSON.stringify(j); } catch(e){}
      throw new Error(txt || `HTTP ${res.status}`);
    }

    const cd = res.headers.get('content-disposition') || '';
    let filename = 'download.bin';
    const m = cd.match(/filename\*=UTF-8''([^;]+)/);
    if (m) filename = decodeURIComponent(m[1]);
    else {
      const m2 = cd.match(/filename="?([^";]+)"?/);
      if (m2) filename = m2[1];
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; document.body.appendChild(a);
    a.click(); a.remove(); URL.revokeObjectURL(url);
    resultEl.innerHTML = `<div style="color:green">Downloaded: ${filename}</div>`;
  } catch (err) {
    resultEl.innerHTML = `<div style="color:#b00">Error: ${err.message}</div>`;
  }
}

// Health check and utility
async function fetchHealth() {
  try {
    const res = await fetch('/api/health');
    const json = await res.json();
    return json;
  } catch (e) {
    return { error: String(e) };
  }
}

function setButtonState(form, disabled) {
  const btn = form.querySelector('button[type=submit]');
  if (btn) btn.disabled = !!disabled;
}

// Setup handlers
document.addEventListener('DOMContentLoaded', async () => {
  const statusBody = document.getElementById('systemStatusBody');
  statusBody.textContent = 'Checking system...';

  const health = await fetchHealth();
  if (health.error) {
    statusBody.innerHTML = `<div style="color:#b00">Health check failed: ${health.error}</div>`;
  } else {
    const parts = [];
    parts.push(`<div>Demucs: ${health.demucs_installed ? '✅' : '❌'} ${health.demucs_path || ''}</div>`);
    parts.push(`<div>FFmpeg: ${health.ffmpeg_installed ? '✅' : '❌'} ${health.ffmpeg_path || ''}</div>`);
    parts.push(`<div>Torch cache exists: ${health.torch_cache_exists ? '✅' : '❌'}; files: ${health.torch_cache_nonempty ? health.torch_cache_files.join(', ') : 'none'}</div>`);
    statusBody.innerHTML = parts.join('');

    // If demucs not installed, disable separator
    if (!health.demucs_installed) {
      const sepForm = document.getElementById('separateForm');
      setButtonState(sepForm, true);
    }
    if (!health.ffmpeg_installed) {
      const convForm = document.getElementById('convertForm');
      setButtonState(convForm, true);
    }
  }

  const analyzeForm = document.getElementById('analyzeForm');
  const analyzeResult = document.getElementById('analyzeResult');
  analyzeForm.action = '/audio/analyze';
  analyzeForm.addEventListener('submit', (e) => { e.preventDefault(); setButtonState(analyzeForm, true); postFormAsJson(analyzeForm, analyzeResult).finally(()=>setButtonState(analyzeForm, false)); });

  const convertForm = document.getElementById('convertForm');
  const convertResult = document.getElementById('convertResult');
  convertForm.action = '/audio/convert';
  convertForm.addEventListener('submit', (e) => { e.preventDefault(); setButtonState(convertForm, true); postFormAndDownload(convertForm, convertResult).finally(()=>setButtonState(convertForm, false)); });

  const separateForm = document.getElementById('separateForm');
  const separateResult = document.getElementById('separateResult');
  separateForm.action = '/audio/separate';
  separateForm.addEventListener('submit', (e) => { e.preventDefault(); setButtonState(separateForm, true); postFormAndDownload(separateForm, separateResult).finally(()=>setButtonState(separateForm, false)); });
});