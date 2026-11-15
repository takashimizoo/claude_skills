"""Deep Security のリリースノート HTML から、導入版より新しいビルドの記載だけをテキストで抜き出す。

使い方:
  python -I extract_notes.py dsa <release-notes-dsa.html> <導入ビルド 例 20.0.1-14610> [Linux|Windows|Unix]
  python -I extract_notes.py dsm <release-notes-dsm.html> <導入ビルド 例 20.0.1173>
"""
import html
import re
import sys

H2 = re.compile(r'<h2[^>]*>(.*?)</h2>', re.S)


def text(fragment):
    fragment = re.sub(r'<li[^>]*>', '\n- ', fragment)
    fragment = re.sub(r'<(h3|h4)[^>]*>', '\n\n### ', fragment)
    fragment = re.sub(r'</(p|div|h3|h4|tr|ul|ol)>|<br\s*/?>', '\n', fragment)
    fragment = html.unescape(re.sub(r'<[^>]+>', '', fragment))
    fragment = re.sub(r'[ \t\r\f\v]+', ' ', fragment)
    return re.sub(r'\n\s*\n\s*\n+', '\n\n', fragment).strip()


def key(kind, title):
    if kind == 'dsa':
        m = re.search(r'20\.0\.(\d+)-(\d+)', title)
        return (int(m.group(1)), int(m.group(2))) if m else None
    m = re.search(r'20\.0\.(\d{3,})', title)
    return (int(m.group(1)),) if m else None


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    kind, path, current = sys.argv[1], sys.argv[2], sys.argv[3]
    platform = sys.argv[4] if len(sys.argv) > 4 else 'Linux'
    src = open(path, encoding='utf-8').read()
    cur = key(kind, current)
    if cur is None:
        print(f'ビルド番号を解釈できません: {current}', file=sys.stderr)
        sys.exit(1)

    heads = [(m.start(), m.end(), text(m.group(1))) for m in H2.finditer(src)]
    heads = [h for h in heads if key(kind, h[2])]
    if not heads:
        sys.exit('リリース見出し (h2) が見つかりません。ページ構成が変わった可能性があります。')

    # dsa はページ内に Linux / Windows / Unix の順でセクションが並ぶ。
    # ビルド番号が前の見出しより大きくなった位置をセクションの境界とみなし、
    # 直前のテキストからプラットフォーム名を取る。
    sections, prev = [], None
    for i, (start, end, title) in enumerate(heads):
        k = key(kind, title)
        if prev is None or k > prev:
            before = text(src[max(0, start - 3000):start]).split()
            name = before[-1] if before else '?'
            sections.append([name, []])
        sections[-1][1].append(i)
        prev = k

    if kind == 'dsa':
        names = [s[0] for s in sections]
        chosen = [s for s in sections if s[0].lower() == platform.lower()]
        if not chosen:
            sys.exit(f'プラットフォーム {platform} のセクションがありません（検出: {names}）')
        idxs = chosen[0][1]
    else:
        idxs = [i for s in sections for i in s[1]]

    found = False
    for i in idxs:
        start, end, title = heads[i]
        if key(kind, title) <= cur:
            continue
        stop = heads[i + 1][0] if i + 1 < len(heads) else len(src)
        body = src[end:stop]
        body = re.split(r'<footer|id="site-footer"', body)[0]
        print('=' * 80)
        print('##', title)
        print(text(body))
        print()
        found = True

    if not found:
        print(f'{current} より新しいビルドはありません。')


if __name__ == '__main__':
    main()
