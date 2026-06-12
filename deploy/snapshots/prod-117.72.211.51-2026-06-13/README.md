# 生产快照 · 117.72.211.51 · 2026-06-13

从外网 **当时正在服务** 的静态页抓下来的副本，用于本地对比与紧急回滚。

| 字段 | 值 |
|------|-----|
| 服务器 | 117.72.211.51 |
| 抓取时间 | 2026-06-13 |
| 路径（云上） | `/opt/sandtable/web/` |
| 抓取方式 | `curl http://117.72.211.51/...`（无需 SSH） |

## 这一版有什么

- `index.html`：工作台待办已接 `/api/todos`（动态加载 + 勾选同步），**尚无**副标题「品牌：」字段
- `visit.html` / `profile.html` / `intel.html` / `js/shell.js`：与当时线上一致

## 与本地 git 的关系

| 版本 | 说明 |
|------|------|
| `git HEAD`（commit `c0404dd`） | 待办仍是 **4 条静态 HTML**，与**当前线上不同** |
| 本目录 | **线上真实在跑的前端**（应用作回滚基准） |
| 本地未提交改动 | 在 HEAD 基础上又改了待办 API、品牌字段等 |

## 回滚到这一版（仅前端）

在本机项目根目录执行（会提示输入 root 密码）：

```bash
bash deploy/snapshots/prod-117.72.211.51-2026-06-13/rollback-web.sh 117.72.211.51
```

或手动：

```bash
scp deploy/snapshots/prod-117.72.211.51-2026-06-13/web/index.html \
    root@117.72.211.51:/opt/sandtable/web/index.html
# 其他页面按需 scp
```

回滚后浏览器 **Cmd+Shift+R** 硬刷新。

## 更新快照

下次上线前建议再抓一份，命名：`prod-117.72.211.51-YYYYMMDD/`。

```bash
bash deploy/snapshot-from-cloud.sh 117.72.211.51
```
