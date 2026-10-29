/**
 * 通用文案解析校验器
 *
 * 用途：从 index.html 里切出真实的 parseAndRenderTiktok 函数，
 *       用 DOM stub 喂真实 md 文件跑一遍，确认新品类能被正确识别与渲染。
 *       这样不用打开浏览器就能发现「文案掉进 📌 其他」「条数不对」这类问题。
 *
 * 用法：
 *   node verify_copy.js --repo <仓库根目录> --key babywipes [--expect 18]
 */

const fs = require('fs');
const path = require('path');

function parseArgs(argv) {
  const o = { repo: null, key: null, expect: 0 };
  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === '--repo') o.repo = argv[++i];
    else if (argv[i] === '--key') o.key = argv[++i];
    else if (argv[i] === '--expect') o.expect = parseInt(argv[++i], 10);
  }
  return o;
}

const args = parseArgs(process.argv);
if (!args.repo || !args.key) {
  console.error('用法: node verify_copy.js --repo <仓库根目录> --key <品类key> [--expect <每批条数>]');
  process.exit(2);
}

const REPO = args.repo;
const KEY = args.key;
const EXPECT = args.expect || 0;

const html = fs.readFileSync(path.join(REPO, 'index.html'), 'utf8');

const fails = [];
function assert(cond, msg) { if (!cond) fails.push(msg); }

// ---- 静态检查：index.html 里必须同时具备三处改动 ----
assert(html.includes(`'${KEY}'`), `index.html 缺少 catKey 分支 '${KEY}'`);

// ---- 提取真实解析逻辑 ----
const start = html.indexOf('function parseAndRenderTiktok(mdText) {');
const end = html.indexOf('function copyTiktokTitle(');
if (start < 0 || end < 0) {
  console.error('[FAIL] 无法在 index.html 中定位 parseAndRenderTiktok');
  process.exit(1);
}
const snippet = html.slice(start, end);

const el = () => ({ textContent: '', style: {}, innerHTML: '' });
let renderedHTML = '', subTabsHTML = '';
global.document = {
  getElementById: (id) => {
    const o = el();
    if (id === 'tiktokCategories') Object.defineProperty(o, 'innerHTML', { set(v) { renderedHTML = v; }, get() { return renderedHTML; } });
    if (id === 'tiktokSubtabs') Object.defineProperty(o, 'innerHTML', { set(v) { subTabsHTML = v; }, get() { return subTabsHTML; } });
    return o;
  }
};
global.escapeHtml = (s) => String(s);
global.tiktokAllTitles = [];
eval(snippet);

// ---- 找出所有批次文件 ----
const batchFiles = fs.readdirSync(REPO)
  .filter(f => /^tiktok_titles_\d+\.md$/.test(f))
  .sort((a, b) => parseInt(a.match(/\d+/)[0], 10) - parseInt(b.match(/\d+/)[0], 10));

if (batchFiles.length === 0) {
  console.error('[FAIL] 未找到任何 tiktok_titles_N.md 批次文件');
  process.exit(1);
}

console.log(`仓库: ${REPO}`);
console.log(`校验品类 key: ${KEY}`);
console.log(`发现批次文件: ${batchFiles.join(', ')}\n`);

const allTitles = [];
const BANNED = [
  [/\b(I|I'm|I've|my|we|our)\b/i, '第一人称'],
  [/\b(heal|heals|cure|treat|treats|prevent|prevents|repair|therapy|antibacterial|hypoallergenic|dermatologist|pediatrician|eczema)\b/i, '功效/医疗宣称'],
  [/\b(99%|100%|zero\s?(%|percent)|aloe|vitamin\s?E|chamomile|cucumber|bamboo|probiotic)\b/i, '未确认成分/虚假定量'],
];
const CN_BANNED = /(我|我们|治|疗|预防|修复|抗菌|99%|100%|芦荟|维E|洋甘菊|黄瓜|竹纤维|益生菌)/;

for (const f of batchFiles) {
  const md = fs.readFileSync(path.join(REPO, f), 'utf8');
  parseAndRenderTiktok(md);          // 单批加载，模拟真实轮换
  const titles = global.tiktokAllTitles;

  // 用渲染出的 data-cat 反查本次目标品类对应的中文品类名
  const targetCats = new Set();
  let m, reCat = /data-cat="([^"]+)"/g;
  const sub = subTabsHTML;
  // 从字幕按钮中找 key 对应的品类名
  const reSub = /data-cat="([^"]+)"[^>]*>([^<]*)</g;
  let catName = null;
  while ((m = reSub.exec(sub))) {
    if (m[1] === KEY) catName = m[2].trim();
  }

  const matched = catName
    ? titles.filter(t => catName.includes(t.category) || t.category.includes(catName.replace(/^\S+\s/, '')))
    : titles.filter(t => t.category.includes(KEY));

  const hit = matched.length;

  console.log(`${f}: 品类 ${(sub.match(/data-cat=/g) || []).length - 1} 个，目标品类 ${hit} 条${catName ? '  [' + catName + ']' : ''}`);

  assert(sub.includes(`data-cat="${KEY}"`), `${f} 子标签缺少 ${KEY} 分支（品类可能掉进「其他」）`);
  assert(!sub.includes('📌'), `${f} 存在落到「📌 其他」的品类`);
  if (EXPECT) assert(hit === EXPECT, `${f} 期望 ${EXPECT} 条，实际 ${hit} 条`);
  assert(hit > 0, `${f} 未解析出目标品类的任何文案`);

  matched.forEach((t, i) => {
    const tag = `${f} 第${i + 1}条`;
    assert(t.en && t.en.length > 20, `${tag} EN 过短: ${t.en}`);
    assert(!/[一-龥]/.test(t.en), `${tag} EN 混入中文: ${t.en}`);
    assert(/[一-龥]/.test(t.cn) && t.cn.length > 5, `${tag} CN 异常: ${t.cn}`);
    assert(/#\w+/.test(t.en.slice(-60)), `${tag} EN 尾部缺英文标签`);
    assert(/#/.test(t.cn), `${tag} CN 缺中文标签`);
    BANNED.forEach(([re, label]) => assert(!re.test(t.en), `${tag} EN 命中${label}: ${t.en}`));
    assert(!CN_BANNED.test(t.cn), `${tag} CN 命中违禁词: ${t.cn}`);
  });

  allTitles.push(...matched.map(t => ({ f, ...t })));
}

// ---- 跨批次去重 ----
const seen = new Set();
allTitles.forEach(t => {
  if (seen.has(t.en)) fails.push(`EN 重复: ${t.en}`);
  seen.add(t.en);
});

console.log(`\n合计: ${allTitles.length} 条 / ${batchFiles.length} 批`);
if (allTitles.length) {
  console.log(`样例: ${allTitles[0].en}`);
  console.log(`      ${allTitles[0].cn}`);
}

if (fails.length) {
  console.log('\n[FAIL]');
  fails.forEach(f => console.log(' - ' + f));
  process.exit(1);
}
console.log('\n[OK] 全部校验通过');
