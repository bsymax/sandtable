/**
 * M3/M5 登录态 · Max 维护
 */
(function (global) {
  'use strict';

  var TOKEN_KEY = 'sandtable_auth_token';
  var USER_KEY = 'sandtable_auth_user';
  var GUARD_PAGES = ['index.html', 'profile.html', 'visit.html', 'intel.html', 'admin-users.html', 'admin-llm.html'];

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

  function currentPage() {
    return window.location.pathname.split('/').pop() || 'index.html';
  }

  function redirectToChangePassword(next) {
    var target = next || window.location.pathname.split('/').pop() || 'index.html';
    window.location.href = 'change-password.html?next=' + encodeURIComponent(target);
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

  function changePassword(oldPassword, newPassword) {
    return fetch(apiBase() + '/api/auth/change-password', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    }).then(function (r) {
      return r.json().then(function (data) {
        if (!r.ok) throw new Error(data.detail || '修改失败');
        var cached = getCachedUser() || {};
        cached.must_change_password = false;
        setCachedUser(cached);
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

  function userDeptLabel(user) {
    if (user && user.dept) return user.dept;
    return '';
  }

  function renderTopbarRight(container, user) {
    if (!container) return;
    var d = new Date();
    var wd = ['日', '一', '二', '三', '四', '五', '六'];
    var dateHtml = '<span id="m1s-top-date">' + d.toISOString().slice(0, 10) + ' 周' + wd[d.getDay()] + '</span>';
    var dept = userDeptLabel(user);
    var teamHtml = dept
      ? '<span style="color:#a3acba;">|</span><span>' + dept + '</span>'
      : '';

    if (user && user.display_name) {
      var adminUsersLink = user.role === 'admin'
        ? '<a href="admin-users.html" style="color:#697386;font-size:12px;text-decoration:none;margin-right:8px;">用户管理</a>'
        : '';
      var adminLlmLink = user.role === 'admin'
        ? '<a href="admin-llm.html" style="color:#697386;font-size:12px;text-decoration:none;margin-right:8px;">llm状态</a>'
        : '';
      var pwdLink = '<a href="change-password.html" style="color:#697386;font-size:12px;text-decoration:none;margin-right:8px;">修改密码</a>';
      container.innerHTML =
        dateHtml + teamHtml +
        '<span style="color:#a3acba;">|</span>' +
        '<span id="auth-user-label">' + user.display_name + '</span>' +
        '<div class="user-avatar" title="' + user.username + '">' + avatarChar(user.display_name) + '</div>' +
        adminUsersLink + adminLlmLink + pwdLink +
        '<a href="#" id="auth-logout-link" style="color:#697386;font-size:12px;text-decoration:none;">退出</a>';
      var link = container.querySelector('#auth-logout-link');
      if (link) {
        link.addEventListener('click', function (e) {
          e.preventDefault();
          logout().then(function () { window.location.href = 'login.html'; });
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

  function guardMustChangePassword() {
    var page = currentPage();
    if (page === 'login.html' || page === 'change-password.html') return Promise.resolve(null);
    if (GUARD_PAGES.indexOf(page) === -1) return Promise.resolve(null);
    return fetchMe().then(function (user) {
      if (!user) return null;
      if (user.must_change_password) {
        redirectToChangePassword(page);
        return null;
      }
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
    changePassword: changePassword,
    initTopbar: initTopbar,
    renderTopbarRight: renderTopbarRight,
    guardMustChangePassword: guardMustChangePassword,
  };

  function boot() {
    initTopbar();
    guardMustChangePassword();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})(window);
