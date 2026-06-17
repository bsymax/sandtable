/**
 * 品牌沙盘 M3 · 全局配置（培翛模块 · Max 合并版）
 *
 * - 品牌过滤走 M3-A：/api/brands 已按登录用户权限返回
 * - LLM 各路开关默认 false；Max 在 .env 开 LLM 后再逐路打开 LLM_ROUTES（含 profile_blurb / profile_strategy）
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
      responsible_brands: ['midea'],
    },

    LLM_ROUTES: {
      record_extract: true,
      reminder_llm: true,
      profile_blurb: true,
      profile_strategy: true,
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
