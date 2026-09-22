document.addEventListener('DOMContentLoaded', () => {
  // Login & Sign Up DOM Elements
  const loginModal = document.getElementById('loginModal');
  const tabSignIn = document.getElementById('tabSignIn');
  const tabSignUp = document.getElementById('tabSignUp');
  
  const loginForm = document.getElementById('loginForm');
  const signupForm = document.getElementById('signupForm');
  
  const loginUsername = document.getElementById('loginUsername');
  const loginPassword = document.getElementById('loginPassword');
  const rememberMe = document.getElementById('rememberMe');
  const loginErrorMsg = document.getElementById('loginErrorMsg');
  const btnTogglePassword = document.getElementById('btnTogglePassword');
  const btnLoginSubmit = document.getElementById('btnLoginSubmit');

  const signupFullName = document.getElementById('signupFullName');
  const signupEmail = document.getElementById('signupEmail');
  const signupPassword = document.getElementById('signupPassword');
  const signupMsg = document.getElementById('signupMsg');
  
  const displayUserName = document.getElementById('displayUserName');
  const btnLogout = document.getElementById('btnLogout');

  // Application DOM Elements
  const tunnelStatusDot = document.querySelector('.status-dot');
  const tunnelStatusText = document.getElementById('tunnel-status');

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
  const metricAccuracy = document.getElementById('metricAccuracy');
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

  // ==========================================
  // Auth Tab Navigation (Sign In vs Sign Up)
  // ==========================================
  tabSignIn.addEventListener('click', () => {
    tabSignIn.classList.add('active');
    tabSignUp.classList.remove('active');
    loginForm.style.display = 'flex';
    signupForm.style.display = 'none';
  });

  tabSignUp.addEventListener('click', () => {
    tabSignUp.classList.add('active');
    tabSignIn.classList.remove('active');
    signupForm.style.display = 'flex';
    loginForm.style.display = 'none';
  });

  // Toggle Password Visibility
  btnTogglePassword.addEventListener('click', () => {
    const type = loginPassword.getAttribute('type') === 'password' ? 'text' : 'password';
    loginPassword.setAttribute('type', type);
    btnTogglePassword.textContent = type === 'password' ? 'Show' : 'Hide';
  });

  // REAL Sign In Form Submission (Backend Verified)
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const userVal = loginUsername.value.trim();
    const passVal = loginPassword.value.trim();

    if (!userVal || !passVal) {
      showLoginError('Please enter username and password.');
      return;
    }

    btnLoginSubmit.disabled = true;
    btnLoginSubmit.textContent = 'Verifying Credentials...';

    try {
      const resp = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: userVal, password: passVal })
      });

      const data = await resp.json();

      if (!resp.ok) {
        showLoginError(data.detail || 'Authentication failed. Fake users cannot log in.');
        btnLoginSubmit.disabled = false;
        btnLoginSubmit.textContent = 'Sign In to Workspace →';
        return;
      }

      const userData = {
        username: data.user.full_name || data.user.username,
        email: data.user.email,
        loginTime: new Date().toISOString()
      };

      if (rememberMe.checked) {
        localStorage.setItem('do178c_user', JSON.stringify(userData));
      } else {
        sessionStorage.setItem('do178c_user', JSON.stringify(userData));
      }

      displayUserName.textContent = userData.username;
      loginModal.classList.add('hidden');
      loginErrorMsg.style.display = 'none';

    } catch (err) {
      showLoginError(`Authentication Server Error: ${err.message}`);
    } finally {
      btnLoginSubmit.disabled = false;
      btnLoginSubmit.textContent = 'Sign In to Workspace →';
    }
  });

  // REAL Sign Up Form Submission (Backend Persistence)
  signupForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fullName = signupFullName.value.trim();
    const email = signupEmail.value.trim();
    const pwd = signupPassword.value.trim();

    if (pwd.length < 6) {
      showSignupMsg('Password must be at least 6 characters.', true);
      return;
    }

    try {
      const resp = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: fullName, email: email, password: pwd })
      });

      const data = await resp.json();

      if (!resp.ok) {
        showSignupMsg(data.detail || 'Registration failed.', true);
        return;
      }

      const userData = {
        username: data.user.full_name || data.user.username,
        email: data.user.email,
        loginTime: new Date().toISOString()
      };

      localStorage.setItem('do178c_user', JSON.stringify(userData));
      displayUserName.textContent = userData.username;

      showSignupMsg('Account successfully created! Signing you in...', false);
      setTimeout(() => {
        loginModal.classList.add('hidden');
        signupMsg.style.display = 'none';
      }, 1000);

    } catch (err) {
      showSignupMsg(`Registration Error: ${err.message}`, true);
    }
  });

  function showLoginError(msg) {
    loginErrorMsg.textContent = msg;
    loginErrorMsg.className = 'login-error-msg';
    loginErrorMsg.style.display = 'block';
  }

  function showSignupMsg(msg, isError = true) {
    signupMsg.textContent = msg;
    signupMsg.className = isError ? 'login-error-msg' : 'login-error-msg success-msg';
    signupMsg.style.display = 'block';
  }

  // Logout Handler
  btnLogout.addEventListener('click', () => {
    localStorage.removeItem('do178c_user');
    sessionStorage.removeItem('do178c_user');
    loginModal.classList.remove('hidden');
  });

  function checkAuthSession() {
    const savedUser = localStorage.getItem('do178c_user') || sessionStorage.getItem('do178c_user');
    if (savedUser) {
      const user = JSON.parse(savedUser);
      displayUserName.textContent = user.username;
      loginModal.classList.add('hidden');
    } else {
      loginModal.classList.remove('hidden');
    }
  }

  checkAuthSession();

  // ==========================================
  // SSH Tunnel Status & Model Selector Functions
  // ==========================================
  const modelSelect = document.getElementById('modelSelect');

  async function loadAvailableModels() {
    try {
      const resp = await fetch('/api/models');
      if (resp.ok) {
        const data = await resp.json();
        const activeModel = data.active_model;
        const models = data.available_models || [];

        modelSelect.innerHTML = models.map(m => `
          <option value="${m}" ${m === activeModel ? 'selected' : ''}>
            ${m} ${m.includes('gpt-oss') ? '(SSH Tunnel)' : ''}
          </option>
        `).join('');
      }
    } catch (err) {
      console.error('Failed to load models:', err);
    }
  }

  modelSelect.addEventListener('change', async (e) => {
    const selectedModel = e.target.value;
    try {
      const resp = await fetch('/api/set-model', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
      });

      if (resp.ok) {
        const data = await resp.json();
        addLog(`Switched active LLM model to: ${data.active_model}`);
      } else {
        alert('Failed to switch model.');
      }
    } catch (err) {
      alert(`Model switch error: ${err.message}`);
    }
  });

  async function checkTunnelStatus() {
    try {
      const resp = await fetch('/api/status');
      if (resp.ok) {
        const data = await resp.json();
        if (data.ssh_tunnel_online) {
          tunnelStatusDot.style.backgroundColor = '#10B981';
          tunnelStatusDot.style.boxShadow = '0 0 10px #10B981';
          tunnelStatusText.textContent = `SSH Tunnel: ${data.endpoint} (${data.model})`;
        } else {
          tunnelStatusDot.style.backgroundColor = '#EF4444';
          tunnelStatusDot.style.boxShadow = '0 0 10px #EF4444';
          tunnelStatusText.textContent = 'SSH Tunnel: CLOSED';
        }
      }
    } catch (e) {
      tunnelStatusDot.style.backgroundColor = '#EF4444';
      tunnelStatusDot.style.boxShadow = '0 0 10px #EF4444';
      tunnelStatusText.textContent = 'SSH Tunnel: CLOSED';
    }
  }

  setInterval(checkTunnelStatus, 5000);
  checkTunnelStatus();
  loadAvailableModels();

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

  // ==========================================
  // Live Log Console Modal Event Handlers
  // ==========================================
  const btnOpenLogsModal = document.getElementById('btnOpenLogsModal');
  const btnCloseLogsModal = document.getElementById('btnCloseLogsModal');
  const logsModal = document.getElementById('logsModal');
  const modalTerminalLog = document.getElementById('modalTerminalLog');
  const btnClearLogs = document.getElementById('btnClearLogs');
  const btnCopyLogs = document.getElementById('btnCopyLogs');

  btnOpenLogsModal.addEventListener('click', () => {
    logsModal.style.display = 'flex';
  });

  btnCloseLogsModal.addEventListener('click', () => {
    logsModal.style.display = 'none';
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && logsModal.style.display === 'flex') {
      logsModal.style.display = 'none';
    }
  });

  btnClearLogs.addEventListener('click', () => {
    terminalLog.innerHTML = '';
    modalTerminalLog.innerHTML = '<div class="log-line">> Log console cleared.</div>';
  });

  btnCopyLogs.addEventListener('click', () => {
    const text = modalTerminalLog.textContent;
    navigator.clipboard.writeText(text).then(() => {
      alert('Live console logs copied to clipboard!');
    }).catch(err => {
      console.error('Copy failed:', err);
    });
  });

  function addLog(msg) {
    const line1 = document.createElement('div');
    line1.className = 'log-line';
    line1.textContent = `> ${msg}`;
    terminalLog.appendChild(line1);
    terminalLog.scrollTop = terminalLog.scrollHeight;

    const line2 = document.createElement('div');
    line2.className = 'log-line';
    line2.textContent = `[${new Date().toLocaleTimeString()}] > ${msg}`;
    modalTerminalLog.appendChild(line2);
    modalTerminalLog.scrollTop = modalTerminalLog.scrollHeight;
  }

  function updateComplianceScore(testCases) {
    if (!metricAccuracy) return;
    if (!testCases || testCases.length === 0) {
      metricAccuracy.textContent = '0%';
      metricAccuracy.style.color = '#94A3B8';
      return;
    }

    let compliantCount = 0;
    testCases.forEach(tc => {
      const ti = (tc.test_inputs || '').toLowerCase();
      const er = (tc.expected_result || '').toLowerCase();
      const desc = (tc.description || '').toLowerCase();
      const tt = (tc.test_type || '').toUpperCase();

      const outputInInputs = /act_disp_range_\w+_fault|harmonizing_psr_data_fault|harmonizing_failed|contract_stop_collection_complete|expand_stop_collection_complete|void_collection_complete|command(?:ed)?\s+to/.test(ti);
      const emptyFields = !tc.test_inputs || !tc.expected_result || !tc.initial_condition || ti === 'none';
      const isNegative = tt === 'DC' || /false|outside|invalid|error|fails/.test(desc);
      const hasBoolAssertion = /= false|= true|false|true/.test(er);
      const missingNegative = isNegative && !hasBoolAssertion;

      if (!outputInInputs && !emptyFields && !missingNegative) {
        compliantCount++;
      }
    });

    const score = Math.round((compliantCount / testCases.length) * 100);
    metricAccuracy.textContent = `${score}%`;
    if (score >= 95) {
      metricAccuracy.style.color = '#10B981';
    } else if (score >= 80) {
      metricAccuracy.style.color = '#F59E0B';
    } else {
      metricAccuracy.style.color = '#EF4444';
    }
  }

  async function handleFileSelected(file) {
    if (!file.name.toLowerCase().endsWith('.docx')) {
      alert('Please select a valid .docx Word requirement document.');
      return;
    }

    selectedFile = file;
    const formData = new FormData();
    formData.append('file', file);

    terminalLog.innerHTML = '';
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

      // Instant Auto-Resume: If cached test cases exist, populate UI table immediately!
      if (data.cached_testcases && data.cached_testcases.length > 0) {
        allGeneratedTCs = data.cached_testcases;
        renderFullTable(allGeneratedTCs);
        metricTCs.textContent = allGeneratedTCs.length;
        updateComplianceScore(allGeneratedTCs);
        if (data.excel_path) currentExcelPath = data.excel_path;
        if (data.json_path) currentJsonPath = data.json_path;
        btnExportExcel.disabled = false;
        btnExportJSON.disabled = false;
        addLog(`⚡ Auto-Resume: Loaded ${data.cached_testcases_count} existing test cases instantly into workspace!`);
      } else {
        allGeneratedTCs = [];
        metricTCs.textContent = '0';
        updateComplianceScore([]);
      }

    } catch (err) {
      addLog(`ERROR: ${err.message}`);
      alert(`Upload error: ${err.message}`);
    }
  }

  // Start Generation Event Handler
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

  const chkForceReprocess = document.getElementById('chkForceReprocess');

  if (chkForceReprocess) {
    chkForceReprocess.addEventListener('change', () => {
      if (chkForceReprocess.checked) {
        allGeneratedTCs = [];
        metricTCs.textContent = '0';
        updateComplianceScore([]);
        tableBody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding:30px; color:#94A3B8;">⚡ Force Full AI Re-process enabled. Click "Start Test Case Generation" to stream fresh test cases live.</td></tr>';
        btnExportExcel.disabled = true;
        btnExportJSON.disabled = true;
      }
    });
  }

  function handleStreamPayload(data) {
    if (data.step === 'LOG') {
      addLog(data.message);
    } else if (data.step === 'QUERYING') {
      progressBarFill.style.width = `${data.percentage}%`;
      progressPctText.textContent = `${data.percentage}%`;
      progressStatusText.textContent = `🧠 Reasoning on ${data.requirement_id} (${data.current_index}/${data.total_requirements})...`;
      addLog(`Querying requirement: ${data.requirement_id}`);

    } else if (data.step === 'PROGRESS') {
      data.new_test_cases.forEach(tc => {
        if (!allGeneratedTCs.some(t => t.test_case_id === tc.test_case_id)) {
          allGeneratedTCs.push(tc);
        }
      });
      metricTCs.textContent = allGeneratedTCs.length;
      updateComplianceScore(allGeneratedTCs);
      renderFullTable(allGeneratedTCs);
      filterTableRows();

    } else if (data.step === 'COMPLETED') {
      progressBarFill.style.width = '100%';
      progressPctText.textContent = '100%';
      progressStatusText.textContent = '✅ Generation & Export Complete!';
      metricTCs.textContent = data.total_test_cases;
      updateComplianceScore(allGeneratedTCs);
      addLog(`Successfully generated ${data.total_test_cases} test cases!`);
      addLog(`Saved Excel: ${data.excel_path}`);

      currentExcelPath = data.excel_path;
      currentJsonPath = data.json_path;

      btnExportExcel.disabled = false;
      btnExportJSON.disabled = false;
      btnStartGeneration.disabled = false;
      btnStartGeneration.style.opacity = '1';

      loadHistory();
    }
  }

  async function startGenerationStream() {
    allGeneratedTCs = [];
    metricTCs.textContent = '0';
    updateComplianceScore([]);
    tableBody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding:30px; color:#94A3B8;">🚀 Generation in progress... Test cases will stream here live as they are generated.</td></tr>';

    const isForce = chkForceReprocess && chkForceReprocess.checked;
    if (isForce) {
      addLog('⚡ Force Re-process enabled: Bypassing cache to query AI model fresh!');
    } else {
      addLog('Connecting to Ollama model over SSH (gpt-oss:latest)...');
    }

    const streamUrl = isForce ? '/api/generate-stream?force=true' : '/api/generate-stream';

    try {
      const response = await fetch(streamUrl);
      if (!response.ok) {
        throw new Error(`Server returned error ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith(':')) continue;
          if (trimmed.startsWith('data:')) {
            try {
              const data = JSON.parse(trimmed.slice(5).trim());
              handleStreamPayload(data);
            } catch (jsonErr) {
              console.warn('Malformed stream payload:', trimmed);
            }
          }
        }
      }

      btnStartGeneration.disabled = false;
      btnStartGeneration.style.opacity = '1';

    } catch (err) {
      addLog(`Stream error: ${err.message}`);
      btnStartGeneration.disabled = false;
      btnStartGeneration.style.opacity = '1';
    }
  }

  function renderFullTable(testCases) {
    tableBody.innerHTML = '';
    testCases.forEach((tc, idx) => {
      const row = document.createElement('tr');
      const badgeClass = getBadgeClass(tc.test_type);

      row.innerHTML = `
        <td>${idx + 1}</td>
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

  // ==========================================
  // Real-Time Multi-Column Table Search Engine
  // ==========================================
  function filterTableRows() {
    const q = tableSearch.value.toLowerCase().trim();
    const rows = tableBody.querySelectorAll('tr');

    rows.forEach(r => {
      const rowText = r.textContent.toLowerCase();
      if (!q || rowText.includes(q)) {
        r.style.display = '';
      } else {
        r.style.display = 'none';
      }
    });
  }

  tableSearch.addEventListener('input', filterTableRows);
  tableSearch.addEventListener('keyup', filterTableRows);
  tableSearch.addEventListener('change', filterTableRows);

  // ==========================================
  // Execution History Management
  // ==========================================
  async function loadHistory() {
    try {
      const resp = await fetch('/api/history');
      if (resp.ok) {
        const history = await resp.json();
        renderHistoryList(history);
      }
    } catch (e) {
      console.error('History load error:', e);
    }
  }

  function renderHistoryList(history) {
    if (!history || history.length === 0) {
      historyList.innerHTML = `
        <div class="history-item">
          <div class="history-info">
            <h4>No past runs yet</h4>
            <p>Uploaded runs will appear here</p>
          </div>
        </div>
      `;
      return;
    }

    historyList.innerHTML = history.map(item => `
      <div class="history-item" id="history-row-${item.id}">
        <div class="history-info">
          <div class="history-title-row">
            <h4>${item.file_name}</h4>
            <span class="history-count-badge">${item.test_cases_count} TCs</span>
          </div>
          <p>${item.timestamp} • ${item.requirements_count} Reqs</p>
        </div>
        <div class="history-actions">
          <a href="/api/download?file_path=${encodeURIComponent(item.excel_path)}" class="btn-icon-history btn-icon-download" title="Download Excel Report">
            📥
          </a>
          <button class="btn-icon-history btn-icon-delete btn-delete-history" data-id="${item.id}" title="Delete History Entry">
            🗑️
          </button>
        </div>
      </div>
    `).join('');

    document.querySelectorAll('.btn-delete-history').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const runId = e.currentTarget.getAttribute('data-id');
        deleteHistoryItem(runId);
      });
    });
  }

  async function deleteHistoryItem(runId) {
    if (!confirm(`Are you sure you want to delete history entry ${runId}?`)) {
      return;
    }

    try {
      const resp = await fetch('/api/history-delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: runId })
      });

      if (resp.ok) {
        const row = document.getElementById(`history-row-${runId}`);
        if (row) {
          row.style.opacity = '0';
          row.style.transform = 'scale(0.9)';
          setTimeout(() => loadHistory(), 200);
        } else {
          loadHistory();
        }
      } else {
        alert('Failed to delete history item.');
      }
    } catch (err) {
      console.error('Delete history error:', err);
      alert(`Error deleting history: ${err.message}`);
    }
  }

  loadHistory();
});
