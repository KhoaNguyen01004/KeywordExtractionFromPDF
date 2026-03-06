/**
 * Configuration and Constants
 */

const AppConfig = {
    // API Endpoints
    API_EXTRACT: '/api/extract',
    API_SAVE_COMPARISON: '/api/save-comparison',
    API_SESSIONS: '/api/sessions',
    API_SESSION_DETAIL: '/api/session/',

    // Pagination
    DEFAULT_LIMIT: 20,

    // File types
    ACCEPTED_FILE_TYPE: '.pdf'
};

// Field definitions for data extraction
const allFields = [
    { key: 'Số vận đơn', english: 'bl_no' },
    { key: 'Mã số hàng hóa', english: 'hs_code' },
    { key: 'Người xuất khẩu', english: 'shipper' },
    { key: 'Người nhập khẩu', english: 'consignee' },
    { key: 'Địa điểm lưu kho', english: 'warehouse_location' },
    { key: 'Địa điểm dỡ hàng', english: 'discharge_place' },
    { key: 'Ngày hàng đi', english: 'departure_date' },
    { key: 'Ngày hàng đến', english: 'arrival_date' },
    { key: 'Trọng lượng', english: 'total_weight' },
    { key: 'Số lượng', english: 'total_packages' },
    { key: 'Số container', english: 'containers' },
    { key: 'Mã bộ phận xử lý tờ khai', english: 'declaration_office_code' }
];

// Pagination state
let paginationState = {
    offset: 0,
    limit: AppConfig.DEFAULT_LIMIT,
    totalCount: 0,
    hasMore: false,
    isLoadingMore: false,
    allSessions: []
};

// Application state
let extractedData = null;
let currentSessionId = null;
let comparisonData = {};
let historyLoaded = false;
let selectedFile = null;

