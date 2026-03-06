/**
 * UI Rendering Functions
 */

// Tab Navigation
function switchTab(tab) {
    ['upload', 'compare', 'history', 'reports'].forEach(t => {
        document.getElementById(t + 'Section').classList.add('hidden');
        document.getElementById('tab' + t.charAt(0).toUpperCase() + t.slice(1)).classList.remove('tab-active');
        document.getElementById('tab' + t.charAt(0).toUpperCase() + t.slice(1)).classList.add('text-gray-500', 'dark:text-gray-400');
    });

    document.getElementById(tab + 'Section').classList.remove('hidden');
    const tabBtn = document.getElementById('tab' + tab.charAt(0).toUpperCase() + tab.slice(1));
    tabBtn.classList.add('tab-active');
    tabBtn.classList.remove('text-gray-500', 'dark:text-gray-400');

    if (tab === 'history' && !historyLoaded) {
        loadHistory();
        historyLoaded = true;
    }

    if (tab === 'compare') {
        updateCompareVisibility();
    }
}

// Display Results
function displayResults(result) {
    document.getElementById('resultsSection').classList.remove('hidden');
    const alertsContainer = document.getElementById('validationAlerts');
    const issues = (result.validation || {}).issues || [];

    window.lastValidationIssues = issues;

    if (issues.length > 0) {
        alertsContainer.innerHTML = issues.map(issue =>
            '<div class="alert-' + issue.severity.toLowerCase() + ' px-4 py-3 rounded">' +
            '<div class="font-medium text-gray-800 dark:text-white">' + issue.message + '</div>' +
            '<div class="text-sm mt-1 text-gray-600 dark:text-gray-300">' + (issue.recommendation || '') + '</div></div>'
        ).join('');
    } else {
        alertsContainer.innerHTML = '<div class="bg-green-100 dark:bg-green-900 border-l-4 border-green-500 px-4 py-3 text-green-800 dark:text-green-200">Trích xuất thành công!</div>';
    }

    const dataContainer = document.getElementById('extractedDataDisplay');
    let html = '<div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4"><h3 class="font-bold text-lg mb-2 text-gray-800 dark:text-white">' + (extractedData.doc_type || 'Document') + '</h3><div class="grid grid-cols-1 gap-2 text-sm">';

    let hasData = false;
    allFields.forEach(f => {
        const value = extractedData[f.english];
        if (value !== null && value !== undefined && value !== '') {
            hasData = true;
            html += '<div class="flex justify-between py-1 border-b border-gray-200 dark:border-gray-700"><span class="font-medium text-gray-600 dark:text-gray-400">' + f.key + ':</span><span class="text-gray-800 dark:text-white">' + formatValue(value) + '</span></div>';
        }
    });

    if (!hasData) {
        html += '<div class="text-center text-gray-500 dark:text-gray-400 py-4">Không trích xuất được dữ liệu từ file PDF này</div>';
    }

    html += '</div>';
    dataContainer.innerHTML = html;
}

// Format Value
function formatValue(value) {
    if (value === null || value === undefined) return '';
    if (Array.isArray(value)) return value.map(v => JSON.stringify(v)).join(', ');
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
}

// Update Compare Visibility
function updateCompareVisibility() {
    const noCompareData = document.getElementById('noCompareData');
    const table = document.getElementById('compareTable').closest('table');

    if (!extractedData) {
        noCompareData.classList.remove('hidden');
        table.classList.add('hidden');
    } else {
        noCompareData.classList.add('hidden');
        table.classList.remove('hidden');
    }
}

// Update Comparison Table
function updateComparisonTable() {
    const tbody = document.getElementById('compareTable');
    if (!extractedData) {
        tbody.innerHTML = '<tr><td colspan="4" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">Chưa có dữ liệu</td></tr>';
        return;
    }

    tbody.innerHTML = allFields.map(field => {
        const extracted = extractedData[field.english] || '';
        const userEntered = comparisonData[field.key] || '';
        const isMatch = extracted && userEntered && String(extracted).toLowerCase().trim() === String(userEntered).toLowerCase().trim();
        let status = '<span class="text-gray-400">Chưa nhập</span>';
        if (userEntered) status = isMatch ? '<span class="text-green-600 dark:text-green-400 font-medium">Khớp</span>' : '<span class="text-red-600 dark:text-red-400 font-medium">Không khớp</span>';

        return '<tr class="' + (!isMatch && userEntered ? 'mismatch' : '') + '">' +
            '<td class="px-4 py-3 font-medium text-gray-700 dark:text-gray-300">' + field.key + '</td>' +
            '<td class="px-4 py-3 text-gray-800 dark:text-white">' + formatValue(extracted) + '</td>' +
            '<td class="px-4 py-3"><input type="text" data-field="' + field.key + '" value="' + userEntered + '" onchange="updateComparisonData(this)" class="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded px-2 py-1" placeholder="Nhập dữ liệu ECUSS..."></td>' +
            '<td class="px-4 py-3">' + status + '</td></tr>';
    }).join('');
}

// Update Comparison Data
function updateComparisonData(input) {
    comparisonData[input.dataset.field] = input.value;
    updateComparisonTable();
}

// Render History Table
function renderHistoryTable(sessions) {
    const tableEl = document.getElementById('historyTable');
    tableEl.innerHTML = sessions.map(session => createHistoryRow(session)).join('');
}

// Create History Row
function createHistoryRow(session) {
    const statusClass = session.status === 'PASSED' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
        session.status === 'WARNING' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
            'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';

    return '<tr class="fade-in">' +
        '<td class="px-4 py-3 font-mono text-sm text-gray-700 dark:text-gray-300">' + session.session_id.substring(0, 8) + '...</td>' +
        '<td class="px-4 py-3 text-gray-600 dark:text-gray-400">' + new Date(session.created_at).toLocaleString('vi-VN') + '</td>' +
        '<td class="px-4 py-3"><span class="px-2 py-1 rounded text-sm ' + statusClass + '">' + session.status + '</span></td>' +
        '<td class="px-4 py-3 text-gray-600 dark:text-gray-400">' + (session.file_count || 0) + '</td>' +
        '<td class="px-4 py-3"><button onclick="viewSession(\'' + session.session_id + '\')" class="text-blue-600 dark:text-blue-400 hover:underline">Xem</button></td></tr>';
}

// Generate Report
function generateReport() {
    const issues = window.lastValidationIssues || [];
    document.getElementById('reportCritical').textContent = issues.filter(i => i.severity === 'CRITICAL').length;
    document.getElementById('reportErrors').textContent = issues.filter(i => i.severity === 'ERROR').length;
    document.getElementById('reportWarnings').textContent = issues.filter(i => i.severity === 'WARNING').length;

    const detailsEl = document.getElementById('reportDetails');
    if (issues.length === 0) {
        detailsEl.innerHTML = '<div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4"><h3 class="font-bold mb-2 text-gray-800 dark:text-white">Chi tiết lỗi</h3><p class="text-gray-500 dark:text-gray-400">Không có lỗi nào được ghi nhận.</p></div>';
    } else {
        detailsEl.innerHTML = '<div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4"><h3 class="font-bold mb-2 text-gray-800 dark:text-white">Chi tiết lỗi</h3>' +
            issues.map(issue =>
                '<div class="mb-2 pb-2 border-b border-gray-200 dark:border-gray-700">' +
                '<div class="font-medium text-gray-800 dark:text-white">' + (issue.field_name || issue.field || 'N/A') + '</div>' +
                '<div class="text-sm text-gray-600 dark:text-gray-400">' + issue.message + '</div>' +
                '</div>'
            ).join('') + '</div>';
    }
}

// Toast Notifications
function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.remove('translate-y-20', 'opacity-0');
    setTimeout(() => toast.classList.add('translate-y-20', 'opacity-0'), 3000);
}

// Show Error
function showError(message) {
    const errorMsg = document.getElementById('errorMsg');
    errorMsg.textContent = message;
    errorMsg.classList.remove('hidden');
}

// Copy Results
function copyResults() {
    let text = '';
    allFields.forEach(f => {
        if (extractedData && extractedData[f.english])
            text += f.key + ': ' + extractedData[f.english] + '\n';
    });
    navigator.clipboard.writeText(text).then(() => showToast('Đã copy!'));
}

// Export Results to CSV
function exportResults() {
    let csv = '\uFEFFTrường dữ liệu,Giá trị\n';
    allFields.forEach(f => {
        if (extractedData && extractedData[f.english])
            csv += '"' + f.key + '","' + String(extractedData[f.english]).replace(/"/g, '""') + '"\n';
    });
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'extraction_results_' + Date.now() + '.csv';
    link.click();
    showToast('Đã export!');
}

// Toggle Dark Mode
function toggleDarkMode() {
    const html = document.documentElement;
    const btn = document.getElementById('darkModeBtn');

    html.classList.toggle('dark');

    if (html.classList.contains('dark')) {
        btn.textContent = 'Light Mode';
        localStorage.setItem('darkMode', 'enabled');
    } else {
        btn.textContent = 'Dark Mode';
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Initialize Dark Mode
function initDarkMode() {
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.documentElement.classList.add('dark');
        const btn = document.getElementById('darkModeBtn');
        btn.textContent = 'Light Mode';
    }
}

