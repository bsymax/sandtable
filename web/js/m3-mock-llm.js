/**
 * 品牌沙盘 M4 · 纪要/提醒 LLM 前端（培翛 · M4 增强版）
 *
 * M4 变更:
 * - 纪要 LLM 边界加固：截断/JSON 失败降级
 * - 确认后才落库：AI 抽取结果展示后，用户须确认再提交
 * - LLM 失败自动降级规则版，不算 bug
 */
(function (global) {
  'use strict';

  var M3 = global.M3;

  var MAX_MINUTES_CHARS = 3000;
  var MAX_AI_INPUT_CHARS = 2400;

  var TODO_TEMPLATES = [
    { keys: ['投放', '预算', '联合投放', '广告'],     priority: 'P0', title: '跟进联合投放方案确认',       assignee: '采销' },
    { keys: ['新品', '首发', '排期', '上市'],         priority: 'P0', title: '跟进新品排期确认',           assignee: '采销' },
    { keys: ['价', '包销', '专供', '折扣', '降价'],   priority: 'P0', title: '跟进价格/包销方案确认',     assignee: '采销' },
    { keys: ['库存', '备货', '供应链', '断货'],       priority: 'P1', title: '跟进库存/供应链协调',       assignee: '采销' },
    { keys: ['618', '双11', '大促', '活动', '促销'],  priority: 'P1', title: '跟进大促活动方案对齐',       assignee: '采销' },
    { keys: ['人员', '变动', '岗位', '换人', '调整'],  priority: 'P1', title: '确认对方人员变动情况',       assignee: '采销' },
    { keys: ['续约', '框架', '年度', '合同'],         priority: 'P1', title: '跟进年度框架/续约准备',     assignee: '采销' },
    { keys: ['客诉', '品质', '质量', '售后'],         priority: 'P0', title: '跟进客诉/品质问题处理',     assignee: '采销' },
    { keys: ['数据', '报表', '份额', '占比'],         priority: 'P2', title: '整理品牌经营数据',           assignee: '采销' },
    { keys: ['下次', '后续', '跟进'],                 priority: 'P2', title: '下次拜访准备',               assignee: '采销' },
  ];

  var COMMITMENT_TEMPLATES = [
    { keys: ['投放', '预算', '联合投放'], party: 'brand', content: '联合投放预算确认' },
    { keys: ['新品', '首发', '排期'],     party: 'brand', content: '新品首发排期确认' },
    { keys: ['降价', '折扣', '价'],       party: 'brand', content: '价格方案确认' },
    { keys: ['库存', '备货'],             party: 'brand', content: '库存保障承诺' },
    { keys: ['资源', '置换', '广告'],     party: 'brand', content: '广告资源置换确认' },
    { keys: ['数据', '报表'],             party: 'brand', content: '经营数据同步' },
    { keys: ['售后', '品质', '质量'],     party: 'brand', content: '售后/品质保障承诺' },
  ];

  function _truncateMinutes(text) {
    if (!text) return '';
    if (text.length <= MAX_AI_INPUT_CHARS) return text;
    return text.substring(0, MAX_AI_INPUT_CHARS) + '\n…[纪要内容较长，已截断至' + MAX_AI_INPUT_CHARS + '字符]';
  }

  function mockExtractTodos(text, brandName) {
    if (!text || !text.trim()) {
      return { todos: [], commitments: [], source: 'rule', warning: null };
    }

    var truncated = _truncateMinutes(text);
    var useText = truncated;
    var warning = null;
    if (text.length > MAX_AI_INPUT_CHARS) {
      warning = '纪要超过' + MAX_AI_INPUT_CHARS + '字符，已截断处理；完整内容仍会保存到数据库';
    }

    var lower = useText.toLowerCase();
    var matchedTodos = [];
    var matchedCommits = [];

    TODO_TEMPLATES.forEach(function (tpl) {
      var hit = false;
      for (var i = 0; i < tpl.keys.length; i++) {
        if (lower.indexOf(tpl.keys[i]) !== -1) {
          hit = true;
          break;
        }
      }
      if (hit) {
        var already = matchedTodos.some(function (m) { return m.title === tpl.title; });
        if (!already) {
          var deadline = new Date();
          var offsetDays = tpl.priority === 'P0' ? 3 : (tpl.priority === 'P1' ? 7 : 14);
          deadline.setDate(deadline.getDate() + offsetDays);
          matchedTodos.push({
            priority: tpl.priority,
            title: tpl.title + (brandName ? '（' + brandName + '）' : ''),
            deadline: deadline.toISOString().split('T')[0],
            assignee: tpl.assignee,
          });
        }
      }
    });

    COMMITMENT_TEMPLATES.forEach(function (tpl) {
      var hit = false;
      for (var i = 0; i < tpl.keys.length; i++) {
        if (lower.indexOf(tpl.keys[i]) !== -1) {
          hit = true;
          break;
        }
      }
      if (hit) {
        var already = matchedCommits.some(function (m) { return m.content === tpl.content; });
        if (!already) {
          matchedCommits.push({ content: tpl.content, party: tpl.party });
        }
      }
    });

    if (!matchedTodos.length) {
      matchedTodos.push(
        { priority: 'P0', title: '跟进会谈要点', deadline: _offsetDate(3),  assignee: '采销' },
        { priority: 'P1', title: '确认后续行动计划', deadline: _offsetDate(7),  assignee: '采销' },
        { priority: 'P2', title: '下次拜访准备',     deadline: _offsetDate(12), assignee: '采销' }
      );
    }

    if (!matchedCommits.length && text.trim()) {
      var lines = text.split('\n').filter(function (l) {
        var trimmed = l.trim();
        return trimmed.startsWith('-') || trimmed.startsWith('•') || trimmed.startsWith('·');
      });
      if (lines.length) {
        matchedCommits = lines.slice(0, 5).map(function (l) {
          return {
            content: l.replace(/^[-•·]\s*/, '').replace(/【.*】/, '').trim().substring(0, 40),
            party: 'brand',
          };
        });
      }
    }

    return {
      todos: matchedTodos.slice(0, 6),
      commitments: matchedCommits.slice(0, 5),
      source: 'rule',
      warning: warning || null,
    };
  }

  function mockReminderSummary(reminderData) {
    if (!reminderData) return null;

    var parts = [];

    if (reminderData.dw_period_hint) {
      parts.push('经营数据已更新至 ' + reminderData.dw_period_hint);
    }

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
    if (daysSince && daysSince > 30) {
      parts.push('距上次拜访已' + daysSince + '天，建议尽快安排');
    } else if (daysSince && daysSince <= 30) {
      parts.push('上次拜访' + daysSince + '天前，节奏正常');
    }

    if (reminderData.relation_temp != null && reminderData.relation_temp < 50) {
      parts.push('关系温度偏低（' + reminderData.relation_temp + '°），建议加强沟通');
    }

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
    var todos = (data.todos || []).map(function (t) {
      return {
        priority: t.priority || 'P2',
        title: t.title || t.content || '',
        deadline: t.deadline || null,
        assignee: t.assignee || '采销',
      };
    });
    var commitments = (data.commitments || []).map(function (c) {
      return {
        content: c.content || c.title || '',
        party: c.party || 'brand',
      };
    });
    return { todos: todos, commitments: commitments, source: data.source };
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
        console.warn('[M3] 后端 AI 抽取失败，降级 mock:', err);
        return null;
      });
  }

  function extractTodosFromMinutes(text, brandName) {
    if (text && text.length > MAX_MINUTES_CHARS) {
      text = text.substring(0, MAX_MINUTES_CHARS);
    }
    return new Promise(function (resolve) {
      if (!M3.isLLMEnabled() || !M3.isRouteEnabled('record_extract')) {
        setTimeout(function () {
          resolve(mockExtractTodos(text, brandName));
        }, 200);
        return;
      }
      setTimeout(function () {
        resolve(mockExtractTodos(text, brandName));
      }, 200);
    });
  }

  function getReminderSummary(reminderData) {
    return new Promise(function (resolve) {
      if (!M3.isLLMEnabled() || !M3.isRouteEnabled('reminder_llm')) {
        resolve(null);
        return;
      }
      setTimeout(function () {
        resolve(mockReminderSummary(reminderData));
      }, 400);
    });
  }

  function requiresConfirmation() {
    return true;
  }

  global.M3LLM = {
    extractTodosFromMinutes: extractTodosFromMinutes,
    extractFromSavedRecord: extractFromSavedRecord,
    getReminderSummary: getReminderSummary,
    mockExtractTodos: mockExtractTodos,
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
