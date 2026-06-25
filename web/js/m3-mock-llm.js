/**
 * 品牌沙盘 M5 · 纪要/提醒 LLM 前端（培翛 · M5 补丁 0623）
 *
 * M5 变更:
 * - 去待办，只抽提承诺
 * - 从 会谈议题 + 承诺事项 + 未达成 综合文本中提取承诺人/内容/截止
 * - AI 面板承诺可编辑
 */
(function (global) {
  'use strict';

  var M3 = global.M3;

  var MAX_MINUTES_CHARS = 3000;
  var MAX_AI_INPUT_CHARS = 2400;

  // 承诺方关键词：品牌方 vs 我方
  var BRAND_PARTY_KEYS = ['品牌方', '供应商', '对方', '他们', '九牧', '美的', '苏泊尔', '小熊', '摩飞', '箭牌', 'brand'];
  var BD_PARTY_KEYS = ['我方', '我们', '采销', '厨小', '京东', '我方承诺', '我方负责'];

  // 承诺内容关键词模板（按行匹配，优先级高于整文匹配）
  var COMMIT_KEYWORDS = [
    { keys: ['投放', '预算', '联合投放', '广告', '资源'], content: '联合投放/广告资源确认' },
    { keys: ['新品', '首发', '排期', '上市', '上市时间'], content: '新品首发排期确认' },
    { keys: ['价格', '降价', '折扣', '包销', '专供', '报价'], content: '价格/包销方案确认' },
    { keys: ['库存', '备货', '供应链', '断货', '供货'], content: '库存/供应链保障' },
    { keys: ['大促', '618', '双11', '活动', '促销', '大促活动'], content: '大促活动方案对齐' },
    { keys: ['人员', '变动', '换人', '岗位', '调整', '组织'], content: '人员变动/决策链确认' },
    { keys: ['续约', '框架', '年度', '合同', '签署'], content: '年度框架/续约签署' },
    { keys: ['客诉', '品质', '质量', '售后', '投诉'], content: '客诉/品质问题处理' },
    { keys: ['数据', '报表', '份额', '占比', '经营数据'], content: '经营数据同步' },
    { keys: ['培训', '赋能', '产品培训', '演示'], content: '产品培训/赋能支持' },
    { keys: ['费用', '返利', '补贴', '结算'], content: '费用/返利结算' },
  ];

  var _WEEKDAY_OFFSET = { '一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'日':0,'天':0 };
  function _tryExtractDeadline(text) {
    if (!text) return null;
    var m1 = text.match(/(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})/);
    if (m1) return m1[1] + '-' + String(m1[2]).padStart(2,'0') + '-' + String(m1[3]).padStart(2,'0');
    var now = new Date();
    var m2 = text.match(/(\d{1,2})\s*月\s*(\d{1,2})\s*[日号]/);
    if (m2) return String(now.getFullYear()) + '-' + String(m2[1]).padStart(2,'0') + '-' + String(m2[2]).padStart(2,'0');
    var m2b = text.match(/(\d{1,2})[-\/](\d{1,2})/);
    if (m2b) return String(now.getFullYear()) + '-' + String(m2b[1]).padStart(2,'0') + '-' + String(m2b[2]).padStart(2,'0');
    var nextWeek = text.match(/下周\s*([一二三四五六日天])/);
    if (nextWeek) { var w = _WEEKDAY_OFFSET[nextWeek[1]]; if (w == null) return null; var d = new Date(); var curDay = d.getDay(); var diff = (7 - curDay) + w; d.setDate(d.getDate() + diff); return d.toISOString().split('T')[0]; }
    var thisWeek = text.match(/本周\s*([一二三四五六日天])/);
    if (thisWeek) { var w2 = _WEEKDAY_OFFSET[thisWeek[1]]; if (w2 == null) return null; var d2 = new Date(); var curDay2 = d2.getDay(); var diff2 = w2 - curDay2; if (diff2 < 0) diff2 = 0; d2.setDate(d2.getDate() + diff2); return d2.toISOString().split('T')[0]; }
    if (/明[天日]/.test(text)) { var d3 = new Date(); d3.setDate(d3.getDate()+1); return d3.toISOString().split('T')[0]; }
    if (/后[天日]/.test(text)) { var d4 = new Date(); d4.setDate(d4.getDate()+2); return d4.toISOString().split('T')[0]; }
    var ndays = text.match(/(\d{1,2})\s*天\s*[后内]/);
    if (ndays) { var d5 = new Date(); d5.setDate(d5.getDate()+parseInt(ndays[1],10)); return d5.toISOString().split('T')[0]; }
    return null;
  }

  // v1.1: 去除内容中的日期信息（截止日期独立存储到 deadline 字段）
  function _stripDateInfo(text) {
    if (!text) return text;
    var stripped = text
      .replace(/\d{4}[-\/]\d{1,2}[-\/]\d{1,2}/g, '')
      .replace(/\d{1,2}\s*月\s*\d{1,2}\s*[日号]/g, '')
      .replace(/\d{1,2}[-\/]\d{1,2}/g, '')
      .replace(/下周\s*[一二三四五六日天]/g, '')
      .replace(/本周\s*[一二三四五六日天]/g, '')
      .replace(/明[天日]/g, '')
      .replace(/后[天日]/g, '')
      .replace(/\d{1,2}\s*天\s*[后内]/g, '')
      .replace(/[\s\n]*[（(][\s\n]*截止[日期]?[：:]\s*\S+[\s\n]*[）)]?/g, '')
      .replace(/[\s\n]*[（(][\s\n]*DDL[：:]\s*\S+[\s\n]*[）)]?/g, '')
      .replace(/[\s\n]*[（(][\s\n]*截止[日期]?[：:]\s*\S*[\s\n]*[）)]?/g, '')
      .replace(/[\s\n]*(预计)?截止[日期]?[：:]\s*\S+/g, '')
      .replace(/[\s\n]*DDL[：:]\s*\S+/gi, '')
      .replace(/\s+/g, ' ')
      .trim();
    return stripped || text;
  }

  // 从文本行推断承诺方
  function _guessParty(lineText, fullText) {
    var t = (lineText || '') + ' ' + (fullText || '');
    var tLower = t.toLowerCase();
    for (var i = 0; i < BD_PARTY_KEYS.length; i++) {
      if (tLower.indexOf(BD_PARTY_KEYS[i].toLowerCase()) !== -1) return 'bd';
    }
    for (var j = 0; j < BRAND_PARTY_KEYS.length; j++) {
      if (tLower.indexOf(BRAND_PARTY_KEYS[j].toLowerCase()) !== -1) return 'brand';
    }
    return 'brand'; // 默认为品牌方承诺
  }

  // 从文本行提取承诺内容描述
  function _extractContent(lineText, fullText) {
    var t = (lineText || '').toLowerCase();
    var matched = [];
    for (var i = 0; i < COMMIT_KEYWORDS.length; i++) {
      var tpl = COMMIT_KEYWORDS[i];
      for (var j = 0; j < tpl.keys.length; j++) {
        if (t.indexOf(tpl.keys[j]) !== -1) {
          matched.push(tpl.content);
          break;
        }
      }
    }
    if (matched.length > 0) return matched[0]; // 取第一个匹配

    // 没匹配到则用原行文本(去前缀、去日期后截断)
    var clean = (lineText || '').replace(/^[-•·]\s*/, '').replace(/【.*?】/g, '').trim();
    clean = _stripDateInfo(clean);
    return clean.substring(0, 40) || '跟进待确认事项';
  }

  /**
   * M5 新版：只抽取承诺，不抽取待办
   * @param {string} topics - 会谈议题
   * @param {string} commitmentsText - 承诺事项
   * @param {string} undoneText - 未达成
   * @param {string} brandName - 品牌名
   * @returns {{ commitments: Array, source: string, warning: string|null }}
   */
  function mockExtractCommitments(topics, commitmentsText, undoneText, brandName) {
    // 拼接全部输入
    var fullText = [topics, commitmentsText, undoneText].filter(function(s) { return s && s.trim(); }).join('\n');

    if (!fullText || !fullText.trim()) {
      return { commitments: [], source: 'rule', warning: null };
    }

    var warning = null;
    if (fullText.length > MAX_AI_INPUT_CHARS) {
      warning = '输入超过' + MAX_AI_INPUT_CHARS + '字符，已截断处理；完整内容仍会保存';
      fullText = fullText.substring(0, MAX_AI_INPUT_CHARS);
    }

    var matched = [];
    var seenContent = {};

    // 1) 从承诺事项中的每行提取（优先级最高）
    if (commitmentsText && commitmentsText.trim()) {
      var commitLines = commitmentsText.split('\n').filter(function(l) { var t2 = l.trim(); return t2.startsWith('-') || t2.startsWith('•') || t2.startsWith('·') || t2.length > 5; });
      commitLines.forEach(function(line) {
        var content = _extractContent(line, fullText);
        if (seenContent[content]) return;
        seenContent[content] = true;
        var explicitDeadline = _tryExtractDeadline(line) || _tryExtractDeadline(fullText);
        var suggested = _offsetDate(7);
        matched.push({
          content: content + (brandName ? '（' + brandName + '）' : ''),
          party: _guessParty(line, fullText),
          deadline: explicitDeadline || null,
          suggestedDeadline: explicitDeadline ? null : suggested,
          deadlineNeedUserFill: !explicitDeadline,
        });
      });
    }

    // 2) 从会谈议题中关键词补抽（去重）
    if (topics && topics.trim()) {
      var topicContent = _extractContent(topics, fullText);
      if (topicContent && !seenContent[topicContent]) {
        seenContent[topicContent] = true;
        var explicitD2 = _tryExtractDeadline(topics) || _tryExtractDeadline(fullText);
        var suggested2 = _offsetDate(7);
        matched.push({
          content: topicContent + (brandName ? '（' + brandName + '）' : ''),
          party: _guessParty(topics, fullText),
          deadline: explicitD2 || null,
          suggestedDeadline: explicitD2 ? null : suggested2,
          deadlineNeedUserFill: !explicitD2,
        });
      }
    }

    // 3) 从未达成中抽提
    if (undoneText && undoneText.trim()) {
      var undoContent = _extractContent(undoneText, fullText);
      if (undoContent && !seenContent[undoContent]) {
        seenContent[undoContent] = true;
        var explicitD3 = _tryExtractDeadline(undoneText) || _tryExtractDeadline(fullText);
        var suggested3 = _offsetDate(7);
        matched.push({
          content: undoContent + '（需跟进）' + (brandName ? '（' + brandName + '）' : ''),
          party: _guessParty(undoneText, fullText),
          deadline: explicitD3 || null,
          suggestedDeadline: explicitD3 ? null : suggested3,
          deadlineNeedUserFill: !explicitD3,
        });
      }
    }

    // 4) 如果什么都没抽到，从全文生成一条兜底
    if (!matched.length) {
      var fallbackContent = (commitmentsText || topics || '').replace(/^[-•·]\s*/gm, '').trim().substring(0, 40) || '跟进会谈要点';
      var fallbackExplicit = _tryExtractDeadline(fullText);
      var fallbackSuggested = _offsetDate(7);
      matched.push({
        content: fallbackContent + (brandName ? '（' + brandName + '）' : ''),
        party: _guessParty(fullText, ''),
        deadline: fallbackExplicit || null,
        suggestedDeadline: fallbackExplicit ? null : fallbackSuggested,
        deadlineNeedUserFill: !fallbackExplicit,
      });
    }

    return {
      commitments: matched.slice(0, 8), // 最多8条
      source: 'rule',
      warning: warning || null,
    };
  }

  // 兼容旧接口：只返回 commitments，todos 永远为空
  function mockExtractTodos(text, brandName) {
    return {
      todos: [],
      commitments: mockExtractCommitments('', text, '', brandName).commitments,
      source: 'rule',
      warning: null,
    };
  }

  function mockReminderSummary(reminderData) {
    if (!reminderData) return null;
    var parts = [];
    if (reminderData.dw_period_hint) parts.push('经营数据已更新至 ' + reminderData.dw_period_hint);
    var brokenCount = (reminderData.broken_commitments || []).length;
    if (brokenCount > 0) parts.push(brokenCount + '项承诺已逾期未兑现');
    var p0Count = (reminderData.p0_alerts || []).length;
    if (p0Count > 0) {
      var riskAlerts = reminderData.p0_alerts.filter(function (a) { return a.category === '风险预警'; });
      var growthAlerts = reminderData.p0_alerts.filter(function (a) { return a.category !== '风险预警'; });
      if (riskAlerts.length) parts.push(riskAlerts.length + '条风险预警需关注');
      if (growthAlerts.length) parts.push(growthAlerts.length + '条增长机会');
    }
    var daysSince = reminderData.days_since_last_visit;
    if (daysSince && daysSince > 30) parts.push('距上次拜访已' + daysSince + '天，建议尽快安排');
    else if (daysSince && daysSince <= 30) parts.push('上次拜访' + daysSince + '天前，节奏正常');
    if (reminderData.relation_temp != null && reminderData.relation_temp < 50) parts.push('关系温度偏低（' + reminderData.relation_temp + '°），建议加强沟通');
    if (!parts.length) parts.push('当前状态正常，按计划推进即可');
    return '🤖 AI：' + parts.join('；') + '。';
  }

  function authHeaders() {
    if (global.SandAuth && global.SandAuth.authHeaders) return global.SandAuth.authHeaders();
    return { 'Content-Type': 'application/json' };
  }

  function apiBase() {
    return global.M1_API_BASE != null ? global.M1_API_BASE : '';
  }

  function normalizeApiExtract(data) {
    var commitments = (data.commitments || []).map(function (c) {
      return {
        content: c.content || c.title || '',
        party: c.party || 'brand',
        deadline: c.deadline || null,
        suggestedDeadline: c.suggestedDeadline || null,
        deadlineNeedUserFill: !c.deadline,
      };
    });
    return { todos: [], commitments: commitments, source: data.source };
  }

  function extractFromSavedRecord(recordId) {
    var url = apiBase() + '/api/records/' + recordId + '/ai/extract';
    return fetch(url, { method: 'POST', headers: authHeaders() })
      .then(function (r) {
        return r.json().then(function (data) {
          if (!r.ok) throw new Error(data.detail || 'AI 抽取失败');
          return normalizeApiExtract(data);
        });
      })
      .catch(function (err) {
        console.warn('[sandtable] 后端 AI 抽取失败，降级 mock:', err);
        return null;
      });
  }

  /**
   * M5 新版：从 议题+承诺+未达成 综合抽取承诺
   */
  function extractCommitmentsFromTopics(topics, commitmentsRaw, undoneItems, brandName) {
    var t = [topics, commitmentsRaw, undoneItems].filter(function(s) { return s && s.trim(); }).join('\n');
    if (t.length > MAX_MINUTES_CHARS) t = t.substring(0, MAX_MINUTES_CHARS);
    var self = this; // unused but kept for closure
    return new Promise(function (resolve) {
      setTimeout(function () {
        resolve(mockExtractCommitments(topics, commitmentsRaw, undoneItems, brandName));
      }, 200);
    });
  }

  // 兼容旧调用
  function extractTodosFromMinutes(text, brandName) {
    return extractCommitmentsFromTopics('', text, '', brandName);
  }

  function getReminderSummary(reminderData) {
    return new Promise(function (resolve) {
      if (!M3.isLLMEnabled() || !M3.isRouteEnabled('reminder_llm')) { resolve(null); return; }
      setTimeout(function () { resolve(mockReminderSummary(reminderData)); }, 400);
    });
  }

  function requiresConfirmation() { return true; }

  global.M3LLM = {
    extractTodosFromMinutes: extractTodosFromMinutes,
    extractCommitmentsFromTopics: extractCommitmentsFromTopics,
    extractFromSavedRecord: extractFromSavedRecord,
    getReminderSummary: getReminderSummary,
    mockExtractTodos: mockExtractTodos,
    mockExtractCommitments: mockExtractCommitments,
    mockReminderSummary: mockReminderSummary,
    requiresConfirmation: requiresConfirmation,
    MAX_MINUTES_CHARS: MAX_MINUTES_CHARS,
    MAX_AI_INPUT_CHARS: MAX_AI_INPUT_CHARS,
  };

  function _offsetDate(days) {
    var d = new Date();
    d.setDate(d.getDate() + days);
    return d.toISOString().split('T')[0];
  }
})(window);
