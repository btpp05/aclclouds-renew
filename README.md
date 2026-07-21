# ACL Cloud Renew

自动续期 ACL Cloud 代理节点 — GitHub Actions 每天自动运行。

## Secrets 配置

| Secret | 说明 |
|--------|------|
| `GH_TOKEN` | GitHub PAT 用于 checkout 本仓库 |
| `ACL_COOKIE` | ACL Cloud 面板登录 Cookie |
| `TG_TOKEN` | Telegram Bot Token |
| `TG_USERID` | Telegram 通知 Chat ID |
| `KATA_LINK` | (可选) sing-box 代理链接，用于绕过 CF 盾 |