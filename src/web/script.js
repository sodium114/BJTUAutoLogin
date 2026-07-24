// ========== PyWebView Python API 辅助 ==========

/** 动态获取 API（解决时序问题） */
function getApi() {
    return window.pywebview?.api;
}

// DOM 元素
const el = {
    studentId: document.getElementById('studentId'),
    password: document.getElementById('password'),
    togglePwd: document.getElementById('togglePassword'),
    showPwdCb: document.getElementById('showPasswordCheckbox'),
    loginBtn: document.getElementById('loginBtn'),
    clearLogBtn: document.querySelector('.clear-log-btn'),
    autoStart: document.getElementById('autoStart'),
    logContent: document.getElementById('logContent'),
    minimizeBtn: document.querySelector('.control.minimize'),
    closeBtn: document.querySelector('.control.close'),
};

// ========== 密码显示切换 ==========
if (el.togglePwd && el.password) {
    el.togglePwd.addEventListener('click', () => {
        const t = el.password.getAttribute('type') === 'password' ? 'text' : 'password';
        el.password.setAttribute('type', t);
        if (el.showPwdCb) el.showPwdCb.checked = t === 'text';
    });
}
if (el.showPwdCb && el.password) {
    el.showPwdCb.addEventListener('change', (e) => {
        el.password.setAttribute('type', e.target.checked ? 'text' : 'password');
    });
}

// ========== 窗口控制按钮 ==========
if (el.minimizeBtn) el.minimizeBtn.addEventListener('click', () => getApi()?.minimize());
if (el.closeBtn)    el.closeBtn.addEventListener('click', () => getApi()?.close());

// ========== 登录按钮 ==========
if (el.loginBtn) {
    el.loginBtn.addEventListener('click', async () => {
        const u = el.studentId?.value.trim() || '';
        const p = el.password?.value || '';
        if (!u) { log('警告', '请输入学号'); return; }
        if (!p) { log('警告', '请输入密码'); return; }

        log('信息', '正在登录...');
        const api = getApi();
        if (!api) { log('警告', 'API 未就绪'); return; }
        try {
            const r = await api.login(u, p);
            log(r.success ? '成功' : '警告',
                r.success ? '登录成功！' : `登录失败：${r.message}`);
        } catch (e) { log('警告', `登录异常：${e}`); }
    });
}

// ========== 清空日志 ==========
if (el.clearLogBtn) {
    el.clearLogBtn.addEventListener('click', async () => {
        if (el.logContent) el.logContent.innerHTML = '';
        getApi()?.clear_logs();
        log('信息', '日志已清空');
    });
}

// ========== 保存配置 & 日志查看 ==========
document.querySelectorAll('.action-item').forEach(item => {
    item.addEventListener('click', async () => {
        const t = item.querySelector('.action-title')?.textContent || '';
        if (t.includes('保存配置')) {
            const u = el.studentId?.value.trim() || '';
            const p = el.password?.value || '';
            if (!u || !p) { log('警告', '请先填写学号和密码再保存'); return; }
            try { await getApi()?.save_config(u, p); log('信息', '配置已保存'); }
            catch (e) { log('警告', `保存失败：${e}`); }
        } else if (t.includes('日志查看')) {
            getApi()?.open_log();
        }
    });
});

// ========== 开机自启 ==========
if (el.autoStart) {
    el.autoStart.addEventListener('change', async () => {
        const on = el.autoStart.checked;
        try { await getApi()?.set_autostart(on); }
        catch (e) { log('警告', `开机自启设置失败：${e}`); el.autoStart.checked = !on; }
    });
}

// ========== 日志工具 ==========
function log(type, msg) {
    if (!el.logContent) return;
    const d = new Date();
    const date = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
    const time = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    const t = `[${date} ${time}]`;
    const cls = type === '成功' ? 'success' : type === '警告' ? 'warning' : 'info';
    const e = document.createElement('div');
    e.className = 'log-entry';
    e.innerHTML = `<span class="log-time">${t}</span><span class="log-tag ${cls}">[${type}]</span><span class="log-msg">${msg}</span>`;
    el.logContent.appendChild(e);
    el.logContent.scrollTop = el.logContent.scrollHeight;
}
function pad(n) { return String(n).padStart(2, '0'); }

function parseLog(line) {
    if (!el.logContent) return;
    const m = line.match(/^\[([^\]]+)\]\s*(.*)/);
    if (!m) return;
    const msg = m[2];
    let t = 'info', l = '信息';
    if (/成功|登录成功/i.test(msg)) { t = 'success'; l = '成功'; }
    else if (/失败|错误|异常|警告|未连接/i.test(msg)) { t = 'warning'; l = '警告'; }
    const cls = t === 'success' ? 'success' : t === 'warning' ? 'warning' : 'info';
    const e = document.createElement('div');
    e.className = 'log-entry';
    e.innerHTML = `<span class="log-time">[${m[1]}]</span><span class="log-tag ${cls}">[${l}]</span><span class="log-msg">${msg}</span>`;
    el.logContent.appendChild(e);
}

// ========== 状态刷新 ==========
async function refreshStatus() {
    const api = getApi(); if (!api) return;
    try {
        const s = await api.get_status();
        updateStatusUI(s);
    } catch (e) {}
}

async function forceRefreshStatus() {
    const api = getApi(); if (!api) return;
    try {
        const s = await api.refresh_status();
        updateStatusUI(s);
    } catch (e) { refreshStatus(); }
}

function updateStatusUI(s) {
    const items = document.querySelectorAll('.status-item');
    if (items.length < 2) return;

    // WiFi
    const wifiIcon = items[0].querySelector('.status-icon.wifi svg');
    const wv = items[0].querySelector('.status-value');
    const wb = items[0].querySelector('.status-badge');
    const wbr = items[0].querySelector('.signal-bars');

    if (s.wifi_connected) {
        if (wifiIcon) wifiIcon.setAttribute('stroke', '#1a73e8');
        if (wv) { wv.textContent = s.wifi_ssid ? `已连接：${s.wifi_ssid}` : '已连接'; wv.className = 'status-value connected'; }
        if (wb) { wb.textContent = '已连接'; wb.className = 'status-badge connected'; }
        if (wbr) wbr.className = 'signal-bars';
    } else {
        if (wifiIcon) wifiIcon.setAttribute('stroke', '#e74c3c');
        if (wv) { wv.textContent = '未连接到 WiFi'; wv.className = 'status-value disconnected'; }
        if (wb) { wb.textContent = '未连接'; wb.className = 'status-badge disconnected'; }
        if (wbr) wbr.className = 'signal-bars off';
    }

    // 网络
    const netIcon = items[1].querySelector('.status-icon.network svg');
    const globeSvg = items[1].querySelector('.globe-icon svg');
    const nv = items[1].querySelector('.status-value');
    const nb = items[1].querySelector('.status-badge');

    if (s.net_connected) {
        if (netIcon) netIcon.setAttribute('stroke', '#1a73e8');
        if (globeSvg) globeSvg.setAttribute('stroke', '#22c55e');
        if (nv) { nv.textContent = '已连接到互联网'; nv.className = 'status-value connected'; }
        if (nb) { nb.textContent = '正常'; nb.className = 'status-badge normal'; }
    } else {
        if (netIcon) netIcon.setAttribute('stroke', '#e74c3c');
        if (globeSvg) globeSvg.setAttribute('stroke', '#e74c3c');
        if (nv) { nv.textContent = '网络不可用'; nv.className = 'status-value disconnected'; }
        if (nb) { nb.textContent = '异常'; nb.className = 'status-badge disconnected'; }
    }
}

// ========== 日志刷新 ==========
let lastLogCount = 0;
async function refreshLogs(force = false) {
    const api = getApi(); if (!api) return;
    try {
        const logs = await api.get_logs();
        if (force || logs.length !== lastLogCount) {
            if (el.logContent) {
                el.logContent.innerHTML = '';
                logs.forEach(l => parseLog(l));
                el.logContent.scrollTop = el.logContent.scrollHeight;
            }
            lastLogCount = logs.length;
        }
    } catch (e) {}
}

// ========== 启动 ==========
async function init() {
    const api = getApi();
    if (!api) { setTimeout(init, 200); return; }

    try {
        const c = await api.load_config();
        if (el.studentId && c.username) el.studentId.value = c.username;
        if (el.password && c.password) el.password.value = c.password;
    } catch (e) {}

    try {
        const a = await api.check_autostart();
        if (el.autoStart) el.autoStart.checked = a;
    } catch (e) {}

    await refreshLogs(true);
    await refreshStatus();
    setInterval(refreshStatus, 2000);
    setInterval(() => refreshLogs(false), 3000);

    // 状态图标点击重新检测
    document.querySelectorAll('.status-icon').forEach(icon => {
        icon.style.cursor = 'pointer';
        icon.title = '点击重新检测';
        icon.addEventListener('click', forceRefreshStatus);
    });

    // Logo 点击跳转 MIS 系统
    const logo = document.querySelector('.logo-circle');
    if (logo) {
        logo.style.cursor = 'pointer';
        logo.title = '北京交通大学 MIS 系统';
        logo.addEventListener('click', () => getApi()?.open_url('https://mis.bjtu.edu.cn/'));
    }
}

document.addEventListener('DOMContentLoaded', init);
