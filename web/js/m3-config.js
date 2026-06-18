/**
 * 品牌沙盘 M4 · 全局配置（培翛模块 · Max 合并版）
 *
 * - M4-A: readonly 角色禁写（后端 require_writable 403 + 前端 UI 禁用）
 * - M4-C: 数仓 BI，经营数据 period_value（monthly YYYY-MM）
 */
(function (global) {
  'use strict';

  global.M3 = {
    LLM_ENABLED: true,
    LLM_GATEWAY_URL: '',
    LLM_TIMEOUT_SEC: 20,

    /** 主工程已接 M3-A，不再使用 Mock 登录 */
    USE_MOCK_AUTH: false,

    MOCK_USER: {
      id: 1,
      name: '周采销',
      dept: '厨小事业部 · 采销二组',
      avatar: '周',
      responsible_brands: ['jomoo'],
    },

    LLM_ROUTES: {
      record_extract: true,
      reminder_llm: true,
      profile_blurb: true,
      profile_strategy: true,
    },

    get currentRole() {
      try {
        var user = (global.SandAuth && global.SandAuth.getCachedUser) ? global.SandAuth.getCachedUser() : null;
        return (user && user.role) ? user.role : 'bd';
      } catch (e) {
        return 'bd';
      }
    },

    isWritable: function () {
      if (global.M3.USE_MOCK_AUTH) return true;
      return global.M3.currentRole !== 'readonly';
    },

    _dwLatestPeriod: null,
    _dwLatestFetchedAt: 0,
    _dwLatestNameKey: null,

    fetchDwLatestPeriod: function (nameKey) {
      var now = Date.now();
      if (
        global.M3._dwLatestPeriod &&
        global.M3._dwLatestNameKey === nameKey &&
        (now - global.M3._dwLatestFetchedAt < 300000)
      ) {
        return Promise.resolve(global.M3._dwLatestPeriod);
      }
      if (!nameKey) return Promise.resolve(null);
      var apiBase = global.M1_API_BASE || '';
      var headers = (global.SandAuth && global.SandAuth.authHeaders) ? global.SandAuth.authHeaders() : {};
      var url = apiBase + '/api/dw/latest-period?name_key=' + encodeURIComponent(nameKey);
      return fetch(url, { headers: headers })
        .then(function (r) {
          if (!r.ok) throw new Error('获取数仓周期失败');
          return r.json();
        })
        .then(function (data) {
          global.M3._dwLatestPeriod = data;
          global.M3._dwLatestFetchedAt = now;
          global.M3._dwLatestNameKey = nameKey;
          return data;
        })
        .catch(function () {
          return null;
        });
    },

    formatPeriodHint: function (periodValue) {
      if (!periodValue) return null;
      var w = String(periodValue).match(/^(\d{4})W(\d{2})$/);
      if (w) return w[1] + '年第' + parseInt(w[2], 10) + '周';
      var m = String(periodValue).match(/^(\d{4})-(\d{2})$/);
      if (m) return m[1] + '年' + parseInt(m[2], 10) + '月';
      return String(periodValue);
    },

    isResponsibleFor: function (nameKey) {
      if (!global.M3.USE_MOCK_AUTH) return true;
      var brands = global.M3.MOCK_USER.responsible_brands;
      return brands.indexOf(nameKey) !== -1;
    },

    filterBrandsForUser: function (brands) {
      if (!brands || !brands.length) return [];
      if (!global.M3.USE_MOCK_AUTH) return brands;
      return brands.filter(function (b) {
        return global.M3.isResponsibleFor(b.name_key);
      });
    },

    isLLMEnabled: function () {
      return global.M3.LLM_ENABLED;
    },

    isRouteEnabled: function (route) {
      return global.M3.LLM_ENABLED && global.M3.LLM_ROUTES[route];
    },
  };
})(window);
