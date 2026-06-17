/**
 * M3 登录态 · Max 维护
 * 用法：api-base.js 之后、业务脚本之前引入
 */
(function (global) {
  'use strict';

  var TOKEN_KEY = 'sandtable_auth_token';
  var USER_KEY = 'sandtable_auth_user';

  function getToken() {
    return localStorage.getItem(TOKEN_KEY) || '';
  }

  function setToken(token) {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  }

  function getCachedUser() {
    try {
      var raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function setCachedUser(user) {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(USER_KEY);
  }

  function authHeaders(extra) {
    var h = extra ? Object.assign({}, extra) : {};
    var t = getToken();
    if (t) h.Authorization = 'Bearer ' + t;
    if (!h['Content-Type'] && !h['content-type']) h['Content-Type'] = 'application/json';
    return h;
  }

  function apiBase() {
    return global.M1_API_BASE != null ? global.M1_API_BASE : '';
  }

  function fetchMe() {
    var t = getToken();
    if (!t) return Promise.resolve(null);
    return fetch(apiBase() + '/api/auth/me', { headers: authHeaders() })
      .then(function (r) {
        if (!r.ok) throw new Error('未登录');
        return r.json();
      })
      .then(function (data) {
        setCachedUser(data);
        return data;
      })
      .catch(function () {
        setToken('');
        setCachedUser(null);
        return null;
      });
  }

  function login(username, password) {
    return fetch(apiBase() + '/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username, password: password }),
    }).then(function (r) {
      return r.json().then(function (data) {
        if (!r.ok) throw new Error(data.detail || '登录失败');
        setToken(data.token);
        setCachedUser(data);
        return data;
      });
    });
  }

  function logout() {
    var t = getToken();
    setToken('');
    setCachedUser(null);
    if (!t) return Promise.resolve();
    return fetch(apiBase() + '/api/auth/logout', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + t },
    }).catch(function () {});
  }

  function avatarChar(name) {
    if (!name) return '?';
    return name.trim().charAt(0);
  }

  function renderTopbarRight(container, user) {
    if (!container) return;
    var d = new Date();
    var wd = ['日', '一', '二', '三', '四', '五', '六'];
    var dateHtml = '<span id="m1s-top-date">' + d.toISOString().slice(0, 10) + ' 周' + wd[d.getDay()] + '</span>';
    var teamHtml = '<span style="color:#a3acba;">|</span><span>厨小事业部 · 采销二组</span>';

    if (user && user.display_name) {
      container.innerHTML =
        dateHtml + teamHtml +
        '<span style="color:#a3acba;">|</span>' +
        '<span id="auth-user-label">' + user.display_name + '</span>' +
        '<div class="user-avatar" title="' + user.username + '">' + avatarChar(user.display_name) + '</div>' +
        '<a href="#" id="auth-logout-link" style="color:#697386;font-size:12px;text-decoration:none;">退出</a>';
      var link = container.querySelector('#auth-logout-link');
      if (link) {
        link.addEventListener('click', function (e) {
          e.preventDefault();
          logout().then(function () {
            window.location.href = 'login.html';
          });
        });
      }
      return;
    }

    container.innerHTML =
      dateHtml + teamHtml +
      '<span style="color:#a3acba;">|</span>' +
      '<a href="login.html" style="color:#0d7aff;text-decoration:none;">登录</a>' +
      '<div class="user-avatar">访</div>';
  }

  function initTopbar() {
    var right = document.querySelector('.topbar-right');
    if (!right) return Promise.resolve(null);
    return fetchMe().then(function (user) {
      renderTopbarRight(right, user || getCachedUser());
      return user;
    });
  }

  global.SandAuth = {
    getToken: getToken,
    setToken: setToken,
    getCachedUser: getCachedUser,
    authHeaders: authHeaders,
    fetchMe: fetchMe,
    login: login,
    logout: logout,
    initTopbar: initTopbar,
    renderTopbarRight: renderTopbarRight,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTopbar);
  } else {
    initTopbar();
  }
})(window);
