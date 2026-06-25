/**
 * 品牌沙盘 M1 · 统一壳层（Max 维护，模块页勿改）
 *
 * 用法：模块页 </body> 前加一行
 *   <script src="js/shell.js"></script>
 *
 * 作用：
 * - 左侧导航侧栏（与工作台 index 一致）
 * - 三模块顶栏统一：← 工作台 › 品牌沙盘 M1 › 当前模块名
 * - #main 布局与 topbar-right 统一
 */
(function () {
  'use strict';

  var SIDEBAR_W = 256;

  var MODULE_PAGES = {
    'profile.html': '品牌档案',
    'visit.html': '智能拜访助手',
    'intel.html': '品牌情报流'
  };

  var NAV = [
    { section: '入口', items: [
      { href: 'index.html', icon: '\uD83D\uDCCB', label: '今日工作台', badge: null },
    ]},
    { section: '核心业务', items: [
      { href: 'profile.html', icon: '\uD83C\uDFE2', label: '品牌档案', badge: null },
      { href: 'visit.html',   icon: '\uD83C\uDFAF', label: '智能拜访助手', badge: null },
      { href: 'intel.html',   icon: '\uD83D\uDD0D', label: '品牌情报流', badge: null },
    ]},
  ];

  var CSS = [
    '#m1s-sidebar{position:fixed;top:0;left:0;bottom:0;width:' + SIDEBAR_W + 'px;',
    'background:#0f172a;color:#e2e8f0;display:flex;flex-direction:column;z-index:999;',
    'font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;}',
    '#m1s-sidebar .m1s-header{padding:18px 20px;border-bottom:1px solid rgba(255,255,255,.06);}',
    '#m1s-sidebar .m1s-name{font-size:16px;font-weight:700;letter-spacing:-.2px;color:#fff;}',
    '#m1s-sidebar .m1s-name small{font-size:11px;font-weight:500;color:#64748b;}',
    '#m1s-sidebar .m1s-sub{font-size:12px;color:#94a3b8;margin-top:6px;line-height:1.4;}',
    '#m1s-sidebar .m1s-nav{flex:1;overflow-y:auto;padding:8px 0;}',
    '#m1s-sidebar .m1s-sec-title{font-size:10px;text-transform:uppercase;letter-spacing:1.2px;color:#475569;padding:12px 20px 6px;font-weight:600;}',
    '#m1s-sidebar a.m1s-item{display:flex;align-items:center;gap:10px;padding:10px 20px;cursor:pointer;font-size:13px;',
    'color:#94a3b8;text-decoration:none;transition:all .15s;border-left:3px solid transparent;}',
    '#m1s-sidebar a.m1s-item:hover{background:rgba(255,255,255,.04);color:#e2e8f0;}',
    '#m1s-sidebar a.m1s-item.active{color:#fff;background:rgba(255,255,255,.06);border-left-color:#3b82f6;font-weight:500;}',
    '#m1s-sidebar .m1s-icon{width:18px;text-align:center;font-size:15px;flex-shrink:0;}',
    '#m1s-sidebar .m1s-label{flex:1;min-width:0;font-size:12px;line-height:1.35;white-space:nowrap;}',
    '#m1s-sidebar .m1s-badge{margin-left:auto;font-size:10px;padding:2px 6px;border-radius:8px;font-weight:600;background:#0e7c4b;color:#fff;}',
    'body.m1s-module{margin-left:' + SIDEBAR_W + 'px !important;}',
    'body.m1s-module #main{flex:1;display:flex;flex-direction:column;min-width:0;min-height:100vh;}',
    'body.m1s-module #main > .content{flex:1;overflow-y:auto;max-width:1200px;width:100%;margin:0 auto;}',
    'body.m1s-module .topbar{height:56px;background:#fff;border-bottom:1px solid #e3e8ee;display:flex;align-items:center;padding:0 28px;gap:20px;flex-shrink:0;position:relative;top:auto;z-index:10;}',
    'body.m1s-module .topbar .breadcrumb{font-size:13px;color:#697386;}',
    'body.m1s-module .topbar .breadcrumb a{color:#2f6fed;text-decoration:none;}',
    'body.m1s-module .topbar .breadcrumb .current{color:#1a1f36;font-weight:600;}',
    'body.m1s-module .topbar .topbar-right{margin-left:auto;display:flex;align-items:center;gap:16px;font-size:13px;color:#697386;}',
    'body.m1s-module .topbar .user-avatar{width:32px;height:32px;border-radius:50%;background:#3b82f6;color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;}',
    '@media (max-width:900px){#m1s-sidebar{display:none;}body.m1s-module{margin-left:0 !important;}}',
  ].join('');

  function currentPage() {
    return window.location.pathname.split('/').pop() || 'index.html';
  }

  function breadcrumbHtml(moduleName) {
    var sep = '<span style="margin:0 6px;color:#c1c9d2;">›</span>';
    return '<a href="index.html">← 工作台</a> ' + sep + ' 品牌沙盘 ' + sep +
      ' <span class="current">' + moduleName + '</span>';
  }

  function topbarRightHtml() {
    var d = new Date();
    var wd = ['日', '一', '二', '三', '四', '五', '六'];
    return '<span id="m1s-top-date">' + d.toISOString().slice(0, 10) + ' 周' + wd[d.getDay()] + '</span>' +
      '<span style="color:#a3acba;">|</span>' +
      '<a href="login.html" style="color:#0d7aff;text-decoration:none;">登录</a>' +
      '<div class="user-avatar">访</div>';
  }

  function ensureMainWrapper() {
    if (document.getElementById('main')) return;
    var topbar = document.querySelector('.topbar');
    var content = document.querySelector('.content');
    if (!topbar || !content) return;
    var parent = topbar.parentNode;
    if (parent !== document.body && parent !== document.getElementById('main')) return;
    if (parent === document.body) {
      var main = document.createElement('div');
      main.id = 'main';
      document.body.insertBefore(main, topbar);
      main.appendChild(topbar);
      main.appendChild(content);
    }
  }

  function normalizeModuleTopbar(moduleName) {
    ensureMainWrapper();
    var topbar = document.querySelector('.topbar');
    if (!topbar) return;
    var bc = topbar.querySelector('.breadcrumb');
    if (bc) bc.innerHTML = breadcrumbHtml(moduleName);
    var right = topbar.querySelector('.topbar-right');
    if (right) {
      right.innerHTML = topbarRightHtml();
      if (window.SandAuth && window.SandAuth.renderTopbarRight) {
        window.SandAuth.renderTopbarRight(right, window.SandAuth.getCachedUser());
        window.SandAuth.fetchMe().then(function (user) {
          window.SandAuth.renderTopbarRight(right, user);
        });
      }
    }
  }

  function build() {
    var cur = currentPage();
    var moduleName = MODULE_PAGES[cur];

    var style = document.createElement('style');
    style.id = 'm1s-style';
    style.textContent = CSS;
    document.head.appendChild(style);

    if (moduleName) document.body.classList.add('m1s-module');

    var html = '<div class="m1s-header">' +
      '<div class="m1s-name">品牌沙盘</div>' +
      '<div class="m1s-sub">Brand Sandtable · 厨小事业部</div>' +
      '</div><div class="m1s-nav">';
    NAV.forEach(function (sec) {
      html += '<div class="m1s-sec-title">' + sec.section + '</div>';
      sec.items.forEach(function (it) {
        var active = (it.href === cur) ? ' active' : '';
        html += '<a class="m1s-item' + active + '" href="' + it.href + '">' +
          '<span class="m1s-icon">' + it.icon + '</span>' +
          '<span class="m1s-label">' + it.label + '</span>' +
          (it.badge ? '<span class="m1s-badge">' + it.badge + '</span>' : '') +
          '</a>';
      });
    });
    html += '</div>';

    var bar = document.createElement('div');
    bar.id = 'm1s-sidebar';
    bar.innerHTML = html;
    document.body.insertBefore(bar, document.body.firstChild);

    if (moduleName) normalizeModuleTopbar(moduleName);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
