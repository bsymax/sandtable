/**
 * 品牌沙盘 M1 · API 根地址（本机开发 vs 生产 Nginx 同源）
 * 本机：静态 5510 + 后端 8000 分离 → 指向 8000
 * 生产：Nginx 反代 → 空字符串走同源
 */
(function (global) {
  function resolveApiBase() {
    if (global.__API_BASE__ != null && global.__API_BASE__ !== '') {
      return global.__API_BASE__;
    }
    if (global.location.protocol === 'file:') {
      return 'http://127.0.0.1:8000';
    }
    var host = global.location.hostname;
    var port = global.location.port;
    if (host === '127.0.0.1' || host === 'localhost') {
      if (port !== '8000') {
        return 'http://127.0.0.1:8000';
      }
      return 'http://127.0.0.1:8000';
    }
    return '';
  }
  global.M1_API_BASE = resolveApiBase();
})(window);
