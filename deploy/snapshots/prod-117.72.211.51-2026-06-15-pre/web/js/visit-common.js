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

  function buildReminderHTML(d) {
    if (!d) return '<p style="color:var(--text-muted);">暂无提醒数据</p>';
    var html = '';
    var daysSince = d.days_since_last_visit;

    if (d.last_visit_date) {
      html += '<div class="visit-alert-banner"><span style="font-size:18px;">📋</span><div>';
      html += '<b style="color:var(--text);">最近拜访：</b>' + formatDate(d.last_visit_date) + '（' + daysSince + '天前）';
      if (d.last_visit_purpose) html += ' · ' + d.last_visit_purpose;
      html += '</div></div>';
    } else {
      html += '<div class="visit-alert-banner"><span style="font-size:18px;">🚨</span><div><b style="color:var(--text);">无拜访记录</b></div></div>';
    }

    if (d.pending_commitments && d.pending_commitments.length > 0) {
      html += '<p><b style="color:var(--text);">未兑现承诺：</b>';
      d.pending_commitments.forEach(function(c) {
        html += '<span class="tag tag-red" style="margin-right:4px;margin-bottom:4px;">' + c.content + '</span>';
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
      return '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">' +
        (emptyMsg || '暂无记录') + '</td></tr>';
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
    var colSpan = showBrand ? 6 : 5;
    if (!commitments.length) {
      return '<tr><td colspan="' + colSpan + '" style="text-align:center;color:var(--text-muted);">' +
        (options.emptyMsg || '暂无承诺（保存拜访记录后按行自动生成）') + '</td></tr>';
    }
    return commitments.map(function(c) {
      var visit = visitMap[c.visit_id] || {};
      return '<tr>' +
        (showBrand ? '<td>' + (visit.brand_name || '—') + '</td>' : '') +
        '<td>' + truncate(c.content, 40) + '</td>' +
        '<td>' + (c.party === 'bd' ? '我方' : '品牌方') + '</td>' +
        '<td>' + commitmentStatusTag(c.status) + '</td>' +
        '<td>' + formatDate(c.deadline) + '</td>' +
        '<td><select class="form-select" style="width:110px;padding:4px 8px;font-size:12px;" onchange="' +
          onStatusChange + '(' + c.id + ', this.value)">' +
          '<option value="pending"' + (c.status === 'pending' ? ' selected' : '') + '>待兑现</option>' +
          '<option value="fulfilled"' + (c.status === 'fulfilled' ? ' selected' : '') + '>已兑现</option>' +
          '<option value="broken"' + (c.status === 'broken' ? ' selected' : '') + '>未兑现</option>' +
        '</select></td></tr>';
    }).join('');
  }

  function renderVisitsCalendar(visits, options) {
    options = options || {};
    var onScheduled = options.onScheduledClick || 'fillRecordForm';
    if (!visits.length) {
      return '<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">' +
        (options.emptyMsg || '暂无数据') + '</td></tr>';
    }
    return visits.map(function(v) {
      var actionCell;
      if (options.linkToVisit) {
        actionCell = '<td><button class="btn-sm-outline" onclick="window.location.href=\'visit.html?brand=' +
          (options.brandKey || '') + '\'">' +
          (v.status === 'scheduled' ? '记录' : '查看') + '</button></td>';
      } else {
        actionCell = '<td><button class="btn-sm-outline" onclick="' +
          (v.status === 'scheduled'
            ? onScheduled + '(' + v.id + ')'
            : 'window.alert(\'详情（演示）\')') +
          '">' + (v.status === 'scheduled' ? '记录' : '查看') + '</button></td>';
      }
      return '<tr>' +
        '<td>' + formatDate(v.visit_date) + '</td>' +
        '<td>' + (v.brand_name || '') + '</td>' +
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
  };
})(window);
