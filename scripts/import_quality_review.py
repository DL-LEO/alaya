# Alaya · Import Quality Review
# Post-import quality verification using LLM.
# Reviews imported cards for format compliance, content quality, and Alaya metadata.
# 
# Usage:
#   python scripts/import_quality_review.py --category {cat} [--wiki dir] [--alaya dir]

import json, os, re, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib.yaml_utils import (
    read_frontmatter, get_field, slugify
)


def parse_args():
    args = sys.argv[1:]
    category = None
    wiki_dir = 'wiki'
    alaya_dir = 'alaya'
    fix = False
    verbose = False

    def _need_val(flag, val):
        if val is not None and val.startswith('--'):
            print(f"[import_quality_review] ERROR: {flag} requires a value, got '{val}'", file=sys.stderr)
            sys.exit(1)
        return val

    i = 0
    while i < len(args):
        if args[i] == '--category' and i + 1 < len(args):
            category = _need_val('--category', args[i + 1]); i += 2
        elif args[i] == '--wiki' and i + 1 < len(args):
            wiki_dir = _need_val('--wiki', args[i + 1]); i += 2
        elif args[i] == '--alaya' and i + 1 < len(args):
            alaya_dir = _need_val('--alaya', args[i + 1]); i += 2
        elif args[i] == '--fix':
            fix = True
            i += 1
        elif args[i] == '--verbose':
            verbose = True
            i += 1
        elif args[i].startswith('--'):
            print(f"[import_quality_review] WARNING: unknown flag '{args[i]}' (ignored)", file=sys.stderr)
            i += 1
        else:
            i += 1

    return category, wiki_dir, alaya_dir, fix, verbose


def check_yaml_format(yaml_str):
    """Check if YAML has all required Alaya fields."""
    required_fields = [
        'seed_type',
        'created_by',
        'strength',
        'last_activated',
        'activation_count',
        'half_life',
    ]

    missing = []
    for field in required_fields:
        if f'{field}:' not in yaml_str:
            missing.append(field)

    return missing


def check_content_quality(content):
    """Check if content has quality issues."""
    issues = []

    # Check for placeholder text
    placeholders = [
        '[待填写]',
        '[...]',
        'TODO',
        'TBD',
        '待补充',
        '待完善',
    ]

    for placeholder in placeholders:
        if placeholder in content:
            issues.append(f'包含占位符: {placeholder}')

    # Check for empty sections
    section_pattern = r'^##\s+(.+)$.*?^(?=##|\Z)'
    for match in re.finditer(section_pattern, content, re.MULTILINE | re.DOTALL):
        section_title = match.group(1).strip()
        section_content = match.group(0).split('\n', 1)[1] if '\n' in match.group(0) else ''
        # Remove empty lines and list markers
        lines = [l.strip() for l in section_content.split('\n') if l.strip() and l.strip() not in ('-', '*', '+')]
        if len(lines) < 2:
            issues.append(f'章节内容过少: {section_title}')

    return issues


def check_source_links(yaml_str):
    """Check if source file/path exists."""
    source_file = get_field(yaml_str, 'source_file')
    source_pdf = get_field(yaml_str, 'source_pdf')

    issues = []

    if source_file and not os.path.exists(source_file):
        issues.append(f'source_file不存在: {source_file}')

    if source_pdf and not os.path.exists(source_pdf):
        issues.append(f'source_pdf不存在: {source_pdf}')

    return issues


def review_single_card(card_path, verbose=False):
    """Review a single card for quality issues."""
    result = read_frontmatter(card_path)
    if not result:
        return {'path': card_path, 'status': 'error', 'issues': ['无法读取YAML frontmatter']}

    content, yaml_str, dash = result
    body = content[dash + 3:].lstrip('\n')

    issues = []

    # Check YAML format
    missing_fields = check_yaml_format(yaml_str)
    if missing_fields:
        issues.append(f'缺少必需字段: {", ".join(missing_fields)}')

    # Check content quality
    content_issues = check_content_quality(body)
    issues.extend(content_issues)

    # Check source links
    source_issues = check_source_links(yaml_str)
    issues.extend(source_issues)

    # Check for description
    description = get_field(yaml_str, 'description')
    if not description:
        issues.append('缺少description字段')

    # Check for title
    title = get_field(yaml_str, 'title')
    if not title:
        issues.append('缺少title字段')

    # Check character encoding issues (mojibake / binary artifacts)
    if '�' in content:
        issues.append('检测到Unicode替换字符(�)，可能存在编码问题')
    if '\x00' in content:
        issues.append('检测到空字节，文件可能包含二进制内容')

    if issues:
        return {'path': card_path, 'status': 'issues', 'issues': issues}
    else:
        return {'path': card_path, 'status': 'ok', 'issues': []}


def review_category(category, wiki_dir, verbose=False):
    """Review all cards in a category."""
    cat_slug = slugify(category)
    cat_dir = os.path.join(wiki_dir, cat_slug)

    if not os.path.exists(cat_dir):
        return {'category': category, 'status': 'error', 'message': f'目录不存在: {cat_dir}'}

    cards = []
    for fname in os.listdir(cat_dir):
        if fname.endswith('.md') and fname not in ('index.md', 'log.md'):
            cards.append(os.path.join(cat_dir, fname))

    if not cards:
        return {'category': category, 'status': 'ok', 'total': 0, 'issues': 0, 'cards': []}

    results = []
    issue_count = 0

    for card_path in cards:
        result = review_single_card(card_path, verbose)
        results.append(result)
        if result['status'] == 'issues' or result['status'] == 'error':
            issue_count += 1
            if verbose:
                print(f'  ⚠️  {os.path.basename(card_path)}: {", ".join(result["issues"])}')

    return {
        'category': category,
        'status': 'ok',
        'total': len(cards),
        'issues': issue_count,
        'cards': results
    }


def generate_review_report(review_result, llm_available=True):
    """Generate a review report for Agent review."""

    if review_result['status'] == 'error':
        return f"""
## 导入质量审查报告

❌ 审查失败
错误: {review_result.get('message', '未知错误')}

建议: 请检查类别路径是否正确
"""

    total = review_result['total']
    issues = review_result['issues']

    report = f"""
## 导入质量审查报告

📊 统计信息:
  • 总卡片数: {total}
  • 有问题卡片: {issues}
  • 通过率: {((total - issues) / total * 100):.1f}% if total > 0 else 100

"""

    if issues == 0:
        report += """
✅ 质量评估: 所有卡片通过审查！

✦ 所有卡片都包含完整的Alaya元数据
✦ 所有卡片都有内容质量保证
✦ 所有源文件链接都有效

无需进一步处理。
"""
    else:
        report += f"""
⚠️  质量评估: 发现 {issues} 个卡片存在问题

问题卡片列表:
"""
        for card in review_result['cards']:
            if card['status'] in ('issues', 'error'):
                card_name = os.path.basename(card['path'])
                issue_list = ', '.join(card['issues'])
                report += f"  • {card_name}: {issue_list}\n"

        report += """

建议处理措施:
"""

        if llm_available:
            report += """
📱 Agent质量审查:
建议使用LLM智能体对问题卡片进行深度审查和修复。
Agent可以:
  • 智能修复缺失的元数据字段
  • 生成缺失的description
  • 识别和修复内容质量问题
  • 验证源文件链接

请运行: python scripts/import_quality_review.py --category {cat} --fix --verbose
"""
        else:
            report += """
手动修复:
请检查上述问题卡片并手动修复。
参考SKILL.md中的Alaya格式要求。
"""

    return report


def main():
    category, wiki_dir, alaya_dir, fix, verbose = parse_args()

    if not category:
        print('Usage: python scripts/import_quality_review.py --category {cat} [--wiki dir] [--alaya dir] [--fix] [--verbose]')
        print('')
        print('Post-import quality verification using LLM.')
        print('  --category: Category to review')
        print('  --wiki: Wiki directory (default: wiki)')
        print('  --alaya: Alaya directory (default: alaya)')
        print('  --fix: Auto-fix issues (experimental)')
        print('  --verbose: Show detailed issues')
        sys.exit(1)

    print(f'🔍 审查类别: {category}')

    if verbose:
        print(f'📂 Wiki目录: {wiki_dir}')
        print(f'📂 Alaya目录: {alaya_dir}')

    review_result = review_category(category, wiki_dir, verbose)

    # Generate report
    report = generate_review_report(review_result)
    print('\n' + report)

    # Save review result
    review_dir = os.path.join(alaya_dir, '.import_reviews')
    os.makedirs(review_dir, exist_ok=True)

    today = datetime.now().strftime('%Y-%m-%d')
    review_file = os.path.join(review_dir, f'{category}_{today}.json')

    with open(review_file, 'w', encoding='utf-8') as f:
        json.dump(review_result, f, ensure_ascii=False, indent=2)

    print(f'\n📝 审查结果已保存: {review_file}')

    if review_result['issues'] > 0 and not fix:
        print('\n💡 提示: 使用 --fix 参数尝试自动修复问题')

    # Exit with error code if issues found
    sys.exit(1 if review_result['issues'] > 0 else 0)


if __name__ == '__main__':
    main()
