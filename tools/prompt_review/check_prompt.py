#!/usr/bin/env python3
"""Read-only checks on the existing Markdown prompt, not a visual-quality grader."""
import argparse
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import json
import math
from pathlib import Path
import re

NUM = r'\d+(?:\.\d+)?'
RANGE = rf'({NUM})\s*(?:秒|s)?\s*[–—-]\s*({NUM})\s*(?:秒|s)'
SHOT = re.compile(rf'^镜头\s*(\d+)【\s*\(?\s*{RANGE}[^\n]*', re.M)


def assess_episode_budget(episode=None, base_dir=None):
    """Check only the explicitly supplied current segments; never discover history."""
    if episode is None:
        return {'status': 'not_assessed', 'detail': 'budget not assessed'}
    if not isinstance(episode, dict) or set(episode) != {'audio_seconds', 'segments'}:
        raise ValueError('episode budget requires only audio_seconds and segments')
    audio = episode['audio_seconds']
    if isinstance(audio, bool) or not isinstance(audio, (int, float, Decimal)):
        raise ValueError('audio_seconds must be a finite positive number')
    try:
        audio = Decimal(str(audio))
    except InvalidOperation as exc:
        raise ValueError('audio_seconds must be a finite positive number') from exc
    if not audio.is_finite() or audio <= 0:
        raise ValueError('audio_seconds must be a finite positive number')
    segments = episode['segments']
    if not isinstance(segments, list) or not segments:
        raise ValueError('segments must be a nonempty list of unique current prompt paths')
    seen, total = set(), 0
    base = Path(base_dir or Path.cwd())
    for segment in segments:
        if not isinstance(segment, dict) or set(segment) != {'path', 'mode', 'seconds'}:
            raise ValueError('each segment requires only path, mode and seconds; source lengths and retries are excluded')
        path = segment['path']
        if not isinstance(path, str) or not path.strip() or any(c in path for c in '*?[]'):
            raise ValueError('segment path must be explicit, not a glob')
        resolved = (base / path).resolve()
        if resolved in seen:
            raise ValueError(f'duplicate current segment path: {path}')
        seen.add(resolved)
        if segment['mode'] not in ('native', 'extension'):
            raise ValueError('segment mode must be native or extension')
        seconds = segment['seconds']
        if type(seconds) is not int or seconds <= 0:
            raise ValueError('segment seconds must be a positive integer; extension means newly added seconds')
        total += seconds
    # Exact rational arithmetic keeps ceil independent of Decimal context and
    # avoids rounding the recurring 7*A/60 reserve before the integer ceiling.
    audio_ratio = Fraction(audio)
    minimum_reserve = 8 + 7 * audio_ratio / 60
    minimum = math.ceil((67 * audio_ratio + 480) / 60)
    reserve = total - audio_ratio
    return {'status': 'assessed', 'budget_pass': total >= minimum,
            'budget_scope': 'minimum_only',
            'audio_seconds': float(audio), 'generated_seconds': total,
            'reserve_seconds': float(reserve),
            'minimum_reserve_seconds': float(minimum_reserve),
            'minimum_generated_seconds': minimum,
            'target_generated_seconds': minimum,
            'excess_seconds': max(0, total - minimum),
            'excess_review_required': total > minimum,
            'integer_generated_range': [minimum, None],
            'detail': ('Minimum quantity only; default target is Gmin, excess requires a concrete reason '
                       'and handling under existing authorization. G sums native submissions and extension '
                       'additions once; excludes source copies and retries. No cost, editability, semantic '
                       'or submission approval is established')}


def inspect_extension_source(body, generation_mode=None):
    """Text checks cannot establish actual upload nodes, source identity or readiness."""
    if generation_mode not in (None, 'native', 'extension'):
        raise ValueError('generation_mode must be native or extension')
    report = {'status': 'not_assessed', 'source_binding': 'not_assessed',
              'detail': 'Actual video node, semantic source identity and extension readiness require real evidence'}
    if generation_mode != 'extension':
        return report
    def section(name):
        match = re.search(r'【' + name + r'】\s*\n(.*?)(?=\n【|\Z)', body, re.S)
        return match[1] if match else ''
    refs = re.findall(r'^([^\n：:]+)[：:][ \t]*【?(@视频\d+)】?[^\n]*$',
                      section('人物与场景参考'), re.M)
    if len(refs) != 1:
        return {**report, 'status': 'missing_or_ambiguous',
                'detail': 'Extension body needs one fixed source name with @视频 in 人物与场景参考'}
    name, reference = refs[0][0].strip(), refs[0][1]
    state = re.search(r'^' + re.escape(name) + r'[：:][ \t]*\S[^\n]*$',
                      section('空间与道具状态'), re.M)
    return {**report, 'status': 'text_reference_present' if state else 'state_name_missing',
            'source_name': name, 'video_reference': reference,
            'detail': ('Text reference and same-name state present; actual binding remains unverified' if state else
                       '空间与道具状态 needs the identical fixed source name and a state description')}


def inspect(text, max_shot_seconds=2.5, generation_mode=None):
    if not math.isfinite(max_shot_seconds) or max_shot_seconds <= 0:
        raise ValueError('max_shot_seconds must be finite and positive')
    source_reference = inspect_extension_source('', generation_mode)
    errors, warnings, rows = [], [], []
    def issue(target, code, detail):
        target.append({'code': code, 'detail': detail})
    blocks = re.findall(r'```text\s*\n(.*?)```', text, re.S)
    blocks = [b for b in blocks if '【生成任务】' in b and '【镜头设计】' in b]
    markers = list(re.finditer(r'^##[ \t]+唯一可复制正文[ \t]*$', text, re.M))
    if len(markers) > 1:
        blocks = []
    elif markers:
        section = re.split(r'^#{1,6}[ \t]+', text[markers[0].end():], maxsplit=1, flags=re.M)[0]
        # Accept the real production heading format as well as the template's
        # fenced body. Do not infer a body from arbitrary unmarked prose.
        if '```' not in section and '【生成任务】' in section and '【镜头设计】' in section:
            blocks.append(section.strip())
    if any(b.count('【生成任务】') != 1 or b.count('【镜头设计】') != 1 for b in blocks):
        blocks = []
    if len(blocks) != 1:
        return {'structural_pass': False, 'errors': [{'code': 'body_count', 'detail': '需要唯一text代码块或“## 唯一可复制正文”下的明确正文'}], 'warnings': [], 'shots': [], 'visual_quality': 'not_assessed', 'source_continuity': 'not_assessed',
                'episode_budget': assess_episode_budget(), 'source_reference': source_reference,
                'declared_generation_seconds': None}
    body = blocks[0]
    source_reference = inspect_extension_source(body, generation_mode)
    if generation_mode == 'extension' and source_reference['status'] != 'text_reference_present':
        issue(errors, 'extension_source_reference', source_reference['detail'])
    duration = re.search(rf'生成\s*({NUM})\s*秒', body)
    count = re.search(r'共\s*(\d+)\s*个?\s*(?:真实)?镜(?:头)?', body)
    matches = list(SHOT.finditer(body))
    if not duration:
        issue(errors, 'duration_missing', '未识别生成任务秒数')
    if not matches:
        issue(errors, 'shots_missing', '未识别逐镜时码')
    if not count:
        issue(errors, 'shot_count_missing', '未识别声明镜数')
    if count and int(count[1]) != len(matches):
        issue(errors, 'shot_count', '声明镜数与编号镜头数不一致')
    prev = 0.0
    sound_section = re.search(r'【声音时序】\s*\n(.*?)(?=\n【|\Z)', body, re.S)
    sound_text = sound_section[1] if sound_section else ''
    sounds = [(float(m[1]), float(m[2])) for m in
              re.finditer(rf'^(?:局部\s*)?{RANGE}', sound_text, re.M)]
    voices = [(float(m[1]), float(m[2]), m[3].strip()) for m in
              re.finditer(rf'^(?:局部\s*)?{RANGE}\s*[｜|]\s*([^→\n｜|]+)→', sound_text, re.M)]
    speakers = sorted({v[2] for v in voices}, key=len, reverse=True)
    for a,b in sounds:
        if b <= a or (duration and b > float(duration[1]) + 1e-6):
            issue(errors, 'sound_range', f'{a}–{b}')
    for i,m in enumerate(matches):
        number, a, b = int(m[1]), float(m[2]), float(m[3])
        chunk = body[m.end():matches[i+1].start() if i+1<len(matches) else len(body)].split('【摄影、光线与真实感】')[0]
        length=b-a
        rows.append({'number':number,'start':a,'end':b,'seconds':round(length,6)})
        if number != i+1:
            issue(errors,'shot_number',f'镜头编号{number}应为{i+1}')
        if length <= 0:
            issue(errors,'nonpositive_shot',f'镜头{number}')
        if length > max_shot_seconds+1e-6:
            issue(errors,'shot_too_long',f'镜头{number}: {length:.3f}s > {max_shot_seconds}s')
        if abs(a-prev)>1e-6:
            issue(errors,'coverage_gap_or_overlap',f'镜头{number}起点{a}，前镜终点{prev}')
        prev=b
        # Explicit single opening times only. A whole-line range is not a shot length.
        for opening in re.finditer(rf'(?<![\d.])({NUM})\s*(?:秒|s)\s*开口', chunk):
            when=float(opening[1])
            if not (a-1e-6 <= when < b):
                issue(errors,'opening_outside_shot',f'镜头{number}开口{when}不在{a}–{b}')
        # This is only a narrow textual cue, never a semantic speech verdict.
        # Use known names and continuous windows; do not invent missing subjects.
        if speakers:
            named_subject = re.compile(r'^(?:(?:具体画面|现场对白)[：:]\s*)?(' + '|'.join(re.escape(name) for name in speakers) + r')')
            for clause in re.split(r'[。；;\n]', chunk):
                if '开口' not in clause or re.search(r'准备|等待|等.{0,8}开口|尚未|还未|没有|未曾|不再|不会|不开口|未开口|无词', clause):
                    continue
                for opening in re.finditer('开口', clause):
                    subject = named_subject.match(clause.strip())
                    if not subject:
                        continue
                    speaker = subject[1]
                    if not any(name == speaker and a < end and start < b
                               for start, end, name in voices):
                        issue(warnings, 'inspect_opening_without_sound',
                              f'镜头{number}描述{speaker}开口，但本镜无该角色已列声音窗口；核提前/重复开口或未列发言，不据此判定新增台词')
        if re.search(r'切到|切回|再回到|硬切至|(?:近景|关系镜)切',m[0]+chunk):
            issue(warnings,'inspect_hidden_cut',f'镜头{number}含切换用语，请确认真实边界均单列')
        if re.search(r'沉默|没有说出话|闭口|安静',chunk) and any(a < d and c < b for c,d in sounds):
            issue(warnings,'inspect_silent_subject',f'镜头{number}有静默描述且有对白，核对具体人物；听者安静可合法')
    if duration and matches and abs(prev-float(duration[1]))>1e-6:
        issue(errors,'end_coverage','逐镜终点不等于生成时长')
    if re.search(r'P\d{3,}|由后期|后期旁白|旁白由后期|旁白.*编排',body):
        issue(errors,'postproduction_in_body','可复制正文混入原文编号或后期调度')
    if '特写' not in body:
        issue(warnings,'inspect_visual_scale','无明确特写用语；人工判断转折是否看清，禁止凑关键词')
    return {'structural_pass':not errors,'errors':errors,'warnings':warnings,'shots':rows,
            'visual_quality':'not_assessed','source_continuity':'not_assessed',
            'episode_budget': assess_episode_budget(), 'source_reference': source_reference,
            'declared_generation_seconds': float(duration[1]) if duration else None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*', type=Path)
    parser.add_argument('--max-shot-seconds',type=float,default=2.5,help='默认2.5秒：当前同类快节奏旁白短剧；其他题材传实际上限')
    parser.add_argument('--mode', choices=('native', 'extension'), help='显式生成方式；整集输入时使用每段mode')
    parser.add_argument('--episode-budget', type=Path, help='显式A及唯一当前各段path/mode/seconds的JSON；不扫描历史')
    args=parser.parse_args()
    try:
        budget = assess_episode_budget()
        modes = {}
        files = args.files
        if args.episode_budget:
            if args.mode:
                raise ValueError('--mode cannot override explicit episode segment modes')
            episode = json.loads(args.episode_budget.read_text(), parse_float=Decimal)
            base = args.episode_budget.resolve().parent
            budget = assess_episode_budget(episode, base)
            current = [(base / s['path']).resolve() for s in episode['segments']]
            if files and ([p.resolve() for p in files] != current):
                raise ValueError('positional files must exactly match the explicit current segment paths and order')
            files = current
            modes = {p: s['mode'] for p, s in zip(current, episode['segments'])}
        if not files:
            raise ValueError('supply prompt files or --episode-budget')
        reports=[{'file':str(p),**inspect(p.read_text(), args.max_shot_seconds,
                                        modes.get(p, args.mode))} for p in files]
        if args.episode_budget:
            for report, segment in zip(reports, episode['segments']):
                if report['declared_generation_seconds'] != segment['seconds']:
                    report['errors'].append({'code': 'submission_duration_mismatch',
                                             'detail': '正文生成秒数与显式提交/延长新增秒数不一致'})
                    report['structural_pass'] = False
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    output = {'prompts': reports, 'episode_budget': budget} if args.episode_budget else reports
    print(json.dumps(output,ensure_ascii=False,indent=2))
    raise SystemExit(0 if all(r['structural_pass'] for r in reports)
                     and budget.get('budget_pass', True) else 1)

if __name__=='__main__': main()
