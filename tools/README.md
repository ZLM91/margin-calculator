# 文案品类维护工具

给 margin-calculator 加 TikTok 文案品类时，用这套工具代替手工改四处易漏的地方。

## 为什么需要它

只往 `tiktok_titles_*.md` 里加文案是不够的。`index.html` 里还有三处没同步的话：

| 漏了哪处 | 后果 |
|---|---|
| `catKey()` 归一化分支 | 新品类在分类去重时无法识别 |
| 图标 emoji 映射 | 分类标签显示成通用的 📌 |
| 轮播说明文案 | 页面提示与实际内容对不上 |

最典型的翻车是新品类掉进「📌 其他」，用户在网站上看不到，还以为没加上。

## 怎么用（双击方式）

1. 把 `new_category.example.json` 复制成 `new_category.json`，按里面注释填写
2. 把三批文案分别写进 txt（格式见 `example_titles_batch1.txt`）
3. 双击 **`1_新增文案品类.cmd`** —— 会先预览改动，输入 `y` 才真正写入
4. 完成后按提示自己执行 git diff / commit / push

> 工具不会自动推送。推送前务必先 `git fetch` 确认远端有没有别人新推的提交。

## 怎么用（命令行）

```bash
# 预览（不写文件）
python tools/add_copy_category.py --config tools/new_category.json --dry-run

# 正式执行（含自动校验）
python tools/add_copy_category.py --config tools/new_category.json

# 单独校验某个品类
node tools/verify_copy.js --repo . --key babywipes --expect 18
```

## 校验器检查什么

- 每个批次文件的目标品类条数是否与预期一致
- 子类目标签页是否生成了对应 `data-cat` 分支（即没掉进「其他」）
- 每条文案：中英双语完整、英文尾部带标签、中文带标签、英文没混中文
- 合规红线：第一人称、功效/医疗动词（heal/treat/prevent/hypoallergenic 等）、
  未确认成分或虚假定量（芦荟/维E/益生菌/99% 等）
- 三批之间有无重复文案

## 已有品类对照表

| key | 品类 |
|---|---|
| `wetwipes` | 湿厕纸 |
| `travel` | 旅行装湿厕纸 |
| `facial` | 一次性洗脸巾 |
| `babywipes` | 纯水婴儿湿巾 |
| `toothpaste` | 牙膏 |
| `mudmask` | 控油清洁泥膜 |
| `cleanser` | 洁面啫喱 |
| `pet` | 宠物清洁手套 |

新增 `key` 时不要与上面重复。

## 已知注意事项

- Windows 控制台是 GBK，脚本输出的 emoji 会显示成 `?`，**不影响写入文件的正确性**
- md 文件的换行符不统一（`tiktok_titles_1.md` 是 CRLF，2/3 是 LF），
  脚本会读取原文件行尾并保持一致，避免整份文件在 diff 里被判为改动
- 文案源文件里以 `;` 或 `#` 开头的行会被当作注释跳过
