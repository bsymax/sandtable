/**
 * 拜访模块 · 档案 Tab4 共用展示逻辑（与 visit.html 一致）
 */
(function(global) {
  function formatDate(d) {
    return d ? String(d).replace(/^\d{4}-/, '').replace('-', '/') : '—';
  }

  function truncate(s, n) {
    if (!s) return '—';
    return s.length > n ? s.substring(0, n) + '...' : s;
  }

  function levelBadge(l) {
    if (!l) return '';
    var cls = 'level-' + String(l).toLowerCase();
    return '<span class="level-badge ' + cls + '">' + l + '</span>';
  }

  function typeTag(t) {
    var m = { urgent: ['tag-red', '紧急'], regular: ['tag-blue', '定期'], renewal: ['tag-amber', '续约'] };
    var v = m[t] || ['tag-gray', t || '—'];
    return '<span class="tag ' + v[0] + '">' + v[1] + '</span>';
  }

  function statusTag(s) {
    var m = { scheduled: ['tag-blue', '待拜访'], completed: ['tag-green', '已完成'], cancelled: ['tag-gray', '已取消'] };
    var v = m[s] || ['tag-gray', s];
    return '<span class="tag ' + v[0] + '">' + v[1] + '</span>';
  }

  function tempIcon(c) {
    var m = { up: '🔥 升温', flat: '➡️ 持平', down: '❄️ 降温' };
    return m[c] || '—';
  }

  function commitmentStatusTag(s) {
    var m = {
      pending: ['tag-amber', '待兑现'],
      fulfilled: ['tag-green', '已兑现'],
      broken: ['tag-red', '未兑现'],
    };
    var v = m[s] || ['tag-gray', s || '—'];
    return '<span class="tag ' + v[0] + '">' + v[1] + '</span>';
  }

  function _todayISO() {
    var d = new Date(), m = d.getMonth() + 1, day = d.getDate();
    return d.getFullYear() + '-' + (m < 10 ? '0' : '') + m + '-' + (day < 10 ? '0' : '') + day;
  }

  // 截止日期已过且仍「待兑现」→ 系统自动判定为「未兑现」（用户可在下拉手动调整覆盖）
  function isCommitmentOverdue(c) {
    if (!c || c.status !== 'pending' || !c.deadline) return false;
    return String(c.deadline).slice(0, 10) < _todayISO();
  }

  function effectiveCommitmentStatus(c) {
    return isCommitmentOverdue(c) ? 'broken' : c.status;
  }

  function buildReminderHTML(d) {
    if (!d) return '<p style="color:var(--text-muted);">暂无提醒数据</p>';
    var html = '';

    if (d.dw_period_hint) {
      html += '<div class="visit-alert-banner" style="background:linear-gradient(90deg,#e8f5ef,#fff);border-color:#86efac;">' +
        '<span style="font-size:18px;">📊</span><div>' +
        '<b style="color:var(--green-500);">经营数据已更新至 ' + d.dw_period_hint + '</b>' +
        '</div></div>';
    }

    var daysSince = d.days_since_last_visit;

    // 最近拜访
    if (d.last_visit_date) {
      html += '<div class="visit-alert-banner"><span style="font-size:18px;">📋</span><div>';
      html += '<b style="color:var(--text);">最近拜访：</b>' + formatDate(d.last_visit_date) + '（' + daysSince + '天前）';
      if (d.last_visit_purpose) html += ' · ' + d.last_visit_purpose;
      html += '</div></div>';
    } else {
      html += '<div class="visit-alert-banner"><span style="font-size:18px;">🚨</span><div><b style="color:var(--text);">无拜访记录</b></div></div>';
    }

    // M2: P0 情报预警
    if (d.p0_alerts && d.p0_alerts.length > 0) {
      html += '<div class="visit-alert-banner" style="background:linear-gradient(135deg,#fdecea,#fff);border-color:#fca5a5;"><span style="font-size:18px;">⚠️</span><div>';
      html += '<b style="color:var(--red-500);">来自情报流 P0 预警：</b>';
      d.p0_alerts.forEach(function(a) {
        var catTag = a.category === '风险预警' ?
          '<span class="tag tag-red" style="margin:0 4px 2px 0;">风险</span>' :
          '<span class="tag tag-amber" style="margin:0 4px 2px 0;">增长</span>';
        html += '<div style="margin-top:4px;">' + catTag + ' ' + truncate(a.title, 40) + '</div>';
      });
      html += '</div></div>';
    }

    // M2: 周报简报
    if (d.latest_weekly) {
      var w = d.latest_weekly;
      if (w.risk_points || w.opportunities) {
        html += '<div class="visit-alert-banner"><span style="font-size:18px;">📊</span><div>';
        html += '<b style="color:var(--text);">近期周报简报：</b>';
        if (w.risk_points) html += '<div style="margin-top:2px;color:var(--red-500);">⚠ 风险：' + truncate(w.risk_points, 40) + '</div>';
        if (w.opportunities) html += '<div style="margin-top:2px;color:var(--green-500);">💡 机会：' + truncate(w.opportunities, 40) + '</div>';
        html += '</div></div>';
      }
    }

    // 未兑现承诺（broken）
    if (d.broken_commitments && d.broken_commitments.length > 0) {
      html += '<p style="margin-top:8px;"><b style="color:var(--red-500);">❌ 已broken承诺：</b>';
      d.broken_commitments.forEach(function(c) {
        html += '<span class="tag tag-red" style="margin-right:4px;margin-bottom:4px;">' + c.content + '</span>';
      });
      html += '</p>';
    }

    // 待兑现承诺（pending）
    if (d.pending_commitments && d.pending_commitments.length > 0) {
      html += '<p><b style="color:var(--text);">待兑现承诺：</b>';
      d.pending_commitments.forEach(function(c) {
        html += '<span class="tag tag-amber" style="margin-right:4px;margin-bottom:4px;">' + c.content + '</span>';
      });
      html += '</p>';
    }

    if (d.stale_contacts && d.stale_contacts.length > 0) {
      html += '<p style="margin-top:8px;"><b style="color:var(--text);">超期未建联：</b>';
      d.stale_contacts.forEach(function(c) {
        html += c.name + '（' + c.days_since + '天） ';
      });
      html += '</p>';
    }

    html += '<p style="margin-top:8px;"><b style="color:var(--text);">关系温度：</b>' +
      (d.relation_temp != null ? d.relation_temp : '—') + '° · 档案完整度：' +
      (d.archive_score != null ? d.archive_score : '—') + '分</p>';

    return html;
  }

  function renderRecordsTable(records, emptyMsg) {
    if (!records.length) {
      var msg = emptyMsg || '<div style="font-size:28px;margin-bottom:6px;">📋</div><div>暂无拜访记录</div><div style="font-size:11px;margin-top:4px;color:var(--text-muted);">完成拜访并保存后显示</div>';
      return '<tr><td colspan="6" style="text-align:center;padding:28px 16px;color:var(--text-muted);">' + msg + '</td></tr>';
    }
    return records.map(function(r) {
      return '<tr>' +
        '<td>' + formatDate(r.visit_date) + '</td>' +
        '<td>' + (r.brand_name || '') + '</td>' +
        '<td>' + levelBadge(r.brand_level) + '</td>' +
        '<td>' + typeTag(r.visit_type) + '</td>' +
        '<td>' + truncate(r.topics || r.commitments_raw, 25) + '</td>' +
        '<td>' + tempIcon(r.relation_change) + '</td>' +
        '</tr>';
    }).join('');
  }

  function renderCommitmentsTable(commitments, visitMap, options) {
    options = options || {};
    var showBrand = options.showBrand !== false;
    var onStatusChange = options.onStatusChange || 'updateCommitmentStatus';
    var colSpan = showBrand ? 6 : (options.readOnly ? 4 : 5);
    if (!commitments.length) {
      return '<tr><td colspan="' + colSpan + '" style="text-align:center;padding:28px 16px;color:var(--text-muted);">' +
        '<div style="font-size:28px;margin-bottom:6px;">✅</div>' +
        '<div style="font-size:13px;">' + (options.emptyMsg || '暂无承诺（保存拜访记录后按行自动生成）') + '</div>' +
        '</td></tr>';
    }
    return commitments.map(function(c) {
      var visit = visitMap[c.visit_id] || {};
      var eff = effectiveCommitmentStatus(c);
      var auto = (eff !== c.status);
      return '<tr>' +
        (showBrand ? '<td>' + (visit.brand_name || '—') + '</td>' : '') +
        '<td>' + truncate(c.content, 40) + '</td>' +
        '<td>' + (c.party === 'bd' ? '我方' : '品牌方') + '</td>' +
        '<td>' + commitmentStatusTag(eff) +
          (auto ? ' <span style="font-size:10px;color:var(--text-muted);" title="已过截止日期，系统自动判定为未兑现，可在右侧手动调整">·自动</span>' : '') + '</td>' +
        '<td>' + formatDate(c.deadline) + '</td>' +
        (options.readOnly ? '' :
          '<td><select class="form-select" style="width:110px;padding:4px 8px;font-size:12px;" onchange="' +
            onStatusChange + '(' + c.id + ', this.value)">' +
            '<option value="pending"' + (eff === 'pending' ? ' selected' : '') + '>待兑现</option>' +
            '<option value="fulfilled"' + (eff === 'fulfilled' ? ' selected' : '') + '>已兑现</option>' +
            '<option value="broken"' + (eff === 'broken' ? ' selected' : '') + '>未兑现</option>' +
          '</select></td>') +
        '</tr>';
    }).join('');
  }

  function renderVisitsCalendar(visits, options) {
    options = options || {};
    var onScheduled = options.onScheduledClick || 'fillRecordForm';
    var onCompleted = options.onCompletedClick || 'viewVisitRecord';
    var showBrand = options.showBrand !== false;
    var colSpan = options.colSpan != null ? options.colSpan : (showBrand ? 7 : 6);
    if (!visits.length) {
      return '<tr><td colspan="' + colSpan + '" style="text-align:center;padding:28px 16px;color:var(--text-muted);">' +
        '<div style="font-size:32px;margin-bottom:8px;">📅</div>' +
        '<div style="font-size:13px;">' + (options.emptyMsg || '暂无拜访数据') + '</div>' +
        (showBrand ? '<div style="font-size:12px;margin-top:4px;color:var(--text-muted);">安排拜访后显示</div>' : '') +
        '</td></tr>';
    }
    return visits.map(function(v) {
      var actionCell;
      if (options.linkToVisit) {
        var brandKey = options.brandKey || '';
        if (v.status === 'scheduled') {
          actionCell = '<td><button type="button" class="btn-sm-outline" onclick="window.location.href=\'visit.html?brand=' +
            brandKey + '&vtab=record&visit=' + v.id + '\'">记录</button></td>';
        } else {
          actionCell = '<td><button type="button" class="btn-sm-outline" onclick="window.location.href=\'visit.html?brand=' +
            brandKey + '&vtab=record&visit=' + v.id + '&mode=view\'">查看</button></td>';
        }
      } else {
        actionCell = '<td><button type="button" class="btn-sm-outline" onclick="' +
          (v.status === 'scheduled'
            ? onScheduled + '(' + v.id + ')'
            : onCompleted + '(' + v.id + ')') +
          '">' + (v.status === 'scheduled' ? '记录' : '查看') + '</button></td>';
      }
      return '<tr data-visit-id="' + v.id + '">' +
        '<td>' + formatDate(v.visit_date) + '</td>' +
        (showBrand ? '<td>' + (v.brand_name || '') + '</td>' : '') +
        '<td>' + levelBadge(v.brand_level) + '</td>' +
        '<td>' + typeTag(v.visit_type) + '</td>' +
        '<td>' + truncate(v.purpose, 20) + '</td>' +
        '<td>' + statusTag(v.status) + '</td>' +
        actionCell +
        '</tr>';
    }).join('');
  }

  function renderHealthRow(h) {
    if (!h) {
      return '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">暂无健康度数据</td></tr>';
    }
    var levelMap = { green: 'green', amber: 'amber', red: 'red' };
    var labelMap = { green: '✅ 达标', amber: '⚠️ 偏低', red: '❌ 严重偏低' };
    var cls = levelMap[h.status_level] || 'gray';
    var lbl = labelMap[h.status_level] || h.status_label;
    var nameStyle = h.status_level === 'red' ? 'style="color:var(--red-500);font-weight:600;"' : '';
    var countStyle = h.status_level === 'red' ? 'style="color:var(--red-500);font-weight:600;"' : '';
    return '<tr>' +
      '<td ' + nameStyle + '>' + h.brand_name + '</td>' +
      '<td>' + levelBadge(h.level) + '</td>' +
      '<td>' + h.baseline_freq + '</td>' +
      '<td ' + countStyle + '>' + h.visit_count_90d + '次</td>' +
      '<td><span class="tag tag-' + cls + '">' + lbl + '</span></td>' +
      '</tr>';
  }

  function visitMapFromList(visits) {
    var map = {};
    (visits || []).forEach(function(v) { map[v.id] = v; });
    return map;
  }

  function filterVisitsForBrand(visits, brandId) {
    if (brandId == null) return visits || [];
    return (visits || []).filter(function(v) {
      return v.brand_id == null || v.brand_id === brandId;
    });
  }

  function filterCommitmentsForBrand(commitments, visits) {
    var visitIds = {};
    (visits || []).forEach(function(v) {
      if (v && v.id != null) visitIds[v.id] = true;
    });
    return (commitments || []).filter(function(c) {
      return c.visit_id != null && visitIds[c.visit_id];
    });
  }

  global.VisitCommon = {
    formatDate: formatDate,
    truncate: truncate,
    levelBadge: levelBadge,
    typeTag: typeTag,
    statusTag: statusTag,
    tempIcon: tempIcon,
    commitmentStatusTag: commitmentStatusTag,
    buildReminderHTML: buildReminderHTML,
    renderRecordsTable: renderRecordsTable,
    renderCommitmentsTable: renderCommitmentsTable,
    renderVisitsCalendar: renderVisitsCalendar,
    renderHealthRow: renderHealthRow,
    visitMapFromList: visitMapFromList,
    filterVisitsForBrand: filterVisitsForBrand,
    filterCommitmentsForBrand: filterCommitmentsForBrand,
  };
})(window);
