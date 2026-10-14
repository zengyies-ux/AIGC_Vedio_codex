#!/usr/bin/env python3
"""Read-only checks on the existing Markdown prompt, not a visual-quality grader."""
import argparse
import json
import math
from pathlib import Path
import re

NUM = r'\d+(?:\.\d+)?'
RANGE = rf'({NUM})\s*[–—-]\s*({NUM})\s*秒'
SHOT = re.compile(rf'^镜头\s*(\d+)【\s*{RANGE}[^\n]*', re.M)


def inspect(text, max_shot_seconds=3.0):
    if not math.isfinite(max_shot_seconds) or max_shot_seconds <= 0:
        raise ValueError('max_shot_seconds must be finite and positive')
    errors, warnings, rows = [], [], []
    def issue(target, code, detail):
        target.append({'code': code, 'detail': detail})
    blocks = re.findall(r'```text\s*\n(.*?)```', text, re.S)
    blocks = [b for b in blocks if '【生成任务】' in b and '【镜头设计】' in b]
    if len(blocks) != 1:
        return {'structural_pass': False, 'errors': [{'code': 'body_count', 'detail': '需要唯一可复制text正文'}], 'warnings': [], 'shots': [], 'visual_quality': 'not_assessed'}
    body = blocks[0]
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
            'visual_quality':'not_assessed','source_continuity':'not_assessed'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files',nargs='+',type=Path)
    parser.add_argument('--max-shot-seconds',type=float,default=3.0,help='当前用户快节奏任务为3秒；其他题材传实际上限')
    args=parser.parse_args()
    reports=[{'file':str(p),**inspect(p.read_text(),args.max_shot_seconds)} for p in args.files]
    print(json.dumps(reports,ensure_ascii=False,indent=2))
    raise SystemExit(0 if all(r['structural_pass'] for r in reports) else 1)

if __name__=='__main__': main()
