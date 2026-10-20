"""Durable, small receipt journal for the host LLM's normal browser operations.

No browser driver, private API, click, sleep, download or payment lives here.
Only apply_event(..., op='intent') can return a one-use click permission, AFTER
an atomic save and readback. A lost permission is deliberately not reissued:
resume by reading the visible queue/history, never by retrying the click.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlparse


ACTIVE = ('submit_intent', 'processing', 'unknown')
IDENTITY = ('id', 'card', 'prompt_version', 'prompt_sha256', 'mode', 'seconds',
            'model', 'resolution', 'source_task', 'aspect_ratio', 'repair_root', 'repair_of')


def now():
    return datetime.now(timezone.utc).isoformat()


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _number(value, label, minimum=0):
    if isinstance(value, bool):
        raise ValueError(f'{label} must be a finite number')
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f'{label} must be a finite number') from None
    if not number.is_finite() or number < minimum:
        raise ValueError(f'{label} must be at least {minimum}')
    return number


def _scope(scope):
    if set(scope) != {'project', 'episode', 'target_url'} or not all(_text(v) for v in scope.values()):
        raise ValueError('Exact project, episode and trusted full target_url required')
    url = urlparse(scope['target_url'])
    if url.scheme not in ('https', 'http') or not url.netloc:
        raise ValueError('A full visible project URL is required')


def _authorization(value):
    auth = deepcopy(value)
    auth.setdefault('mode', 'prepare')
    if auth['mode'] not in ('prepare', 'generate'):
        raise ValueError('Authorization mode must be prepare or generate')
    if auth['mode'] == 'generate' and not all(_text(auth.get(k)) for k in ('quote', 'source')):
        raise ValueError('Generation requires the current explicit human instruction and its source')
    limit = auth.get('max_submissions')
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError('Only an actual positive user submission limit may be recorded')
    if auth.get('max_cost') is not None:
        _number(auth['max_cost'], 'User maximum cost')
        if not _text(auth.get('currency')):
            raise ValueError('An explicit cost limit needs its actual currency/unit')
    for key in ('review_required', 'auto_repair', 'review_audio'):
        if key in auth and type(auth[key]) is not bool:
            raise ValueError('Review and repair authorization flags must be boolean')
    if auth.get('auto_repair') and not auth.get('review_required'):
        raise ValueError('Automatic repair requires actual-result review')
    return auth


def snapshot(record):
    """Immutable adoption/target facts the host must reconcile after takeover."""
    return {'scope': deepcopy(record['scope']),
            'tasks': {key: {k: deepcopy(t[k]) for k in IDENTITY if k in t}
                      for key, t in record['tasks'].items()}}


def create(scope, authorization, tasks, simulation=False):
    _scope(scope)
    if type(simulation) is not bool:
        raise ValueError('simulation must be an explicit boolean')
    rows = {}
    for task in tasks:
        t = deepcopy(task)
        if not _text(t.get('id')) or t['id'] in rows or not _text(t.get('card')):
            raise ValueError('Unique task and actual, already reconciled card mapping required')
        if not _text(t.get('prompt_version')) or not re.fullmatch('[0-9a-f]{64}', t.get('prompt_sha256', '')):
            raise ValueError('Adopted version and exact body SHA256 required')
        if t.get('mode') not in ('native', 'extend'):
            raise ValueError('Mode must be native or extend')
        if type(t.get('seconds')) is not int or t['seconds'] < 1:
            raise ValueError('Adopted integer seconds required')
        if t['mode'] == 'native' and t.get('source_task'):
            raise ValueError('Independent native tasks cannot carry an implicit previous-episode source')
        t.setdefault('model', '2.5 Pro')
        t.setdefault('resolution', '480P')
        t.setdefault('downstream_result_keys', [])
        if not isinstance(t['downstream_result_keys'], list) or not all(_text(k) for k in t['downstream_result_keys']):
            raise ValueError('Known existing downstream results need exact locators')
        t.update(status='prepared', intent=None, receipt=None, result=None, source_check=None,
                 wait_issues=0, attention=None, review=None, reviews=[], repair_root=t['id'],
                 repair_of=None, superseded_by=None, prior_repair_attempts=0, history_reconciled=True)
        rows[t['id']] = t
    if not rows:
        raise ValueError('At least one adopted task required')
    for t in rows.values():
        if t['mode'] == 'extend':
            source = rows.get(t.get('source_task'))
            if not source or source['mode'] != 'native':
                raise ValueError('Extension needs one native source in this episode; no extension chain')
    return dict(schema=2, scope=deepcopy(scope), authorization=_authorization(authorization),
                simulation=simulation, paused=False, tasks=rows, updated_at=now())


def _same_snapshot(record, current, evidence):
    if current != snapshot(record) or not _text(evidence):
        raise ValueError('Reconcile the actual target, adopted version, cards and visible queue/history first')


def _identity(record, task, visible):
    expected = {**record['scope'], 'card': task['card'], 'prompt_version': task['prompt_version'],
                'prompt_sha256': task['prompt_sha256'], 'mode': task['mode']}
    if any(visible.get(k) != v for k, v in expected.items()):
        raise ValueError('Visible target/body/version/mode differs from the adopted task')


def _interval(value, duration):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError('Original-source start/end interval required')
    start, end = (_number(x, 'Source interval') for x in value)
    # Visible UI can round a 30.048s resource to 30.05s; do not infer a new end.
    if end <= start or end > duration + Decimal('0.01'):
        raise ValueError('Selected interval lies outside the actual source')
    return [str(start), str(end)]


def _user_accepted(record, task):
    acceptance = task.get('user_acceptance')
    selected = record.get('accepted_results', {}).get(task.get('repair_root', task['id']))
    return (selected == task['id'] and task['status'] == 'result' and task.get('result') is not None
            and acceptance is not None and acceptance['result_key'] == task['result']['key'])


def _source_usable(record, task):
    selected = record.get('accepted_results', {}).get(task.get('repair_root', task['id']))
    if selected and selected != task['id']:
        return False
    return _user_accepted(record, task) or (task.get('review') is not None
                                  and task['review']['outcome'] in ('usable', 'minor'))


def _user_accept(record, task_id, result_key, quote, source, evidence):
    task = record['tasks'][task_id]
    if task['status'] != 'result' or not task.get('result') or result_key != task['result']['key']:
        raise ValueError('User acceptance must identify one definite actual result, never a pending/unknown submission')
    _identity(record, task, task['result'])
    if not all(_text(value) for value in (quote, source, evidence)):
        raise ValueError('Direct human acceptance quote, message source and exact-result evidence required')
    acceptance = dict(result_key=result_key, quote=quote, source=source, evidence=evidence, at=now())
    task.setdefault('user_acceptances', []).append(acceptance)
    task['user_acceptance'] = acceptance
    record.setdefault('accepted_results', {})[task.get('repair_root', task['id'])] = task_id
    # Review, actual coverage, defects and local source_check stay unchanged.


def _source_check(record, task_id, result_key, qualified, interval, evidence, unextended):
    t = record['tasks'][task_id]
    source = record['tasks'].get(t.get('source_task'))
    if t['mode'] != 'extend' or not source or source['mode'] != 'native' or source['status'] != 'result' or source['result']['key'] != result_key:
        raise ValueError('Check the exact completed native source first')
    if type(qualified) is not bool or unextended is not True or not _text(evidence):
        raise ValueError('Explicit local endpoint/body/space evidence and an unextended-source check required')
    if record['paused'] or t['intent'] is not None:
        raise ValueError('Cannot alter source while paused or after submission intent')
    result = source['result']
    if type(result.get('extension_count')) is not int or result['extension_count'] < 0 or (not t.get('repair_of') and result['extension_count'] != 0):
        raise ValueError('The actual native source is already extended or its extension history is unknown')
    if record['authorization'].get('review_required') and not _source_usable(record, source):
        raise ValueError('Review the actual native result before using it as a source')
    selected = _interval(interval, _number(result['actual_seconds'], 'Actual source duration', minimum=Decimal('0.001')))
    t['source_check'] = dict(result_key=result_key, qualified=qualified, interval=selected,
                             evidence=evidence, unextended=True)


def _begin_submission(record, task_id, visible, live=True):
    if record['authorization']['mode'] != 'generate':
        raise ValueError('Prepare-only authorization never permits a submit click')
    if type(live) is not bool or live == record['simulation']:
        raise ValueError('Simulation and live execution must never be interchanged')
    if record['paused']:
        raise ValueError('User takeover: stop writes and reconcile before resuming')
    t = record['tasks'][task_id]
    if t.get('superseded_by'):
        raise ValueError('Superseded task cannot submit')
    if t.get('repair_of'):
        _repair_gate(record, record['tasks'][t['repair_of']], adding=False)
    if t['status'] != 'prepared' or t['intent'] is not None:
        raise ValueError('Already attempted or unresolved; inspect queue/history, never retry automatically')
    active = [row for row in record['tasks'].values() if row['status'] in ACTIVE]
    if any(row['status'] in ('submit_intent', 'unknown') for row in active):
        raise ValueError('Reconcile the active submission before another click')
    # A confirmed processing native job may coexist with another independent
    # native submission in this SAME record. Unresolved clicks still stop all
    # new submissions; extensions retain the sequential source workflow.
    if active and (t['mode'] != 'native' or any(row['mode'] != 'native' for row in active)):
        raise ValueError('Reconcile the active submission before extension-related work')
    _identity(record, t, visible)
    parameters = {k: t[k] for k in ('model', 'resolution', 'seconds')}
    if 'aspect_ratio' in t:
        parameters['aspect_ratio'] = t['aspect_ratio']
    if type(visible.get('seconds')) is not int or any(visible.get(k) != v for k, v in parameters.items()):
        raise ValueError('Same-page parameter readback differs from the adopted task')
    if not all(visible.get(k) is True for k in ('nodes_verified', 'queue_checked', 'downstream_inventory_checked')):
        raise ValueError('Read actual node identities, current queue and any existing downstream first state')
    if visible.get('region_plan_checked') is not True or not _text(visible.get('region_plan_evidence')):
        raise ValueError('Verify adopted regional timing and A/G/R budget; a reference crop is not a reset')
    checks = visible.get('downstream_checks', {})
    if not isinstance(checks, dict) or not set(t['downstream_result_keys']).issubset(checks):
        raise ValueError('Known downstream first-state checks must happen before this submit')
    if any(check.get('qualified') is not True or not _text(check.get('evidence')) for check in checks.values()):
        raise ValueError('Existing downstream first state has an unresolved seam')
    if t['mode'] == 'extend':
        check = t['source_check']
        source = record['tasks'][t['source_task']]
        if not check or not check['qualified'] or source['status'] != 'result' or check['result_key'] != source['result']['key']:
            raise ValueError('Extension waits for the qualified actual native source')
        if record['authorization'].get('review_required') and not _source_usable(record, source):
            raise ValueError('Source review is unresolved or critical; do not propagate it')
        if not t.get('repair_of') and any((x['intent'] and (x['intent'].get('source_key') == check['result_key']
                                or x['intent'].get('source_resource') == source['result']['resource']))
               or (x['mode'] == 'extend' and x['result'] and x['source_check']
                   and x['source_check']['result_key'] == check['result_key'])
               for x in record['tasks'].values()):
            raise ValueError('This native source has already consumed its one extension attempt')
        selection = visible.get('source_input', {})
        if selection.get('key') != check['result_key'] or not _text(selection.get('resource')) or not _text(selection.get('selection_evidence')):
            raise ValueError('Actual source history to selected resource relationship required')
        if t.get('repair_of'):
            if selection.get('native_origin') is not True or selection.get('replaces_task') != t['repair_of']:
                raise ValueError('Replacement extension must visibly reuse native media, never an extension result')
        elif selection.get('native_unextended') is not True:
            raise ValueError('Recheck the visible native source is still unextended before this submit')
        if _interval(selection.get('interval'), _number(source['result']['actual_seconds'], 'Source duration')) != check['interval']:
            raise ValueError('Selected source endpoint/interval changed; recheck the actual endpoint')
        expected = {'resource': selection['resource'], 'interval': selection['interval']}
        if visible.get('video_slot') != expected or visible.get('video_node') != expected:
            raise ValueError('Video slot and real body node must use the same actual input and original interval')
    attempted = sum(row['intent'] is not None for row in record['tasks'].values())
    auth = record['authorization']
    if auth.get('max_submissions') is not None and attempted >= auth['max_submissions']:
        raise ValueError('User submission limit reached')
    quote = deepcopy(visible.get('cost_quote'))
    if quote is not None:
        if not _text(quote.get('evidence')) or not _text(quote.get('currency')):
            raise ValueError('Cost quote needs its visible amount, currency and evidence')
        _number(quote.get('amount'), 'Platform quote')
    if auth.get('max_cost') is not None:
        if not quote or quote['currency'] != auth['currency']:
            raise ValueError('Cannot prove the user cost bound without a comparable platform quote')
        reserved = Decimal(0)
        for row in record['tasks'].values():
            if row['intent']:
                old = row['intent'].get('cost_quote')
                if not old or old['currency'] != auth['currency']:
                    raise ValueError('Prior attempt cost is unknown; do not assume remaining budget')
                reserved += _number(old['amount'], 'Reserved quote')
        if reserved + _number(quote['amount'], 'Platform quote') > _number(auth['max_cost'], 'User cost limit'):
            raise ValueError('Conservative attempt reservations exceed the user cost limit')
    token = hashlib.sha256(json.dumps([record['scope'], task_id, t['prompt_sha256'], now()]).encode()).hexdigest()
    t.update(status='submit_intent', intent=dict(token=token, at=now(), readback=deepcopy(visible),
             source_key=t['source_check']['result_key'] if t['mode'] == 'extend' else None,
             source_resource=source['result']['resource'] if t['mode'] == 'extend' else None,
             cost_quote=quote))
    return token


def _observe(record, task_id, status, evidence, identity, result=None, receipt=None):
    t = record['tasks'][task_id]
    if status not in ('processing', 'result', 'failed', 'unknown') or not _text(evidence):
        raise ValueError('Visible processing/result/failure or unresolved-outcome evidence required')
    _identity(record, t, identity)
    if t['status'] == 'prepared' and not (status == 'result' and result and result.get('adopted_preexisting') is True):
        raise ValueError('No intent: only an explicitly adopted and identified existing result may be attached')
    if t['status'] in ('result', 'failed'):
        if status == t['status'] and (not result or result == t['result']):
            return
        raise ValueError('Terminal outcome changed; do not silently replace an adopted result')
    if status == 'result':
        if not result or not all(_text(result.get(k)) for k in ('key', 'resource', 'identity_evidence')):
            raise ValueError('Exact visible result locator/player resource and identity evidence required')
        if result.get('key_kind') not in ('platform', 'visible_composite'):
            raise ValueError('Use an actual platform ID or a documented visible composite, never invent an ID')
        _identity(record, t, result)
        _number(result.get('actual_seconds'), 'Actual result duration', minimum=Decimal('0.001'))
        if result.get('output_shape', 'unknown') not in ('unknown', 'new_only', 'includes_source'):
            raise ValueError('Record observed output shape or unknown')
        if t['mode'] == 'extend' and not (t['source_check'] and t['source_check']['qualified']):
            raise ValueError('No qualified native-source record for this extension')
        t['result'] = deepcopy(result)
    t.update(status=status, receipt=deepcopy(receipt) if receipt is not None else t['receipt'], observation=evidence)
    if status == 'unknown':
        t['wait_issues'] += 1
        if t['wait_issues'] >= 3:
            t['attention'] = 'Repeated visible lookup failures: user decision, no resubmit'
    else:
        t.update(wait_issues=0, attention=None)



def _root(record, task):
    return record['tasks'][task.get('repair_root', task['id'])]


def _repair_count(record, task):
    root = _root(record, task)
    return root.get('prior_repair_attempts', 0) + sum(
        bool(t.get('repair_of') and t.get('intent')) for t in record['tasks'].values()
        if t.get('repair_root', t['id']) == root['id'])


def _repair_limit(record, task):
    return 3 + sum(decision['additional_attempts'] for decision in _root(record, task).get('repair_decisions', []))


def _repair_decision(record, task_id, additional_attempts, quote, source, evidence):
    task = record['tasks'][task_id]
    root = _root(record, task)
    if record['paused'] or record['authorization']['mode'] != 'generate' or not record['authorization'].get('auto_repair'):
        raise ValueError('Additional repair approval does not override pause or generation authorization')
    if any(t['status'] in ('submit_intent', 'unknown') for t in record['tasks'].values()):
        raise ValueError('Resolve unknown submissions before recording an additional repair decision')
    if task['status'] not in ('result', 'failed') or task.get('superseded_by'):
        raise ValueError('Additional approval must identify the current terminal repair task')
    if type(additional_attempts) is not int or additional_attempts < 1 or not all(_text(v) for v in (quote, source, evidence)):
        raise ValueError('Record the exact positive additional count and direct human quote/message source/evidence')
    if not root.get('history_reconciled'):
        raise ValueError('Reconcile old repair attempts before adding an explicit allowance')
    decisions = root.setdefault('repair_decisions', [])
    # Replaying one human message after a restart must never double its allowance.
    decision_key = hashlib.sha256(json.dumps([root['id'], quote, source], ensure_ascii=False).encode()).hexdigest()
    existing = next((d for d in decisions if d['key'] == decision_key), None)
    if existing:
        if existing['additional_attempts'] != additional_attempts:
            raise ValueError('The same human decision cannot silently change its additional allowance')
        return
    decisions.append(dict(key=decision_key, task_id=task_id, additional_attempts=additional_attempts,
                          quote=quote, source=source, evidence=evidence, at=now()))
    # A direct new repair instruction supersedes adoption for this lineage only;
    # old user-acceptance evidence and all attempted generations are retained.
    record.get('accepted_results', {}).pop(root['id'], None)


def _repair_gate(record, previous, adding=True):
    auth = record['authorization']
    if record['paused'] or auth['mode'] != 'generate' or not auth.get('auto_repair'):
        raise ValueError('Current explicit generation and bounded repair authorization required')
    if any(t['status'] in ('submit_intent', 'unknown') for t in record['tasks'].values()):
        raise ValueError('Unknown submission outcome must be reconciled, never repaired or retried')
    if previous['status'] not in ('result', 'failed'):
        raise ValueError('Only a definite terminal outcome can be repaired')
    if record.get('accepted_results', {}).get(previous.get('repair_root', previous['id'])) or _user_accepted(record, previous):
        raise ValueError('The user adopted this exact result; preserve its known deviations, no automatic repair')
    review = previous.get('review')
    if not review or review['outcome'] != 'critical':
        raise ValueError('Only a reviewed critical problem permits automatic repair')
    if review.get('cause') not in ('prompt', 'model', 'platform_transient') or not _text(review.get('plan')):
        raise ValueError('Repair needs an actionable cause and concrete correction; return the real blocker')
    if not _root(record, previous).get('history_reconciled'):
        raise ValueError('Reconcile legacy and multi-record repair history before automatic repair')
    if _repair_count(record, previous) >= _repair_limit(record, previous):
        raise ValueError('Correction allowance exhausted for this segment lineage; explicit user decision required')
    if adding and previous.get('superseded_by'):
        raise ValueError('An existing replacement already owns this repair lineage')


def _covers_duration(intervals, duration):
    if not intervals:
        return False
    end = Decimal(0)
    for start, stop in sorted((Decimal(a), Decimal(b)) for a, b in intervals):
        if start > end + Decimal('0.01'):
            break
        end = max(end, stop)
    return end >= duration - Decimal('0.01')


def _review_coverage(value, duration, audio_required=False):
    if not isinstance(value, dict) or not isinstance(value.get('limitations'), str):
        raise ValueError('Review records actual visual/audio intervals and known limitations')
    normalized = {'limitations': value['limitations'],
                  'audio_status': 'requested' if audio_required else 'not_requested'}
    complete = {}
    for channel in ('visual', 'audio'):
        intervals = value.get(channel, [] if channel == 'audio' and not audio_required else None)
        if not isinstance(intervals, list):
            raise ValueError('Actual inspected visual and audio interval lists required')
        normalized[channel] = [_interval(item, duration) for item in intervals]
        complete[channel] = _covers_duration(normalized[channel], duration)
    # These flags mean actual viewing/listening interval coverage, never inferred
    # full viewing from a transcript or sampled frame sequence.
    normalized['complete'] = complete
    blockers = value.get('blocking_unknowns', [])
    if not isinstance(blockers, list) or not all(_text(item) for item in blockers):
        raise ValueError('Blocking unknowns must list the actual unresolved judgments')
    normalized['blocking_unknowns'] = deepcopy(blockers)
    methods = 'visual_method' in value or 'audio_method' in value
    normalized['methods_declared'] = methods
    assessed = deepcopy(complete)
    if methods:
        if value.get('visual_method') not in ('overview', 'continuous', 'shot_sequence') or (audio_required and value.get('audio_method') not in ('listening', 'transcript_and_spotcheck')):
            raise ValueError('Declare supported actual visual and audio assessment methods')
        if 'blocking_unknowns' not in value:
            raise ValueError('Method-based assessment must explicitly record blocking unknowns')
        normalized.update(visual_method=value['visual_method'],
                          audio_method=value.get('audio_method', 'not_requested'))
        if value['visual_method'] == 'overview':
            normalized['assessment_scope'] = 'obvious_visual_errors'
            normalized['visual_evidence'] = value.get('visual_evidence', '')
            assessed['visual'] = bool(normalized['visual'] and _text(normalized['visual_evidence']))
        if value['visual_method'] == 'shot_sequence':
            shots = value.get('shot_coverage', [])
            if not isinstance(shots, list):
                raise ValueError('Shot-sequence assessment needs the actual shot interval list')
            normalized['shot_coverage'] = []
            for shot in shots:
                if not isinstance(shot, dict):
                    raise ValueError('Each shot coverage entry must be an object')
                interval = _interval(shot.get('interval'), duration)
                points = shot.get('frame_points')
                if not isinstance(points, list) or not points or not _text(shot.get('evidence')):
                    raise ValueError('Every real shot needs inspected frame times and its evidence')
                checked_points = []
                for point in points:
                    moment = _number(point, 'Inspected frame time')
                    if not Decimal(interval[0]) <= moment <= Decimal(interval[1]) or not any(Decimal(a) <= moment <= Decimal(b) for a, b in normalized['visual']):
                        raise ValueError('Each shot frame must lie in its shot and actual inspected visual window')
                    checked_points.append(str(moment))
                normalized['shot_coverage'].append(dict(interval=interval, frame_points=checked_points, evidence=shot['evidence']))
            normalized['visual_evidence'] = value.get('visual_evidence', '')
            assessed['visual'] = bool(_text(normalized['visual_evidence']) and _covers_duration([shot['interval'] for shot in normalized['shot_coverage']], duration))
        if audio_required and value.get('audio_method') == 'transcript_and_spotcheck':
            transcript = value.get('transcript_coverage', [])
            if not isinstance(transcript, list):
                raise ValueError('Transcript comparison coverage must be separate from actual listening')
            normalized['transcript_coverage'] = [_interval(item, duration) for item in transcript]
            normalized['audio_evidence'] = value.get('audio_evidence', '')
            assessed['audio'] = bool(_text(normalized['audio_evidence']) and normalized['audio'] and _covers_duration(normalized['transcript_coverage'], duration))
    normalized['assessment_complete'] = assessed
    return normalized


def _review(record, task_id, outcome, evidence, result_key=None, issue=None, cause=None, plan=None, coverage=None):
    t = record['tasks'][task_id]
    if t['status'] not in ('result', 'failed') or outcome not in ('usable', 'minor', 'critical', 'unknown') or not _text(evidence):
        raise ValueError('Review needs a definite result/failure and actual inspection evidence')
    if t['status'] == 'result' and result_key != t['result']['key']:
        raise ValueError('Review must identify the exact actual result')
    if t['status'] == 'failed' and outcome not in ('critical', 'unknown'):
        raise ValueError('A failed generation cannot be adopted as usable media')
    if outcome == 'critical' and (not _text(issue) or cause not in ('prompt', 'model', 'platform_transient', 'asset', 'access', 'balance', 'unknown')):
        raise ValueError('Critical review needs a concrete issue and failure attribution')
    inspected = None
    if t['status'] == 'result' and record['authorization'].get('review_required'):
        audio_required = record['authorization'].get('review_audio', False)
        inspected = _review_coverage(coverage, _number(t['result']['actual_seconds'], 'Actual duration'), audio_required)
        required_channels = ('visual', 'audio') if audio_required else ('visual',)
        if outcome in ('usable', 'minor') and (not all(inspected['assessment_complete'][channel] for channel in required_channels) or inspected['blocking_unknowns'] or (not inspected['methods_declared'] and inspected['limitations'].strip())):
            raise ValueError('Missing assessment coverage or blocking unknowns remain unresolved; method limitations alone are not blockers')
    value = dict(outcome=outcome, evidence=evidence, result_key=result_key, issue=issue,
                 cause=cause, plan=plan, coverage=inspected, at=now())
    t.setdefault('reviews', []).append(value)
    t['review'] = value


def _repair(record, task_id, replacement, evidence, dialogue_unchanged):
    previous = record['tasks'][task_id]
    _repair_gate(record, previous)
    if not _text(evidence) or dialogue_unchanged is not True:
        raise ValueError('Record the correction and verify every spoken line remains authorized')
    # Reuse all original task validation. An extension's source is validated
    # separately against the existing canonical journal below.
    spec = deepcopy(replacement)
    if spec.get('id') in record['tasks']:
        raise ValueError('A repair is a new immutable task, never a reset of an old attempt')
    if spec.get('mode') != previous['mode'] or spec.get('seconds') != previous['seconds']:
        raise ValueError('Automatic repair preserves adopted mode and duration; structural changes need a decision')
    for name in ('model', 'resolution', 'aspect_ratio'):
        if name in previous:
            if spec.get(name, previous[name]) != previous[name]:
                raise ValueError('Automatic repair preserves adopted model, resolution and aspect ratio')
            spec[name] = previous[name]
    source = spec.pop('source_task', None)
    if previous['mode'] == 'extend' and source != previous['source_task']:
        raise ValueError('Replacement extension uses the same native source; never extend an extension result')
    if previous['mode'] == 'native' and source:
        raise ValueError('Native repair cannot carry a source')
    validation = deepcopy(spec)
    validation['mode'] = 'native'
    t = create(record['scope'], record['authorization'], [validation], record['simulation'])['tasks'][spec['id']]
    t['mode'] = previous['mode']
    if source:
        if record['tasks'][source]['mode'] != 'native':
            raise ValueError('No extension of an extension')
        t['source_task'] = source
    t.update(repair_root=_root(record, previous)['id'], repair_of=task_id,
             repair_evidence=evidence, dialogue_unchanged=True)
    # Preserve known seams even when a caller omits them from the new spec.
    t['downstream_result_keys'] = list(dict.fromkeys(previous['downstream_result_keys'] + t['downstream_result_keys']))
    record['tasks'][t['id']] = t
    previous['superseded_by'] = t['id']


def _rebind_source(record, task_id, source_task, current, evidence):
    _same_snapshot(record, current, evidence)
    t = record['tasks'][task_id]
    source = record['tasks'][source_task]
    old = record['tasks'].get(t.get('source_task'))
    if record['paused'] or t['mode'] != 'extend' or t['status'] != 'prepared' or t['intent']:
        raise ValueError('Only an unsubmitted extension can bind its repaired native source')
    if not old or source['mode'] != 'native' or source['status'] != 'result' or _root(record, old)['id'] != _root(record, source)['id']:
        raise ValueError('Rebind only within the same native-source repair lineage')
    if not _source_usable(record, source):
        raise ValueError('Replacement native source needs actual review or explicit user acceptance')
    t.update(source_task=source_task, source_check=None, rebind_evidence=evidence)


def _history_reconcile(record, task_id, prior_repair_attempts, evidence):
    if any(t['status'] in ('submit_intent', 'unknown') for t in record['tasks'].values()):
        raise ValueError('Resolve every outstanding submission before marking repair history reconciled')
    root = _root(record, record['tasks'][task_id])
    if type(prior_repair_attempts) is not int or prior_repair_attempts < root.get('prior_repair_attempts', 0) or not _text(evidence):
        raise ValueError('Legacy repair count must be nonnegative, monotonic and supported by reconciled records')
    root.update(prior_repair_attempts=prior_repair_attempts, history_reconciled=True,
                history_evidence=evidence)


def next_actions(record):
    if record['paused']:
        return [{'action': 'reconcile_user_takeover', 'reason': 'Stop writes; read existing cards, assets and queue'}]
    unresolved = [(key, t) for key, t in record['tasks'].items()
                  if t['status'] in ('submit_intent', 'unknown')]
    if unresolved:
        key, t = next(((key, t) for key, t in unresolved if t['attention']), unresolved[0])
        if t['attention']:
            return [dict(task=key, action='user_decision', reason=t['attention'])]
        return [dict(task=key, action='lookup_or_wait', wait_seconds=30,
                     reason='Reconcile unresolved click before any new submission; no retry')]
    processing = [t for t in record['tasks'].values() if t['status'] == 'processing']
    actions = []
    for key, t in record['tasks'].items():
        selected = record.get('accepted_results', {}).get(t.get('repair_root', key))
        # A human can adopt an older result without erasing newer attempts.
        # In-flight newer tasks still receive normal observation; no cancellation.
        if selected and selected != key and t['status'] in ('prepared', 'result', 'failed'):
            continue
        if t.get('superseded_by') and selected != key:
            continue
        source = record['tasks'].get(t.get('source_task'))
        source_selected = record.get('accepted_results', {}).get(source.get('repair_root', source['id'])) if source else None
        if source_selected and source_selected != source['id'] and (t.get('intent') or t.get('result')):
            actions.append(dict(task=key, action='review_existing_downstream',
                                reason='User adopted a different source result; reconcile this already-submitted downstream, never implicitly remake it'))
        if record['authorization'].get('review_required') and t['status'] in ('result', 'failed'):
            if _user_accepted(record, t):
                continue
            review = t.get('review')
            if not review:
                actions.append(dict(task=key, action='review_result'))
            elif review['outcome'] == 'unknown':
                actions.append(dict(task=key, action='inspect_result', reason='Missing review evidence is not permission to regenerate'))
            elif review['outcome'] == 'critical':
                try:
                    _repair_gate(record, t)
                except ValueError as error:
                    actions.append(dict(task=key, action='user_decision', reason=str(error)))
                else:
                    actions.append(dict(task=key, action='prepare_bounded_repair', remaining=_repair_limit(record, t)-_repair_count(record, t)))
            continue
        if t['status'] == 'processing':
            actions.append(dict(task=key, action='lookup_or_wait', wait_seconds=30,
                                reason='Only normal visible queue/history proves outcome; no retry'))
        if t['status'] == 'failed':
            actions.append(dict(task=key, action='user_decision', reason='No automatic failed retry'))
        elif t['status'] == 'prepared':
            if t.get('repair_of') and _user_accepted(record, record['tasks'][t['repair_of']]):
                continue
            if processing and (t['mode'] != 'native' or any(row['mode'] != 'native' for row in processing)):
                continue
            source = record['tasks'].get(t.get('source_task'))
            if source and source['status'] == 'failed':
                actions.append(dict(task=key, action='blocked_by_source', reason='Source failed; user decision'))
            elif source and source['status'] != 'result':
                actions.append(dict(task=key, action='wait_for_source'))
            elif source and ((source_selected and source_selected != source['id']) or (source.get('superseded_by') and not _user_accepted(record, source))):
                actions.append(dict(task=key, action='rebind_repaired_source', reason='Review the repaired native result, then rebind this unsubmitted extension'))
            elif source and record['authorization'].get('review_required') and not _source_usable(record, source):
                actions.append(dict(task=key, action='blocked_by_source', reason='Actual source review is pending or has a critical problem'))
            elif source and t['source_check'] and not t['source_check']['qualified']:
                actions.append(dict(task=key, action='user_decision', reason='Unqualified source; do not propagate errors'))
            elif source and not t['source_check']:
                actions.append(dict(task=key, action='check_source'))
            else:
                actions.append(dict(task=key, action='prepare_only' if record['authorization']['mode'] == 'prepare'
                                    else 'readback_then_one_submit'))
    return actions or [{'action': 'record_results_complete'}]


@contextmanager
def editing(path):
    """OS-owned advisory lock: process death releases it, including on Windows."""
    lock = Path(str(path) + '.lock')
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    # Keep the lock inode: unlinking it races another process acquiring the lock.


def save(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        # Close before replace for Windows; a sharing/permission error grants no click.
        os.replace(temporary, path)
        if os.name != 'nt':
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


def read(path):
    record = json.loads(Path(path).read_text(encoding='utf-8'))
    if record.get('schema') not in (1, 2):
        raise ValueError('Unsupported journal schema; reconcile before using another version')
    if record['schema'] == 1:
        # Compatibility is read-only until the next explicit event is saved.
        record['schema'] = 2
        for key, t in record['tasks'].items():
            t.update(review=None, reviews=[], repair_root=key, repair_of=None,
                     superseded_by=None, prior_repair_attempts=0, history_reconciled=False)
    return record


def apply_event(path, event):
    """Persist one host observation. Only a newly persisted intent grants one click.

    No-event reads, restarts and repeated intent calls never reproduce a permission.
    The host must consume it immediately on the already-verified same page; if
    interrupted before/after the click, treat the intent as unresolved, even if
    that conservatively means a click might never have occurred.
    """
    path = Path(path)
    token = None
    with editing(path):
        op, data = event['op'], event.get('data', {})
        if op == 'init':
            if path.exists():
                raise ValueError('Existing record: read and resume; never reinitialize')
            record = create(**data)
        else:
            record = read(path)
            if op == 'authorize':
                _same_snapshot(record, data['current'], data['evidence'])
                record['authorization'] = _authorization(data['authorization'])
            elif op == 'intent':
                token = _begin_submission(record, **data)
            elif op == 'observe':
                _observe(record, **data)
            elif op == 'repair_decision':
                _repair_decision(record, **data)
            elif op == 'user_accept':
                _user_accept(record, **data)
            elif op == 'review':
                _review(record, **data)
            elif op == 'repair':
                _repair(record, **data)
            elif op == 'rebind_source':
                _rebind_source(record, **data)
            elif op == 'history_reconcile':
                _history_reconcile(record, **data)
            elif op == 'source_check':
                _source_check(record, **data)
            elif op == 'pause':
                if not _text(data.get('reason')):
                    raise ValueError('Record the human takeover/change instruction')
                record.update(paused=True, pause_reason=data['reason'])
            elif op == 'resume':
                _same_snapshot(record, data['current'], data['evidence'])
                record['paused'] = False
            else:
                raise ValueError('Unknown journal event')
        record['updated_at'] = now()
        save(path, record)
        if read(path) != record:
            raise OSError('Journal readback differs; no click permission')
    response = {'execution': 'SIMULATION_ONLY' if record['simulation'] else 'HOST_BROWSER',
                'actions': next_actions(record)}
    if token:
        response['one_use_click_permission'] = dict(task=data['task_id'], intent_token=token,
            simulation=record['simulation'], note='One click now, not a platform receipt; never replay')
    return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--event', type=Path, help='Internal event JSON made by the host, never required from the user')
    args = parser.parse_args()
    if args.event:
        response = apply_event(args.record, json.loads(args.event.read_text(encoding='utf-8')))
    else:
        record = read(args.record)
        response = {'execution': 'SIMULATION_ONLY' if record['simulation'] else 'HOST_BROWSER',
                    'actions': next_actions(record)}
    print(json.dumps(response, ensure_ascii=True))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise SystemExit(str(error))
