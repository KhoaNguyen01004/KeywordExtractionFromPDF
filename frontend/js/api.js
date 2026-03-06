/**
 * API Functions
 */

async function extractSingle(file) {
    if (!file) {
        showError('Vui lòng chọn 1 file PDF');
        return null;
    }

    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('errorMsg').classList.add('hidden');
    document.getElementById('resultsSection').classList.add('hidden');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(AppConfig.API_EXTRACT, { method: 'POST', body: formData });
        const result = await response.json();

        if (!response.ok) throw new Error(result.error || 'Có lỗi xảy ra');

        extractedData = result.data || {};
        currentSessionId = result.session_id;

        displayResults(result);
        updateComparisonTable();
        updateCompareVisibility();

        showToast('Trích xuất thành công!');
        return result;
    } catch (error) {
        showError('Lỗi: ' + error.message);
        return null;
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
}

async function saveComparisonData() {
    if (!currentSessionId) {
        showError('Không có phiên để lưu');
        return false;
    }
    try {
        const response = await fetch(AppConfig.API_SAVE_COMPARISON, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSessionId, comparison_data: comparisonData })
        });
        if (response.ok) {
            showToast('Đã lưu so sánh!');
            return true;
        } else {
            const result = await response.json();
            showError('Lỗi khi lưu: ' + (result.error || 'Unknown error'));
            return false;
        }
    } catch (error) {
        showError('Lỗi: ' + error.message);
        return false;
    }
}

async function loadHistory() {
    const loadingEl = document.getElementById('historyLoading');
    const errorEl = document.getElementById('historyError');
    const tableEl = document.getElementById('historyTable');
    const emptyEl = document.getElementById('historyEmpty');
    const loadMoreContainer = document.getElementById('loadMoreContainer');
    const historyCount = document.getElementById('historyCount');
    const refreshBtn = document.getElementById('refreshBtn');

    paginationState = {
        offset: 0,
        limit: AppConfig.DEFAULT_LIMIT,
        totalCount: 0,
        hasMore: false,
        isLoadingMore: false,
        allSessions: []
    };

    loadingEl.classList.remove('hidden');
    errorEl.classList.add('hidden');
    tableEl.closest('table').classList.add('hidden');
    emptyEl.classList.add('hidden');
    loadMoreContainer.classList.add('hidden');

    if (refreshBtn) refreshBtn.disabled = true;

    try {
        const response = await fetch(`${AppConfig.API_SESSIONS}?offset=0&limit=${AppConfig.DEFAULT_LIMIT}`);
        const result = await response.json();

        loadingEl.classList.add('hidden');
        if (refreshBtn) refreshBtn.disabled = false;

        if (!response.ok) {
            throw new Error(result.error || 'Failed to load history');
        }

        if (result.pagination) {
            paginationState.totalCount = result.pagination.total_count || 0;
            paginationState.hasMore = result.pagination.has_more || false;
        }
        paginationState.allSessions = result.sessions || [];

        if (historyCount && paginationState.totalCount > 0) {
            historyCount.textContent = paginationState.allSessions.length + '/' + paginationState.totalCount + ' phiên';
        }

        if (result.success && result.sessions && result.sessions.length > 0) {
            tableEl.closest('table').classList.remove('hidden');
            renderHistoryTable(result.sessions);

            if (paginationState.hasMore) {
                loadMoreContainer.classList.remove('hidden');
            }
        } else {
            emptyEl.classList.remove('hidden');
        }
    } catch (error) {
        loadingEl.classList.add('hidden');
        if (refreshBtn) refreshBtn.disabled = false;
        errorEl.textContent = 'Lỗi tải lịch sử: ' + error.message;
        errorEl.classList.remove('hidden');
        console.error('History load error:', error);
    }
}

async function loadMoreHistory() {
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    const loadMoreLoading = document.getElementById('loadMoreLoading');
    const tableEl = document.getElementById('historyTable');
    const historyCount = document.getElementById('historyCount');

    if (paginationState.isLoadingMore || !paginationState.hasMore) return;

    paginationState.isLoadingMore = true;
    loadMoreBtn.classList.add('hidden');
    loadMoreLoading.classList.remove('hidden');

    try {
        const newOffset = paginationState.offset + paginationState.limit;
        const response = await fetch(`${AppConfig.API_SESSIONS}?offset=${newOffset}&limit=${paginationState.limit}`);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Failed to load more');
        }

        if (result.pagination) {
            paginationState.hasMore = result.pagination.has_more || false;
        }

        const newSessions = result.sessions || [];
        paginationState.allSessions = [...paginationState.allSessions, ...newSessions];
        paginationState.offset = newOffset;

        // Append new rows
        const newRows = newSessions.map(session => createHistoryRow(session)).join('');
        tableEl.insertAdjacentHTML('beforeend', newRows);

        if (historyCount) {
            historyCount.textContent = paginationState.allSessions.length + '/' + paginationState.totalCount + ' phiên';
        }

        const loadMoreContainer = document.getElementById('loadMoreContainer');
        if (paginationState.hasMore) {
            loadMoreBtn.classList.remove('hidden');
        } else {
            loadMoreContainer.classList.add('hidden');
        }

    } catch (error) {
        console.error('Load more error:', error);
        showToast('Lỗi tải thêm dữ liệu');
        loadMoreBtn.classList.remove('hidden');
    } finally {
        paginationState.isLoadingMore = false;
        loadMoreLoading.classList.add('hidden');
    }
}

async function viewSession(sessionId) {
    try {
        const response = await fetch(AppConfig.API_SESSION_DETAIL + sessionId);
        const data = await response.json();

        if (data.success) {
            if (data.session && data.session.uploads && data.session.uploads.length > 0) {
                extractedData = data.session.uploads[0].extracted_data;
                currentSessionId = sessionId;
                updateComparisonTable();
                updateCompareVisibility();
            }
            switchTab('compare');
            showToast('Đã tải phiên: ' + sessionId.substring(0, 8) + '...');
        }
    } catch (error) {
        showError('Lỗi tải phiên: ' + error.message);
    }
}

async function refreshHistory() {
    await loadHistory();
    showToast('Đã cập nhật lịch sử');
}

// Export functions to global scope for onclick handlers in HTML
// Wrapper function to handle file extraction from UI
window.handleExtractClick = function () {
    // Get the selectedFile from global scope (defined in config.js)
    if (typeof selectedFile === 'undefined' || !selectedFile) {
        showError('Vui lòng chọn 1 file PDF trước');
        return;
    }
    // Call the extractSingle function defined in this file (api.js)
    extractSingle(selectedFile);
};

// Wrapper for remove file
window.handleRemoveFile = function () {
    removeFile();
};

window.saveComparison = saveComparisonData;
window.refreshHistory = refreshHistory;
window.viewSession = viewSession;
window.loadMoreHistory = loadMoreHistory;
window.generateReport = generateReport;
window.copyResults = copyResults;
window.exportResults = exportResults;
window.toggleDarkMode = toggleDarkMode;
window.switchTab = switchTab;
window.updateComparisonData = updateComparisonData;

