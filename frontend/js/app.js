// ===================== STATE =====================
const state = {
    authToken: null,
    user: null,
    student: { name: '', id: '', class: '', discipline: '' },
    gabarito: null,
    capturedBlob: null,
    originalImageUrl: null,
    processedImageUrl: null,
    correctionId: null,
    result: null,
};

// ===================== DOM REFS =====================
const $ = (id) => document.getElementById(id);
const viewer = new Viewer();

const camera = new CameraManager(
    $('camera-view'), $('status-text'), $('camera-status')
);

// ===================== MODALS =====================
function showModal(id) { $(id).classList.remove('hidden'); }
function hideModal(id) { $(id).classList.add('hidden'); }

// Login
$('btn-login-submit').addEventListener('click', doLogin);
$('btn-login-skip').addEventListener('click', () => {
    hideModal('login-modal');
    showModal('student-modal');
});
$('login-user').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') $('login-pass').focus();
});
$('login-pass').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doLogin();
});

async function doLogin() {
    const username = $('login-user').value.trim();
    const password = $('login-pass').value.trim();
    const errEl = $('login-error');
    errEl.style.display = 'none';

    if (!username || !password) {
        errEl.textContent = 'Preencha usuário e senha';
        errEl.style.display = 'block';
        return;
    }

    try {
        const res = await fetch(CONFIG.api.baseUrl + CONFIG.api.endpoints.login, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.detail || 'Falha no login');
        }

        const data = await res.json();
        state.authToken = data.access_token;

        const me = await fetch(CONFIG.api.baseUrl + CONFIG.api.endpoints.me, {
            headers: { Authorization: `Bearer ${state.authToken}` },
        });
        if (me.ok) {
            state.user = await me.json();
            $('header-user').textContent =
                `Professor(a) ${state.user.full_name} - Sistema de Correção`;
        }

        hideModal('login-modal');
        showModal('student-modal');
    } catch (error) {
        errEl.textContent = error.message;
        errEl.style.display = 'block';
    }
}

// Student form
$('btn-student-confirm').addEventListener('click', confirmStudent);
$('student-name').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') $('student-id').focus();
});
$('student-id').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') $('student-class').focus();
});
$('student-class').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') $('student-discipline').focus();
});
$('student-discipline').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') confirmStudent();
});

function confirmStudent() {
    const name = $('student-name').value.trim();
    const id = $('student-id').value.trim();
    const cls = $('student-class').value.trim();

    if (!name || !id || !cls) {
        alert('Preencha nome, matrícula e turma do aluno.');
        return;
    }

    state.student = { name, id, class: cls, discipline: $('student-discipline').value.trim() };

    const gabText = $('gabarito-input').value.trim();
    if (gabText) {
        try {
            state.gabarito = JSON.parse(gabText);
        } catch {
            alert('Gabarito inválido. Use formato JSON: {"1":"A","2":"B"}');
            return;
        }
    }

    hideModal('student-modal');
    updateStudentInfo();
    camera.start();
}

function updateStudentInfo() {
    const s = state.student;
    $('info-student').textContent = `${s.name} (${s.id})`;
}

// ===================== CAMERA =====================
camera.onActiveChange = (active) => {
    $('btn-capture').disabled = !active;
};

async function capturePhoto() {
    const canvas = camera.capture();
    if (!canvas) return;

    $('flash').classList.add('active');
    setTimeout(() => $('flash').classList.remove('active'), 500);

    canvas.toBlob((blob) => {
        state.capturedBlob = blob;
        state.originalImageUrl = URL.createObjectURL(blob);

        $('canvas-preview').src = state.originalImageUrl;
        cameraView.style.display = 'none';
        $('canvas-preview').style.display = 'block';
        $('overlay').style.display = 'none';

        viewer.showOriginal(state.originalImageUrl);
        updateUI('captured');
        updateImageInfo(canvas.width, canvas.height);
    }, CONFIG.image.format, CONFIG.image.quality);
}

function resetCamera() {
    cameraView.style.display = 'block';
    $('canvas-preview').style.display = 'none';
    $('overlay').style.display = 'block';

    state.capturedBlob = null;
    state.originalImageUrl = null;
    state.processedImageUrl = null;
    state.correctionId = null;
    state.result = null;

    viewer.clear();
    updateUI('camera');
    $('image-info').style.display = 'none';
    $('processing-steps').style.display = 'none';
}

// ===================== UI HELPERS =====================
function updateUI(mode) {
    const c = $('btn-capture');
    const r = $('btn-retake');
    const a = $('btn-analyze');
    const s = $('btn-send');

    c.style.display = 'none';
    r.style.display = 'none';
    a.style.display = 'none';
    s.style.display = 'none';

    if (mode === 'camera') {
        c.style.display = 'block';
    } else if (mode === 'captured') {
        r.style.display = 'block';
        a.style.display = 'block';
        $('image-info').style.display = 'block';
        $('processing-steps').style.display = 'block';
    } else if (mode === 'processed') {
        r.style.display = 'block';
        s.style.display = 'block';
        $('image-info').style.display = 'block';
    } else if (mode === 'result') {
        r.style.display = 'block';
        $('image-info').style.display = 'block';
    }

    if (mode === 'captured' || mode === 'processed') {
        document.querySelectorAll('.step').forEach(el =>
            el.classList.remove('completed', 'active')
        );
    }
}

function updateImageInfo(w, h) {
    $('info-resolution').textContent = `${w} x ${h}px`;
    $('info-quality').textContent = `${((w * h) / 1e6).toFixed(1)} MP`;
    $('info-detection').textContent = 'Pendente';
    $('info-detection').style.color = '#764ba2';
}

function showLoading(msg) {
    $('loading-text').textContent = msg;
    $('loading').classList.add('show');
}

function hideLoading() {
    $('loading').classList.remove('show');
}

function stepActive(id) {
    const el = $(id);
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    if (el) el.classList.add('active');
}

function stepDone(id) {
    const el = $(id);
    if (el) { el.classList.remove('active'); el.classList.add('completed'); }
}

// ===================== PROCESS =====================
async function processImage() {
    if (!state.capturedBlob) return;

    showLoading('Enviando imagem para processamento...');

    try {
        const fd = new FormData();
        fd.append('file', state.capturedBlob, 'captura.jpg');
        fd.append('student_name', state.student.name);
        fd.append('student_id', state.student.id);
        fd.append('class_name', state.student.class);
        fd.append('discipline', state.student.discipline);

        const headers = {};
        if (state.authToken) headers['Authorization'] = `Bearer ${state.authToken}`;

        stepActive('step-upload');
        const upRes = await fetch(
            CONFIG.api.baseUrl + CONFIG.api.endpoints.upload,
            { method: 'POST', headers, body: fd }
        );
        if (!upRes.ok) {
            const err = await upRes.json().catch(() => ({}));
            throw new Error(err.detail || 'Erro no upload');
        }
        const correction = await upRes.json();
        state.correctionId = correction.id;
        stepDone('step-upload');

        // Process
        stepActive('step-detect');
        const procFd = new FormData();
        if (state.gabarito) {
            procFd.append('gabarito', JSON.stringify(state.gabarito));
        }

        const procRes = await fetch(
            CONFIG.api.baseUrl + `/api/corrections/${correction.id}/process`,
            { method: 'POST', headers, body: procFd }
        );
        if (!procRes.ok) {
            const err = await procRes.json().catch(() => ({}));
            throw new Error(err.detail || 'Erro no processamento');
        }

        state.result = await procRes.json();
        stepDone('step-detect');
        stepDone('step-perspective');
        stepDone('step-omr');

        // Load processed image
        if (state.result.processed_image_url) {
            state.processedImageUrl = CONFIG.api.baseUrl + state.result.processed_image_url;
            const img = new Image();
            img.onload = () => {
                viewer.showProcessed(state.processedImageUrl);
                viewer.showComparison(state.originalImageUrl, state.processedImageUrl);
            };
            img.src = state.processedImageUrl;
        }

        $('info-detection').textContent = 'Detectado ✓';
        $('info-detection').style.color = '#28a745';
        updateUI('processed');

    } catch (error) {
        console.error('Erro:', error);
        $('info-detection').textContent = 'Falha';
        $('info-detection').style.color = '#dc3545';
        alert('Erro: ' + error.message);
        document.querySelectorAll('.step.active').forEach(s => {
            s.classList.remove('active');
            s.classList.add('completed');
        });
    } finally {
        hideLoading();
    }
}

// ===================== RESULT =====================
function showResult() {
    if (!state.result) {
        alert('Processe a imagem primeiro.');
        return;
    }

    viewer.switchTab('result');
    renderResult();
}

function renderResult() {
    const r = state.result;
    const summary = $('result-summary');
    const details = $('result-details');

    const score = r.score;
    const scoreClass = score >= 70 ? 'score-high' : score >= 40 ? 'score-medium' : 'score-low';

    summary.innerHTML = `
        <div class="result-card result-score">
            <div class="score-value ${scoreClass}">
                ${score != null ? score + '%' : 'N/A'}
            </div>
            <div class="score-label">Pontuação</div>
        </div>
        <div class="result-card">
            <div class="result-stat">
                <span class="result-stat-label">Aluno</span>
                <span class="result-stat-value">${state.student.name}</span>
            </div>
            <div class="result-stat">
                <span class="result-stat-label">Matrícula</span>
                <span class="result-stat-value">${state.student.id}</span>
            </div>
            <div class="result-stat">
                <span class="result-stat-label">Turma</span>
                <span class="result-stat-value">${state.student.class}</span>
            </div>
            ${r.total_questions != null ? `
            <div class="result-stat">
                <span class="result-stat-label">Total de Questões</span>
                <span class="result-stat-value">${r.total_questions}</span>
            </div>
            ` : ''}
            ${r.correct_answers != null ? `
            <div class="result-stat">
                <span class="result-stat-label">Acertos</span>
                <span class="result-stat-value">${r.correct_answers}</span>
            </div>
            ` : ''}
            <div class="result-stat">
                <span class="result-stat-label">Confiança Média</span>
                <span class="result-stat-value">${(r.confidence * 100).toFixed(0)}%</span>
            </div>
        </div>
    `;

    if (r.details && r.details.length > 0) {
        let html = '<div class="result-card"><h4 style="margin-bottom:8px;">Detalhamento</h4>';
        r.details.forEach(q => {
            const correct = q.correct;
            const badge = correct === true ? 'badge-correct' :
                          correct === false ? 'badge-wrong' : 'badge-unknown';
            const label = correct === true ? '✓' :
                          correct === false ? '✗' : '?';

            html += `
                <div class="result-question">
                    <span class="result-q-num">${q.number}.</span>
                    <span class="result-q-badge ${badge}">${label}</span>
                    <span>${q.chosen || '-'}</span>
                    ${q.expected ? `<span style="color:#6c757d;font-size:12px;">(esperado: ${q.expected})</span>` : ''}
                    <span class="result-q-confidence">conf: ${(q.confidence * 100).toFixed(0)}%</span>
                </div>
            `;
        });
        html += '</div>';
        details.innerHTML = html;
    } else {
        details.innerHTML = '';
    }
}

// ===================== EVENTS =====================
$('btn-capture').addEventListener('click', capturePhoto);
$('btn-retake').addEventListener('click', resetCamera);
$('btn-analyze').addEventListener('click', processImage);
$('btn-send').addEventListener('click', showResult);

// ===================== INIT =====================
window.addEventListener('load', () => {
    showModal('login-modal');
    $('login-user').focus();
});

window.addEventListener('beforeunload', () => camera.stop());

document.addEventListener('visibilitychange', () => {
    if (document.hidden) { camera.stop(); }
    else { camera.start(); }
});
