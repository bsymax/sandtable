/**
 * 智能拜访助手 · API 接口封装
 * 连接到 FastAPI 后端：
 *
 * 使用方式：在 visit_assistant.html 中的 </body> 前引入此文件
 *   <script src="api.js"></script>
 */

var API_BASE = window.M1_API_BASE != null ? window.M1_API_BASE : '';

/**
 * 通用请求方法
 */
function api(path, options) {
  options = options || {};
  var method = options.method || 'GET';
  var body = options.body || null;
  var headers = { 'Content-Type': 'application/json' };

  if (options.headers) {
    for (var k in options.headers) {
      headers[k] = options.headers[k];
    }
  }
  if (window.SandAuth && window.SandAuth.authHeaders) {
    headers = window.SandAuth.authHeaders(headers);
  }

  var fetchOptions = {
    method: method,
    headers: headers,
  };

  if (body && method !== 'GET') {
    fetchOptions.body = JSON.stringify(body);
  }

  return fetch(API_BASE + path, fetchOptions)
    .then(function(res) {
      if (!res.ok) {
        return res.json().then(function(err) {
          throw new Error(err.detail || err.message || '请求失败 (' + res.status + ')');
        });
      }
      return res.json();
    });
}

// ===================================================
//  品牌
// ===================================================
function apiListBrands() {
  return api('/api/brands');
}

function apiListBrandsDetail() {
  return api('/api/brands/detail');
}

function apiGetBrand(nameKey) {
  return api('/api/brands/' + nameKey);
}

function apiGetBrandReminder(nameKey) {
  return api('/api/brands/' + nameKey + '/reminder');
}

// ===================================================
//  拜访
// ===================================================
function apiCreateVisit(data) {
  return api('/api/visits', { method: 'POST', body: data });
}

function apiListVisits(params) {
  var qs = [];
  if (params) {
    for (var k in params) {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        qs.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]));
      }
    }
  }
  var path = '/api/visits' + (qs.length ? '?' + qs.join('&') : '');
  return api(path);
}

function apiGetVisit(id) {
  return api('/api/visits/' + id);
}

function apiUpdateVisit(id, data) {
  return api('/api/visits/' + id, { method: 'PUT', body: data });
}

function apiDeleteVisit(id) {
  return api('/api/visits/' + id, { method: 'DELETE' });
}

// ===================================================
//  拜访记录
// ===================================================
function apiCreateRecord(data) {
  return api('/api/records', { method: 'POST', body: data });
}

function apiListRecords(params) {
  var qs = [];
  if (params) {
    for (var k in params) {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        qs.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]));
      }
    }
  }
  var path = '/api/records' + (qs.length ? '?' + qs.join('&') : '');
  return api(path);
}

// ===================================================
//  承诺
// ===================================================
function apiListCommitments(params) {
  var qs = [];
  if (params) {
    for (var k in params) {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        qs.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]));
      }
    }
  }
  return api('/api/commitments' + (qs.length ? '?' + qs.join('&') : ''));
}

function apiUpdateCommitment(id, data) {
  return api('/api/commitments/' + id, { method: 'PUT', body: data });
}

// ===================================================
//  待办
// ===================================================
function apiListTodos(params) {
  var qs = [];
  if (params) {
    for (var k in params) {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        qs.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]));
      }
    }
  }
  return api('/api/todos' + (qs.length ? '?' + qs.join('&') : ''));
}

function apiUpdateTodo(id, data) {
  return api('/api/todos/' + id, { method: 'PUT', body: data });
}

// ===================================================
//  健康度
// ===================================================
function apiGetHealth() {
  return api('/api/health');
}
