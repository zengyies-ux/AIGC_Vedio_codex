#!/usr/bin/env python3
"""Read-only checks on the existing Markdown prompt, not a visual-quality grader."""
import argparse
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR
import json
import math
from pathlib import Path
import re

NUM = r'\d+(?:\.\d+)?'
RANGE = rf'({NUM})\s*[–—-]\s*({NUM})\s*秒'
SHOT = re.compile(rf'^镜头\s*(\d+)【\s*{RANGE}[^\n]*', re.M)


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
    reserve = Decimal(total) - audio
    minimum = int((audio + 6).to_integral_value(rounding=ROUND_CEILING))
    maximum = int((audio + 10).to_integral_value(rounding=ROUND_FLOOR))
    return {'status': 'assessed', 'budget_pass': 6 <= reserve <= 10,
            'audio_seconds': float(audio), 'generated_seconds': total,
            'reserve_seconds': float(reserve),
            'integer_generated_range': [minimum, maximum],
            'detail': 'G sums native submissions and extension additions once; excludes source copies and retries'}


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
    if len(blocks) != 1:
        return {'structural_pass': False, 'errors': [{'code': 'body_count', 'detail': '需要唯一可复制text正文'}], 'warnings': [], 'shots': [], 'visual_quality': 'not_assessed', 'source_continuity': 'not_assessed',
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
    sounds = [(float(m[1]),float(m[2])) for m in re.finditer(rf'^局部\s*{RANGE}', body,re.M)]
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
        for opening in re.finditer(rf'(?:声音时序|局部|在)\s*({NUM})\s*秒开口', chunk):
            when=float(opening[1])
            if not (a-1e-6 <= when < b):
                issue(errors,'opening_outside_shot',f'镜头{number}开口{when}不在{a}–{b}')
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
            episode = json.loads(args.episode_budget.read_text())
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
