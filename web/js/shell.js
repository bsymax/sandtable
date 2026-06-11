/**
 * 品牌沙盘 M1 · 统一侧栏组件（Max 维护，模块页勿改）
 *
 * 用法：模块页 </body> 前加一行
 *   <script src="js/shell.js"></script>
 *
 * 作用：
 * - 在页面左侧注入与工作台 index.html 一致的导航侧栏（固定定位）
 * - 根据当前文件名自动高亮对应模块
 * - 所有 class 带 m1s- 前缀，不会与模块页自身样式冲突
 *
 * ⚠️ 合并 SOP 提醒（手册 §八）：合并新交付的模块页后，
 *    必须确认本文件引用仍在、侧栏正常显示。
 */
(function () {
  'use strict';

  var SIDEBAR_W = 256;

  // 四个标准页面（手册 §6.5）
  var NAV = [
    { section: '入口', items: [
      { href: 'index.html', icon: '\uD83D\uDCCB', label: '今日工作台', badge: null },
    ]},
    { section: '核心业务 · 三模块席', items: [
      { href: 'profile.html', icon: '\uD83C\uDFE2', label: '品牌档案', badge: '已接真库' },
      { href: 'visit.html',   icon: '\uD83C\uDFAF', label: '智能拜访助手', badge: '已接真库' },
      { href: 'intel.html',   icon: '\uD83D\uDD0D', label: '品牌情报流', badge: '已接真库' },
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
    'body{margin-left:' + SIDEBAR_W + 'px !important;}',
    '@media (max-width:900px){#m1s-sidebar{display:none;}body{margin-left:0 !important;}}',
  ].join('');

  function currentPage() {
    var p = window.location.pathname.split('/').pop() || 'index.html';
    return p;
  }

  function build() {
    // 注入样式
    var style = document.createElement('style');
    style.id = 'm1s-style';
    style.textContent = CSS;
    document.head.appendChild(style);

    // 注入侧栏
    var cur = currentPage();
    var html = '<div class="m1s-header">' +
      '<div class="m1s-name">品牌沙盘 <small>M1</small></div>' +
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
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', build);
  } else {
    build();
  }
})();
