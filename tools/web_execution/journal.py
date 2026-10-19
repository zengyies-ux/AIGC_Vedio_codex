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
            'model', 'resolution', 'source_task', 'aspect_ratio')


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
                 wait_issues=0, attention=None)
        rows[t['id']] = t
    if not rows:
        raise ValueError('At least one adopted task required')
    for t in rows.values():
        if t['mode'] == 'extend':
            source = rows.get(t.get('source_task'))
            if not source or source['mode'] != 'native':
                raise ValueError('Extension needs one native source in this episode; no extension chain')
    return dict(schema=1, scope=deepcopy(scope), authorization=_authorization(authorization),
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


def _source_check(record, task_id, result_key, qualified, interval, evidence, unextended):
    t = record['tasks'][task_id]
    source = record['tasks'].get(t.get('source_task'))
    if t['mode'] != 'extend' or not source or source['status'] != 'result' or source['result']['key'] != result_key:
        raise ValueError('Check the exact completed native source first')
    if type(qualified) is not bool or unextended is not True or not _text(evidence):
        raise ValueError('Explicit local endpoint/body/space evidence and an unextended-source check required')
    if record['paused'] or t['intent'] is not None:
        raise ValueError('Cannot alter source while paused or after submission intent')
    result = source['result']
    if type(result.get('extension_count')) is not int or result['extension_count'] != 0:
        raise ValueError('The actual native source is already extended or its extension history is unknown')
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
        if any((x['intent'] and (x['intent'].get('source_key') == check['result_key']
                                or x['intent'].get('source_resource') == source['result']['resource']))
               or (x['mode'] == 'extend' and x['result'] and x['source_check']
                   and x['source_check']['result_key'] == check['result_key'])
               for x in record['tasks'].values()):
            raise ValueError('This native source has already consumed its one extension attempt')
        selection = visible.get('source_input', {})
        if selection.get('key') != check['result_key'] or not _text(selection.get('resource')) or not _text(selection.get('selection_evidence')):
            raise ValueError('Actual source history to selected resource relationship required')
        if selection.get('native_unextended') is not True:
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
        if t['status'] == 'processing':
            actions.append(dict(task=key, action='lookup_or_wait', wait_seconds=30,
                                reason='Only normal visible queue/history proves outcome; no retry'))
        if t['status'] == 'failed':
            actions.append(dict(task=key, action='user_decision', reason='No automatic failed retry'))
        elif t['status'] == 'prepared':
            if processing and (t['mode'] != 'native' or any(row['mode'] != 'native' for row in processing)):
                continue
            source = record['tasks'].get(t.get('source_task'))
            if source and source['status'] == 'failed':
                actions.append(dict(task=key, action='blocked_by_source', reason='Source failed; user decision'))
            elif source and source['status'] != 'result':
                actions.append(dict(task=key, action='wait_for_source'))
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
    if record.get('schema') != 1:
        raise ValueError('Unsupported journal schema; reconcile before using another version')
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
