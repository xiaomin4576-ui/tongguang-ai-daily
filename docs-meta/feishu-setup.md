# 飞书机器人配置指南

> 这份指南教你从零搭建早报飞书通知。约 5 分钟完成。

---

## 整体流程

```
飞书群 → 添加自定义机器人 → 拿到 webhook URL
         ↓
GitHub repo → Settings → Secrets → 加 FEISHU_WEBHOOK
         ↓
.github/workflows/notify.yml 自动用这个 secret 发消息
```

---

## Step 1：在飞书群创建机器人

1. 打开飞书 → 进入或创建一个**专门接收早报的群**（建议命名"同光早报"）
2. 点群右上角 `···` → **设置** → **群机器人** → **添加机器人**
3. 选择 **自定义机器人**
4. 填写信息：
   - **机器人名称**：`同光早报 Bot`
   - **机器人描述**：每日 09:00 推送过去 24h 全球企业 AI 资讯
   - **头像**：可选,推荐用一个🤖或📰图标
5. 点 **下一步**
6. **复制 webhook 地址**（形如 `https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）

   ⚠️ **这个 URL 是密钥级敏感信息，不要发到公开渠道**

7. **安全设置**（强烈推荐）：勾选 **签名校验**，复制签名 secret

   注意：当前 `notify.yml` 工作流**未启用签名校验**（保持最简）。如果你启用了签名校验，需要修改 workflow 加签名计算逻辑——见本文末尾的"高级：签名校验"。

8. 点 **完成**

---

## Step 2：在 GitHub repo 配置 Secret

1. 打开你的 GitHub repo → **Settings**
2. 左侧菜单 → **Secrets and variables** → **Actions**
3. 点 **New repository secret**
4. 填写：
   - **Name**: `FEISHU_WEBHOOK`（**必须严格这个名字**，workflow 里用的）
   - **Secret**: 粘贴 Step 1 第 6 步复制的 webhook URL
5. 点 **Add secret**

完成后你会在 `Repository secrets` 列表里看到 `FEISHU_WEBHOOK` 条目（值会被遮蔽显示）。

---

## Step 3：测试一次

### 方法 A：手动触发 workflow（推荐）

1. 打开 GitHub repo → **Actions** 标签
2. 左侧选 **飞书早报通知**
3. 右上角 **Run workflow** → 选 `main` 分支 → **Run workflow**

如果 `reports/` 里还没有任何早报文件，workflow 会失败（找不到文件）。

### 方法 B：等 Routine 跑出第一份早报后自动触发

每次 Claude Code Routine commit `reports/YYYY-MM-DD.md` 到 main，notify.yml 都会自动触发。

---

## Step 4：验证消息收到

去你的飞书群看，应该收到这样一张卡片：

```
┌─────────────────────────────────────────┐
│ 📰 同光 · 企业 AI 早报              │
├─────────────────────────────────────────┤
│ 📅 日期             🏷 标签             │
│ 2026-05-13         [strong-signal]      │
│                                         │
│ 📊 主报告           🧠 Tier 0 深度参考   │
│ 32 篇              7 篇                 │
├─────────────────────────────────────────┤
│ 预览                                    │
│ 🕐 北京时间 2026-05-13 09:30           │
│ 📅 窗口:过去 24 小时...                │
├─────────────────────────────────────────┤
│ [📖 阅读完整早报]  [📚 历史目录]        │
└─────────────────────────────────────────┘
```

点 **阅读完整早报** 跳转 GitHub 看 markdown 全文。

---

## 🚨 常见问题

### Q1: 飞书没收到消息怎么办？

**先查 GitHub Actions 日志**：
1. Actions 标签 → 点最新一次失败的 workflow run
2. 看 `Send to Feishu webhook` 步骤的输出

常见错误：

| 错误信息 | 原因 | 修复 |
|---|---|---|
| `FEISHU_WEBHOOK secret 未配置,跳过通知` | Secret 没加或名字打错 | 重做 Step 2,Name 必须是 `FEISHU_WEBHOOK` |
| `{"code":9499,"msg":"sign verification failed"}` | 飞书开了签名校验但 workflow 没签名 | 在飞书机器人设置里关闭签名校验,或改造 workflow |
| `{"code":11220,"msg":"too many requests"}` | 飞书限流（同一 webhook 每分钟最多 100 条） | 等 1 分钟,正常运行不会撞 |
| `{"code":19024,"msg":"invalid webhook"}` | webhook URL 复制错了 | 重新去飞书复制完整 URL |
| `curl: (6) Could not resolve host` | GitHub Actions 网络异常 | 重试一次 |

### Q2: 想换一个飞书群怎么办？

1. 在新群里重做 Step 1 拿新 webhook
2. 去 GitHub Secrets 编辑 `FEISHU_WEBHOOK`,粘贴新 URL
3. 下次推送会自动发到新群（旧群不再收到）

### Q3: 想把卡片样式改成纯文本？

把 `notify.yml` 里的 `Build Feishu card payload` 步骤替换成：

```yaml
- name: Build Feishu text payload
  run: |
    cat > /tmp/payload.json << EOF
    {
      "msg_type": "text",
      "content": {
        "text": "📰 同光 ${{ steps.latest.outputs.date }} 早报已生成\\n${{ steps.latest.outputs.main_count }} 篇主报告\\n查看: ${{ steps.latest.outputs.url }}"
      }
    }
    EOF
```

### Q4: 想让通知@某个人？

在 payload 里加 mentions（飞书自定义机器人不支持 @，但可以在 content 里写 `<at id="open_id">` 兼容部分场景）。如果群里某人需要每日提醒，建议**让他自己设置群消息提醒**而不是用 @。

### Q5: 通知频率不对（应该 1 天 1 次，但有时收到 2 条）？

可能原因：
- Routine 跑了 2 次（手动触发 + 定时触发同时发生）
- 你 commit 了 `reports/` 下的非早报文件（比如 index.md 改动也会触发）

修复：workflow 已加 `paths: !reports/index.md` 排除目录文件，应该只在新早报推送时触发。如还有问题，看 workflow run 的 trigger 详情。

---

## 高级：签名校验

如果你的飞书机器人启用了签名校验（**推荐用于生产**），workflow 需要计算签名：

1. 在 GitHub Secrets 多加一个：`FEISHU_SIGN_SECRET`（飞书机器人页面给你的 secret）

2. 修改 `notify.yml` 的 `Send to Feishu webhook` 步骤：

```yaml
- name: Send to Feishu (with signature)
  env:
    FEISHU_WEBHOOK: ${{ secrets.FEISHU_WEBHOOK }}
    FEISHU_SIGN_SECRET: ${{ secrets.FEISHU_SIGN_SECRET }}
  run: |
    TIMESTAMP=$(date +%s)
    STRING_TO_SIGN="${TIMESTAMP}\n${FEISHU_SIGN_SECRET}"
    SIGN=$(echo -en "$STRING_TO_SIGN" | openssl dgst -sha256 -hmac "" -binary | base64)
    
    # 在 payload 里加 timestamp 和 sign 字段
    jq --arg ts "$TIMESTAMP" --arg sign "$SIGN" \
      '. + {timestamp: $ts, sign: $sign}' \
      /tmp/payload.json > /tmp/payload-signed.json
    
    curl -X POST "$FEISHU_WEBHOOK" \
      -H "Content-Type: application/json" \
      -d @/tmp/payload-signed.json
```

详细文档：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot

---

## 🔗 相关链接

- [飞书自定义机器人官方文档](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)
- [飞书消息卡片格式说明](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/im-v1/message-card/specifications/message-card-format)
- [GitHub Actions Secrets 管理](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
