#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
给 margin-calculator 新增 TikTok 文案品类（结构化四步）

为什么需要这个脚本：
  只往 md 里加文案是不够的。index.html 里有两处「品类识别」没同步的话，
  新品类会掉进「📌 其他」区块，用户完全看不到。手动改容易漏。

本脚本一次做完四件事：
  1. 每个批次 md 文件追加品类区块
  2. index.html 的 catKey() 增加归一化分支
  3. index.html 的 icon 映射增加 emoji
  4. index.html 的轮播说明文案补充品类名称
最后自动调用 verify_copy.js 做解析校验。

用法：
  python add_copy_category.py --config tools/new_category.json [--dry-run]

配置项见 new_category.example.json
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys


def _setup_stdout():
    """Windows GBK 控制台下安全输出中文（emoji 会降级为 ?，不影响写入文件）"""
    try:
        sys.stdout.reconfigure(encoding='gbk', errors='replace')
        sys.stderr.reconfigure(encoding='gbk', errors='replace')
    except Exception:
        pass


def detect_eol(data: bytes) -> bytes:
    return b'\r\n' if data.count(b'\r\n') > data.count(b'\n') - data.count(b'\r\n') else b'\n'


def read_text(path: str):
    data = open(path, 'rb').read()
    return data.decode('utf-8'), detect_eol(data)


def write_text(path: str, text: str, eol: bytes):
    data = text.encode('utf-8').replace(b'\r\n', b'\n').replace(b'\n', eol)
    open(path, 'wb').write(data)


def unique_insert(text: str, anchor: str, insertion: str, label: str, dry: bool):
    """在 anchor 之前插入一行；anchor 必须唯一，已存在则不重复插入"""
    cnt = text.count(anchor)
    if cnt != 1:
        raise RuntimeError(f'锚点[{label}]出现 {cnt} 次，期望 1 次，中止以免改错地方')
    if insertion.strip() in text:
        return text, False
    return text.replace(anchor, insertion + anchor), True


def patch_index_html(repo: str, cfg: dict, dry: bool):
    path = os.path.join(repo, 'index.html')
    text, eol = read_text(path)
    orig = text
    log = []

    key = cfg['key']
    match = cfg['match']
    icon = cfg['icon']

    # 1) 品类归一化分支 —— 插在 return 'other'; 之前（优先级最低，安全）
    text, ok1 = unique_insert(
        text,
        "    return 'other';",
        f"    if (name.indexOf('{match}') >= 0) return '{key}';\n",
        'catKey return other',
        dry,
    )
    log.append(('catKey 分支', ok1))

    # 2) 图标映射 —— 插在 else icon = '📌'; 之前
    text, ok2 = unique_insert(
        text,
        "      else icon = '📌';",
        f"      else if (catName.indexOf('{match}') >= 0) icon = '{icon}';\n",
        'icon fallback',
        dry,
    )
    log.append(('图标映射', ok2))

    # 3) 轮播说明文案 —— 在「纯痛点：A / B / C」列表里追加一个
    ui_label = cfg.get('ui_label') or match
    m = re.search(r'(纯痛点：)([^）]+)', text)
    if not m:
        raise RuntimeError('未找到「纯痛点：」说明行，UI 文案跳过（其余改动仍生效）')
    existing = m.group(2)
    if ui_label not in existing:
        new_list = existing.rstrip() + ' / ' + ui_label
        text = text[:m.start(2)] + new_list + text[m.end(2):]
        log.append(('轮播说明文案', True))
    else:
        log.append(('轮播说明文案', False))

    if text != orig and not dry:
        write_text(path, text, eol)
    elif dry:
        log.append(('index.html(预览)', True))

    return log


def append_to_batches(repo: str, cfg: dict, dry: bool):
    name = cfg['name']
    icon = cfg['icon']
    batches = cfg['batches']
    log = []

    for batch, titles_file in batches.items():
        md_path = os.path.join(repo, f'tiktok_titles_{batch}.md')
        if not os.path.isfile(md_path):
            raise RuntimeError(f'批次文件不存在: {md_path}')
        titles_path = titles_file if os.path.isabs(titles_file) else os.path.join(repo, titles_file)
        if not os.path.isfile(titles_path):
            raise RuntimeError(f'文案源文件不存在: {titles_path}')

        text, eol = read_text(md_path)
        # 跳过空行与注释行（分号或井号开头），注释行允许用户在文案源文件里写填写说明
        lines = []
        for l in io.open(titles_path, encoding='utf-8'):
            l = l.strip()
            if not l or l.startswith(';') or l.startswith('#'):
                continue
            lines.append(l)
        if cfg['name'] in text:
            log.append((f'批次{batch}', False, '已存在同名品类，跳过'))
            continue

        header = f"### {icon} {name}\n\n"
        block = '\n' + header + '\n'.join(lines) + '\n'
        new_text = text.rstrip('\n') + '\n' + block

        if not dry:
            write_text(md_path, new_text, eol)
        n = len([l for l in lines if '|' in l])
        log.append((f'批次{batch}', True, f'{n} 条'))

    return log


def run_verify(repo: str, key: str, expect: int):
    here = os.path.dirname(os.path.abspath(__file__))
    node = r'C:\Users\C Z\.workbuddy\binaries\node\versions\22.22.2\node.exe'
    script = os.path.join(here, 'verify_copy.js')
    cmd = [node, script, '--repo', repo, '--key', key]
    if expect:
        cmd += ['--expect', str(expect)]
    proc = subprocess.run(cmd, capture_output=True)
    out = (proc.stdout or b'').decode('utf-8', 'replace') + (proc.stderr or b'').decode('utf-8', 'replace')
    return proc.returncode, out


def git_is_clean(repo: str):
    proc = subprocess.run(['git', 'status', '--porcelain'], cwd=repo, capture_output=True)
    if proc.returncode != 0:
        return None
    return (proc.stdout or b'').decode('utf-8', 'replace').strip()


def main():
    _setup_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True, help='JSON 配置文件路径')
    ap.add_argument('--repo', default=None, help='仓库根目录（默认取配置文件所在目录的上级）')
    ap.add_argument('--dry-run', action='store_true', help='只预览不写文件')
    ap.add_argument('--no-verify', action='store_true', help='跳过 node 校验')
    args = ap.parse_args()

    cfg = json.loads(io.open(args.config, encoding='utf-8').read())
    required = ['name', 'icon', 'key', 'match', 'batches']
    missing = [k for k in required if k not in cfg]
    if missing:
        print(f'[FAIL] 配置缺少字段: {missing}')
        return 1

    repo = args.repo or os.path.dirname(os.path.dirname(os.path.abspath(args.config)))
    if not os.path.isfile(os.path.join(repo, 'index.html')):
        print(f'[FAIL] 不像仓库根目录（没有 index.html）: {repo}')
        return 1

    print(f'仓库: {repo}')
    print(f'品类: {cfg["icon"]} {cfg["name"]}')
    print(f'对照 key: {cfg["key"]} / 匹配词: {cfg["match"]}')
    if args.dry_run:
        print('[预览模式] 不会写入任何文件\n')

    state = git_is_clean(repo)
    if state is None:
        print('[WARN] 无法读取 git 状态，继续但请自行确认工作区干净')
    elif state and not args.dry_run:
        print('[提醒] 工作区已有未提交改动，本次改动会与之混在一起')

    print('\n=== 1. 批次文案文件 ===')
    try:
        for name_, ok, note in append_to_batches(repo, cfg, args.dry_run):
            print(f'  {name_:16s} {"已追加 " + note if ok else "跳过（" + note + "）"}')
    except RuntimeError as e:
        print(f'  [FAIL] {e}')
        return 1

    print('\n=== 2. index.html ===')
    try:
        for name_, ok in patch_index_html(repo, cfg, args.dry_run):
            print(f'  {name_:16s} {"已修改" if ok else "无需修改（已存在）"}')
    except RuntimeError as e:
        print(f'  [FAIL] {e}')
        return 1

    if args.dry_run:
        print('\n预览结束，未写入。去掉 --dry-run 正式执行。')
        return 0

    if args.no_verify:
        print('\n已跳过校验。')
        return 0

    print('\n=== 3. 解析校验 ===')
    expect = cfg.get('expect_per_batch')
    code, out = run_verify(repo, cfg['key'], expect)
    sys.stdout.write(out)
    if code != 0:
        print('\n[FAIL] 校验未通过，请检查上面输出。改动已写入，可用 git diff 回退。')
        return 1

    print('\n=== 下一步 ===')
    print('  1) git diff 过一遍改动')
    print('  2) git add . && git commit -m "feat(copy): ..."')
    print('  3) 推送前先 git fetch 确认没有别人新推的提交（避免 rebase）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
