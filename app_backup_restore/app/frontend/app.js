document.addEventListener('DOMContentLoaded', () => {
  const uploadZone = document.getElementById('uploadZone');
  const fileInput = document.getElementById('fileInput');
  const fileInfoSection = document.getElementById('fileInfoSection');
  const infoFileName = document.getElementById('infoFileName');
  const infoFileDetails = document.getElementById('infoFileDetails');
  const btnStartGeneration = document.getElementById('btnStartGeneration');

  const progressSection = document.getElementById('progressSection');
  const progressBarFill = document.getElementById('progressBarFill');
  const progressStatusText = document.getElementById('progressStatusText');
  const progressPctText = document.getElementById('progressPctText');
  const terminalLog = document.getElementById('terminalLog');

  const metricReqs = document.getElementById('metricReqs');
  const metricTCs = document.getElementById('metricTCs');
  const metricTables = document.getElementById('metricTables');

  const tableBody = document.getElementById('tableBody');
  const tableSearch = document.getElementById('tableSearch');
  const btnExportExcel = document.getElementById('btnExportExcel');
  const btnExportJSON = document.getElementById('btnExportJSON');
  const historyList = document.getElementById('historyList');

  let allGeneratedTCs = [];
  let currentExcelPath = null;
  let currentJsonPath = null;
  let selectedFile = null;

  // File Upload Event Listeners
  uploadZone.addEventListener('click', () => fileInput.click());

  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
  });

  uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));

  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  function addLog(msg) {
    const line = document.createElement('div');
    line.className = 'log-line';
    line.textContent = `> ${msg}`;
    terminalLog.appendChild(line);
    terminalLog.scrollTop = terminalLog.scrollHeight;
  }

  async function handleFileSelected(file) {
    if (!file.name.toLowerCase().endsWith('.docx')) {
      alert('Please select a valid .docx Word requirement document.');
      return;
    }

    selectedFile = file;
    const formData = new FormData();
    formData.append('file', file);

    addLog(`Uploading and analyzing file: ${file.name}`);

    try {
      const resp = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      if (!resp.ok) {
        throw new Error('Failed to parse uploaded document.');
      }

      const data = await resp.json();
      infoFileName.textContent = data.file_name;
      infoFileDetails.textContent = `Found ${data.requirements_found} Requirements & ${data.total_tables} Tables`;
      fileInfoSection.style.display = 'block';

      metricReqs.textContent = data.requirements_found;
      metricTables.textContent = data.total_tables;
      addLog(`Analysis complete: ${data.requirements_found} requirements & ${data.total_tables} tables identified.`);

    } catch (err) {
      addLog(`ERROR: ${err.message}`);
      alert(`Upload error: ${err.message}`);
    }
  }

  // Click handler for "Start Test Case Generation" button
  btnStartGeneration.addEventListener('click', () => {
    if (!selectedFile) {
      alert('Please select a .docx file first.');
      return;
    }

    btnStartGeneration.disabled = true;
    btnStartGeneration.style.opacity = '0.5';
    progressSection.style.display = 'block';
    startGenerationStream();
  });

  function startGenerationStream() {
    allGeneratedTCs = [];
    tableBody.innerHTML = '';
    progressStatusText.textContent = 'Connecting to Ollama model via SSH tunnel...';
    addLog('Connecting to Ollama model at http://localhost:11434 (gpt-oss:latest)...');

    const eventSource = new EventSource('/api/generate-stream');

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.step === 'QUERYING') {
        progressBarFill.style.width = `${data.percentage}%`;
        progressPctText.textContent = `${data.percentage}%`;
        progressStatusText.textContent = `Generating Requirement ${data.requirement_id} (${data.current_index}/${data.total_requirements})...`;
        addLog(`Querying requirement: ${data.requirement_id}`);

      } else if (data.step === 'PROGRESS') {
        allGeneratedTCs.push(...data.new_test_cases);
        metricTCs.textContent = allGeneratedTCs.length;
        renderNewTestCases(data.new_test_cases);

      } else if (data.step === 'COMPLETED') {
        progressBarFill.style.width = '100%';
        progressPctText.textContent = '100%';
        progressStatusText.textContent = 'Generation & Export Complete!';
        addLog(`Successfully generated ${data.total_test_cases} test cases!`);
        addLog(`Saved Excel: ${data.excel_path}`);

        currentExcelPath = data.excel_path;
        currentJsonPath = data.json_path;

        btnExportExcel.disabled = false;
        btnExportJSON.disabled = false;
        btnStartGeneration.disabled = false;
        btnStartGeneration.style.opacity = '1';

        eventSource.close();
        loadHistory();
      }
    };

    eventSource.onerror = (err) => {
      addLog('Stream error or SSH connection lost.');
      eventSource.close();
      btnStartGeneration.disabled = false;
      btnStartGeneration.style.opacity = '1';
    };
  }

  function renderNewTestCases(testCases) {
    testCases.forEach((tc, idx) => {
      const row = document.createElement('tr');
      const badgeClass = getBadgeClass(tc.test_type);

      row.innerHTML = `
        <td>${allGeneratedTCs.length - testCases.length + idx + 1}</td>
        <td style="font-weight: 600; color: #38BDF8;">${tc.test_case_id}</td>
        <td>${tc.requirement_id}</td>
        <td><span class="badge ${badgeClass}">${tc.test_type}</span></td>
        <td>${tc.description}</td>
        <td>${tc.test_inputs}</td>
        <td>${tc.expected_result}</td>
        <td>${tc.pass_criteria}</td>
      `;
      tableBody.appendChild(row);
    });
  }

  function getBadgeClass(type) {
    switch (type.toUpperCase()) {
      case 'DC': return 'badge-dc';
      case 'BOUNDARY': return 'badge-boundary';
      case 'ROBUSTNESS': return 'badge-robustness';
      default: return 'badge-normal';
    }
  }

  // Download Event Handlers
  btnExportExcel.addEventListener('click', () => {
    if (currentExcelPath) {
      window.location.href = `/api/download?file_path=${encodeURIComponent(currentExcelPath)}`;
    }
  });

  btnExportJSON.addEventListener('click', () => {
    if (currentJsonPath) {
      window.location.href = `/api/download?file_path=${encodeURIComponent(currentJsonPath)}`;
    }
  });

  // Search Filter Handler
  tableSearch.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    const rows = tableBody.querySelectorAll('tr');
    rows.forEach(r => {
      const text = r.textContent.toLowerCase();
      r.style.display = text.includes(q) ? '' : 'none';
    });
  });

  // Load Past History
  async function loadHistory() {
    try {
      const resp = await fetch('/api/history');
      if (resp.ok) {
        const history = await resp.json();
        if (history.length > 0) {
          historyList.innerHTML = history.map(item => `
            <div class="history-item">
              <div class="history-info">
                <h4>${item.file_name} (${item.test_cases_count} TCs)</h4>
                <p>${item.timestamp} • ${item.requirements_count} Reqs</p>
              </div>
              <a href="/api/download?file_path=${encodeURIComponent(item.excel_path)}" class="btn btn-secondary" style="padding: 6px 12px; font-size: 11px;">
                Download
              </a>
            </div>
          `).join('');
        }
      }
    } catch (e) {
      console.error('History load error:', e);
    }
  }

  loadHistory();
});
