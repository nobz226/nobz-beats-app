async function postFormAsJson(form, resultEl, callback) {
  console.debug('postFormAsJson submitting to', form.action);
  resultEl.textContent = 'Processing...';
  try {
    const fd = new FormData(form);
    const res = await fetch(form.action, { method: 'POST', body: fd });
    const json = await res.json();
    console.debug('postFormAsJson response', json);
    if (!res.ok) throw new Error(json.error || JSON.stringify(json));

    let handled = false;
    if (typeof callback === 'function') {
      try {
        handled = callback(json) === true;
      } catch (callbackErr) {
        console.error('Callback error:', callbackErr);
      }
    }

    if (!handled) {
      resultEl.innerHTML = `<pre>${JSON.stringify(json, null, 2)}</pre>`;
    }
  } catch (err) {
    resultEl.innerHTML = `<div style="color:#b00">Error: ${err.message}</div>`;
  }
}

async function postFormAndDownloadWithFormat(form, resultEl, format) {
  resultEl.textContent = 'Processing...';
  try {
    const fd = new FormData(form);
    if (format) fd.append('format', format);
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


console.debug('tools.js loaded');

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
  analyzeForm.action = '/api/analyze';
  analyzeForm.addEventListener('submit', (e) => { e.preventDefault(); setButtonState(analyzeForm, true); postFormAsJson(analyzeForm, analyzeResult).finally(()=>setButtonState(analyzeForm, false)); });

  const convertForm = document.getElementById('convertForm');
  const convertResult = document.getElementById('convertResult');
  convertForm.action = '/api/convert';
  convertForm.addEventListener('submit', (e) => { e.preventDefault(); setButtonState(convertForm, true); postFormAndDownload(convertForm, convertResult).finally(()=>setButtonState(convertForm, false)); });

  const separateForm = document.getElementById('separateForm');
  const separateResult = document.getElementById('separateResult');
  separateForm.action = '/api/separate';
  separateForm.addEventListener('submit', (e) => { e.preventDefault(); setButtonState(separateForm, true); postFormAndDownload(separateForm, separateResult).finally(()=>setButtonState(separateForm, false)); });

  const transcribeForm = document.getElementById('transcribeForm');
  const transcribeResult = document.getElementById('transcribeResult');
  transcribeForm.action = '/api/transcribe';
  transcribeForm.addEventListener('submit', (e) => {
    e.preventDefault();
    setButtonState(transcribeForm, true);
    
    // Check if user wants to download MusicXML
    const downloadXmlCheckbox = document.getElementById('downloadXml');
    if (downloadXmlCheckbox && downloadXmlCheckbox.checked) {
      // Download MusicXML file
      postFormAndDownloadWithFormat(transcribeForm, transcribeResult, 'musicxml').finally(()=>setButtonState(transcribeForm, false));
      return;
    }
    
    // Normal JSON response with visual display
    postFormAsJson(transcribeForm, transcribeResult, (json) => {
      console.debug('transcribe callback', json);
      if (json.musicxml) {
        const OSMD = window.opensheetmusicdisplay?.OpenSheetMusicDisplay || window.OpenSheetMusicDisplay || window.opensheetmusicdisplay || window.osmd;
        if (!OSMD) {
          transcribeResult.innerHTML = '<div style="color:#b00">Notation library failed to load. Please refresh the page.</div>';
          return true;
        }
        transcribeResult.innerHTML = '<div id="notationContainer" style="min-height:360px;"></div>';
        const div = document.getElementById('notationContainer');
        try {
          const osmd = new OSMD(div, {autoResize: true});
          osmd.load(json.musicxml).then(() => osmd.render()).catch((err) => {
            transcribeResult.innerHTML = `<div style="color:#b00">Notation render failed: ${err.message}</div>`;
          });
        } catch (renderErr) {
          console.error('OSMD instantiation error', renderErr);
          transcribeResult.innerHTML = `<div style="color:#b00">Notation setup failed: ${renderErr.message}</div>`;
        }
        return true;
      }
      if (json.musicxml_error) {
        transcribeResult.innerHTML = `<div style="color:#b00">MusicXML was not generated: ${json.musicxml_error}</div><pre>${JSON.stringify(json, null, 2)}</pre>`;
        return true;
      }
      console.debug('transcribe no musicxml, showing raw JSON');
      transcribeResult.innerHTML = `<pre>${JSON.stringify(json, null, 2)}</pre>`;
      return true;
    }).finally(()=>setButtonState(transcribeForm, false));
  });
});