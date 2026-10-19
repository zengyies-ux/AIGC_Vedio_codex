"""Controlled SIMULATION ONLY: no real browser, media, paid submission or UI claim."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import journal


SCRIPT = Path(journal.__file__).resolve()
SCOPE = {'project': '受控模拟', 'episode': '18', 'target_url': 'https://example.invalid/project/ep18'}
AUTH = {'mode': 'generate', 'quote': 'SIMULATION: complete this episode native and one extension',
        'source': 'controlled test fixture, never a production authorization'}


def task(key, mode='native', **extra):
    return dict(dict(id=key, card='SIMULATED_CARD_' + (extra.get('source_task') or key),
                prompt_version='adopted-v1', prompt_sha256=hashlib.sha256(key.encode()).hexdigest(),
                mode=mode, seconds=25 if mode == 'extend' else 30,
                assets=[{'semantic': '人物1', 'resource': 'SIMULATED_ASSET_1'}]), **extra)


class JournalBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='网页 回执_')
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / '中文目录' / '执行记录.json'

    def event(self, op, **data):
        return journal.apply_event(self.path, {'op': op, 'data': data})

    def init(self, authorization=None, tasks=None, simulation=True):
        return self.event('init', scope=SCOPE, authorization=deepcopy(authorization if authorization is not None else AUTH),
                          tasks=tasks or [task('N'), task('E', 'extend', source_task='N')], simulation=simulation)

    def record(self):
        return journal.read(self.path)

    def identity(self, key):
        t = self.record()['tasks'][key]
        return {**SCOPE, **{k: t[k] for k in ('card', 'prompt_version', 'prompt_sha256', 'mode')}}

    def visible(self, key):
        t = self.record()['tasks'][key]
        value = {**self.identity(key), **{k: t[k] for k in ('model', 'resolution', 'seconds')},
                 'nodes_verified': True, 'queue_checked': True, 'downstream_inventory_checked': True,
                 'region_plan_checked': True, 'region_plan_evidence': 'SIMULATION: adopted regional timing and A/G/R, no crop reset',
                 'downstream_checks': {k: {'qualified': True, 'evidence': 'SIMULATION: verified existing first state'}
                                       for k in t['downstream_result_keys']}}
        if t['mode'] == 'extend':
            check = t['source_check']
            value.update(source_input={'key': check['result_key'], 'resource': 'SIMULATED_CROPPED_RESOURCE',
                                       'interval': check['interval'], 'native_unextended': True,
                                       'selection_evidence': 'SIMULATION: visible original→selection→resource'},
                         video_slot={'resource': 'SIMULATED_CROPPED_RESOURCE', 'interval': check['interval']},
                         video_node={'resource': 'SIMULATED_CROPPED_RESOURCE', 'interval': check['interval']})
        return value

    def intent(self, key, visible=None):
        return self.event('intent', task_id=key, visible=visible or self.visible(key), live=False)

    def result(self, key, **extra):
        return {**self.identity(key), 'key': 'SIMULATED_RESULT_' + key, 'key_kind': 'visible_composite',
                'resource': 'SIMULATED_MEDIA_' + key, 'identity_evidence': 'SIMULATION: matching history/body/player',
                'actual_seconds': 30.048 if key == 'N' else 25.024, 'extension_count': 0, **extra}

    def observe(self, key, status, **extra):
        return self.event('observe', task_id=key, status=status, identity=self.identity(key),
                          evidence='SIMULATION: normal visible queue/history/player observation', **extra)

    def complete_native(self, **result_extra):
        self.intent('N')
        self.observe('N', 'processing', receipt={'visible_task_id': 'SIMULATION_ONLY_QUEUE_ITEM'})
        self.observe('N', 'result', result=self.result('N', **result_extra))

    def check_source(self, key='E', **extra):
        data=dict(task_id=key, result_key='SIMULATED_RESULT_N', qualified=True,
                  interval=[0.62, 30.048], evidence='SIMULATION: native end identity, pose, space and contact checked',
                  unextended=True)
        data.update(extra)
        return self.event('source_check', **data)

    def test_ascii_console_json_preserves_unicode_task_in_non_utf8_pipe(self):
        import os
        event=Path(self.directory.name)/'event.json'
        event.write_text(json.dumps({'op':'init','data':dict(scope=SCOPE,authorization={},tasks=[task('原生')],simulation=True)}),encoding='utf-8')
        env=dict(os.environ,PYTHONIOENCODING='cp1252',PYTHONUTF8='0')
        completed=subprocess.run([sys.executable,str(SCRIPT),'--record',str(self.path),'--event',str(event)],capture_output=True,env=env)
        self.assertEqual(completed.returncode,0,completed.stderr)
        response=json.loads(completed.stdout.decode('ascii'))
        self.assertEqual(response['actions'][0]['task'],'原生')

    def test_native_wait_qualified_source_extension_result_and_durable_one_click_each(self):
        start = self.init()
        self.assertEqual(start['execution'], 'SIMULATION_ONLY')
        self.assertIn({'task': 'E', 'action': 'wait_for_source'}, start['actions'])
        native = self.intent('N')
        permission = native['one_use_click_permission']
        self.assertTrue(permission['simulation'])
        self.assertEqual(self.record()['tasks']['N']['intent']['token'], permission['intent_token'])
        self.assertEqual(self.observe('N', 'processing')['actions'][0]['wait_seconds'], 30)
        after_native = self.observe('N', 'result', result=self.result('N'))
        self.assertEqual(after_native['actions'], [{'task': 'E', 'action': 'check_source'}])
        self.check_source()
        extension = self.intent('E')
        self.assertNotEqual(permission['intent_token'], extension['one_use_click_permission']['intent_token'])
        self.observe('E', 'processing')
        end = self.observe('E', 'result', result=self.result('E', output_shape='new_only'))
        self.assertEqual(end['actions'], [{'action': 'record_results_complete'}])
        self.assertEqual(sum(t['intent'] is not None for t in self.record()['tasks'].values()), 2)
        self.assertEqual(self.record()['tasks']['E']['result']['output_shape'], 'new_only')

    def test_prepare_is_default_never_returns_submit_permission(self):
        out = self.init(authorization={})
        self.assertEqual(out['actions'][0]['action'], 'prepare_only')
        with self.assertRaisesRegex(ValueError, 'Prepare-only'):
            self.intent('N')
        self.assertIsNone(self.record()['tasks']['N']['intent'])

    def test_explicit_whole_episode_authorization_upgrades_prepare_without_per_segment_approval(self):
        self.init(authorization={})
        self.event('authorize', authorization=AUTH, current=journal.snapshot(self.record()),
                   evidence='SIMULATION: unchanged target/body/cards and queue reconciled')
        self.complete_native()
        self.check_source()
        self.assertIn('one_use_click_permission', self.intent('E'))

    def test_unknown_click_receipt_restart_never_replays_permission_or_submit(self):
        self.init()
        self.intent('N')  # Crash could be either before or after the single host click.
        reopened = self.record()
        self.assertEqual(journal.next_actions(reopened)[0]['action'], 'lookup_or_wait')
        with self.assertRaisesRegex(ValueError, 'never retry'):
            self.intent('N')
        self.observe('N', 'unknown')
        with self.assertRaisesRegex(ValueError, 'never retry'):
            self.intent('N')
        with self.assertRaisesRegex(ValueError, 'active submission'):
            self.event('intent', task_id='E', visible=self.identity('E'), live=False)
        self.assertEqual(self.record()['tasks']['N']['status'], 'unknown')

    def test_confirmed_native_processing_allows_next_native_in_same_record(self):
        self.init(tasks=[task('A'), task('B')])
        self.intent('A')
        with self.assertRaisesRegex(ValueError, 'active submission'):
            self.intent('B')
        self.observe('A', 'processing')
        actions = journal.next_actions(self.record())
        self.assertTrue(any(x['task'] == 'A' and x['action'] == 'lookup_or_wait' for x in actions))
        self.assertTrue(any(x['task'] == 'B' and x['action'] == 'readback_then_one_submit' for x in actions))
        self.assertIn('one_use_click_permission', self.intent('B'))
        self.observe('B', 'processing')
        self.assertEqual(sum(t['intent'] is not None for t in self.record()['tasks'].values()), 2)
        with self.assertRaisesRegex(ValueError, 'never retry'):
            self.intent('A')

    def test_unknown_native_blocks_other_native_and_its_action(self):
        self.init(tasks=[task('A'), task('B')])
        self.intent('A')
        self.observe('A', 'processing')
        self.observe('A', 'unknown')
        with self.assertRaisesRegex(ValueError, 'active submission'):
            self.intent('B')
        self.assertFalse(any(x['action'] == 'readback_then_one_submit'
                             for x in journal.next_actions(self.record())))

    def test_parallel_native_submission_limit_remains_episode_wide(self):
        auth = dict(AUTH, max_submissions=1)
        self.init(authorization=auth, tasks=[task('A'), task('B')])
        self.intent('A')
        self.observe('A', 'processing')
        with self.assertRaisesRegex(ValueError, 'submission limit'):
            self.intent('B')

    def test_parallel_native_cost_limit_counts_processing_job(self):
        self.init(authorization=dict(AUTH, max_cost=100, currency='credits'),
                  tasks=[task('A'), task('B')])
        first = self.visible('A')
        first['cost_quote'] = dict(amount=60, currency='credits', evidence='SIMULATION quote')
        self.intent('A', first)
        self.observe('A', 'processing')
        second = self.visible('B')
        second['cost_quote'] = dict(amount=50, currency='credits', evidence='SIMULATION quote')
        with self.assertRaisesRegex(ValueError, 'cost limit'):
            self.intent('B', second)
        self.assertIsNone(self.record()['tasks']['B']['intent'])

    def test_processing_native_does_not_unlock_extension_submission(self):
        self.init(tasks=[task('A'), task('N'), task('E', 'extend', source_task='N')])
        self.complete_native()
        self.check_source()
        self.intent('A')
        self.observe('A', 'processing')
        with self.assertRaisesRegex(ValueError, 'active submission'):
            self.intent('E')
        self.assertFalse(any(x.get('task') == 'E' and x['action'] == 'readback_then_one_submit'
                             for x in journal.next_actions(self.record())))

    def test_processing_extension_keeps_next_native_waiting(self):
        self.init(tasks=[task('N'), task('E', 'extend', source_task='N'), task('B')])
        self.complete_native()
        self.check_source()
        self.intent('E')
        self.observe('E', 'processing')
        with self.assertRaisesRegex(ValueError, 'active submission'):
            self.intent('B')
        self.assertFalse(any(x.get('task') == 'B' and x['action'] == 'readback_then_one_submit'
                             for x in journal.next_actions(self.record())))

    def test_finite_unknown_lookup_exceptions_return_decision_without_resubmission(self):
        self.init()
        self.intent('N')
        for _ in range(3):
            response = self.observe('N', 'unknown')
        self.assertEqual(response['actions'][0]['action'], 'user_decision')
        self.assertNotIn('one_use_click_permission', response)
        # A later unambiguous result can still be reconciled without another attempt.
        self.observe('N', 'result', result=self.result('N'))
        self.assertEqual(self.record()['tasks']['N']['status'], 'result')

    def test_normal_waiting_is_not_assumed_complete_after_elapsed_time(self):
        self.init()
        self.intent('N')
        for _ in range(12):
            response = self.observe('N', 'processing')
        self.assertEqual(response['actions'][0]['action'], 'lookup_or_wait')
        self.assertIsNone(self.record()['tasks']['N']['result'])

    def test_pause_restart_reconciles_actual_mapping_without_rebuild_upload_or_resubmit(self):
        self.init()
        self.intent('N')
        before = journal.snapshot(self.record())
        self.event('pause', reason='SIMULATION: human takes over')
        self.assertEqual(journal.next_actions(self.record())[0]['action'], 'reconcile_user_takeover')
        with self.assertRaisesRegex(ValueError, 'takeover'):
            self.intent('N')
        wrong = deepcopy(before)
        wrong['tasks']['N']['card'] = 'ANOTHER_CARD'
        with self.assertRaisesRegex(ValueError, 'Reconcile'):
            self.event('resume', current=wrong, evidence='SIMULATION: other card')
        response = self.event('resume', current=before, evidence='SIMULATION: read existing cards/assets and queue')
        self.assertEqual(response['actions'][0]['action'], 'lookup_or_wait')
        self.assertEqual(self.record()['tasks']['N']['assets'], [{'semantic': '人物1', 'resource': 'SIMULATED_ASSET_1'}])
        with self.assertRaisesRegex(ValueError, 'Existing record'):
            self.init()
        with self.assertRaisesRegex(ValueError, 'never retry'):
            self.intent('N')

    def test_changed_target_version_body_mode_or_parameters_reject_old_adoption(self):
        self.init()
        for field in ('target_url', 'episode', 'card', 'prompt_version', 'prompt_sha256', 'mode', 'seconds', 'model', 'resolution'):
            with self.subTest(field=field):
                visible = self.visible('N')
                visible[field] = 'CHANGED'
                with self.assertRaises(ValueError):
                    self.intent('N', visible)
        self.assertIsNone(self.record()['tasks']['N']['intent'])
        changed = journal.snapshot(self.record())
        changed['tasks']['N']['prompt_version'] = 'adopted-v2'
        with self.assertRaisesRegex(ValueError, 'Reconcile'):
            self.event('authorize', authorization=AUTH, current=changed, evidence='SIMULATION: revised body')

    def test_existing_downstream_first_state_is_checked_before_upstream_submit(self):
        self.init(tasks=[task('N', downstream_result_keys=['SIMULATED_EXISTING_DOWNSTREAM'])])
        visible = self.visible('N')
        visible['downstream_checks'] = {}
        with self.assertRaisesRegex(ValueError, 'before this submit'):
            self.intent('N', visible)
        visible = self.visible('N')
        visible['downstream_checks']['SIMULATED_EXISTING_DOWNSTREAM']['qualified'] = False
        with self.assertRaisesRegex(ValueError, 'unresolved seam'):
            self.intent('N', visible)
        self.assertIn('one_use_click_permission', self.intent('N'))

    def test_failed_submission_never_automatically_retries_and_failed_source_blocks_extension(self):
        self.init()
        self.intent('N')
        response = self.observe('N', 'failed')
        self.assertEqual(response['actions'][0]['action'], 'user_decision')
        self.assertEqual(response['actions'][1]['action'], 'blocked_by_source')
        with self.assertRaisesRegex(ValueError, 'never retry'):
            self.intent('N')

    def test_extension_waits_for_true_qualified_unextended_source(self):
        self.init()
        with self.assertRaisesRegex(ValueError, 'completed native source'):
            self.check_source()
        self.complete_native()
        bad = dict(task_id='E', result_key='SIMULATED_RESULT_N', qualified=False,
                   interval=[0.62, 30.048], evidence='SIMULATION: wrong contact at end', unextended=True)
        response = self.event('source_check', **bad)
        self.assertEqual(response['actions'][0]['action'], 'user_decision')
        with self.assertRaisesRegex(ValueError, 'qualified actual native source'):
            self.intent('E')
        bad['qualified'] = 'false'
        with self.assertRaisesRegex(ValueError, 'Explicit'):
            self.event('source_check', **bad)

    def test_already_extended_or_unknown_history_cannot_become_source(self):
        self.init()
        self.complete_native(extension_count=1)
        with self.assertRaisesRegex(ValueError, 'already extended'):
            self.check_source()

    def test_video_slot_node_and_interval_match_for_original_or_cropped_resource(self):
        self.init()
        self.complete_native()
        self.check_source()
        visible = self.visible('E')
        visible['video_node']['interval'] = ['0.62', '29.0']
        with self.assertRaisesRegex(ValueError, 'same actual input'):
            self.intent('E', visible)
        # A nonzero interval with the SAME original URL is also valid.
        visible = self.visible('E')
        for where in ('source_input', 'video_slot', 'video_node'):
            visible[where]['resource'] = 'SIMULATED_MEDIA_N'
        self.assertIn('one_use_click_permission', self.intent('E', visible))

    def test_new_cropped_url_is_accepted_only_with_visible_selection_relationship(self):
        self.init()
        self.complete_native()
        self.check_source()
        visible = self.visible('E')
        visible['source_input']['selection_evidence'] = ''
        with self.assertRaisesRegex(ValueError, 'relationship'):
            self.intent('E', visible)
        self.assertIn('one_use_click_permission', self.intent('E'))

    def test_one_extension_attempt_survives_failure_and_no_extension_of_extension(self):
        self.init(tasks=[task('N'), task('E', 'extend', source_task='N'), task('E2', 'extend', source_task='N')])
        self.complete_native()
        self.check_source()
        self.intent('E')
        self.observe('E', 'failed')
        self.check_source('E2')
        with self.assertRaisesRegex(ValueError, 'one extension attempt'):
            self.intent('E2')
        with self.assertRaisesRegex(ValueError, 'no extension chain'):
            journal.create(SCOPE, AUTH, [task('N'), task('E', 'extend', source_task='N'),
                                       task('E2', 'extend', source_task='E')], simulation=True)

    def test_preexisting_adopted_extension_and_external_extension_block_another_attempt(self):
        self.init(tasks=[task('N'), task('E', 'extend', source_task='N'), task('E2', 'extend', source_task='N')])
        self.complete_native()
        self.check_source()
        visible = self.visible('E')
        visible['source_input']['native_unextended'] = False
        with self.assertRaisesRegex(ValueError, 'still unextended'):
            self.intent('E', visible)
        self.observe('E', 'result', result=self.result('E', adopted_preexisting=True))
        self.check_source('E2')
        with self.assertRaisesRegex(ValueError, 'one extension attempt'):
            self.intent('E2')

    def test_cross_episode_independent_native_does_not_wait_for_prior_result(self):
        self.init(tasks=[task('N')])
        self.assertIn('one_use_click_permission', self.intent('N'))
        with self.assertRaisesRegex(ValueError, 'previous-episode'):
            journal.create(SCOPE, AUTH, [task('N', source_task='PREVIOUS_EPISODE')], simulation=True)

    def test_adopted_region_and_budget_evidence_required_before_submit(self):
        self.init()
        for field,value in [('region_plan_checked',False),('region_plan_evidence','')]:
            visible=self.visible('N');visible[field]=value
            with self.assertRaisesRegex(ValueError,'regional timing'):
                self.intent('N',visible)
        self.assertIsNone(self.record()['tasks']['N']['intent'])

    def test_legitimate_adopted_region_transition_not_rejected_by_total_duration(self):
        # Duration alone does not identify one continuous region. The adopted
        # plan can move to another acting area within an extension.
        self.init(tasks=[task('N',seconds=40),task('E','extend',source_task='N')])
        self.complete_native(actual_seconds=40.048)
        self.check_source(interval=[.1,40.048])
        visible=self.visible('E')
        visible['region_plan_evidence']='SIMULATION: adopted transition at 54s; both regions <=60s; full A/G/R unchanged by crop'
        self.assertIn('one_use_click_permission',self.intent('E',visible))
        self.assertEqual(self.record()['tasks']['N']['result']['actual_seconds'],40.048)

    def test_submission_and_conservative_quote_limits_are_enforced_without_inventing_budget(self):
        auth = {**AUTH, 'max_submissions': 1}
        self.init(authorization=auth)
        self.complete_native()
        self.check_source()
        with self.assertRaisesRegex(ValueError, 'submission limit'):
            self.intent('E')
        self.assertNotIn('max_cost', self.record()['authorization'])
        other = Path(self.directory.name) / 'cost.json'
        journal.apply_event(other, {'op': 'init', 'data': dict(scope=SCOPE, authorization={**AUTH, 'max_cost': '20', 'currency': 'credits'},
                                                               tasks=[task('N')], simulation=True)})
        visible = self.visible('N')
        visible['cost_quote'] = {'amount': '21', 'currency': 'credits', 'evidence': 'SIMULATION: visible quote'}
        with self.assertRaisesRegex(ValueError, 'cost limit'):
            journal.apply_event(other, {'op': 'intent', 'data': dict(task_id='N', visible=visible, live=False)})

    def test_simulation_record_never_grants_live_permission(self):
        self.init()
        with self.assertRaisesRegex(ValueError, 'never be interchanged'):
            self.event('intent', task_id='N', visible=self.visible('N'), live=True)

    def test_result_identity_and_actual_player_duration_required_not_last_thumbnail(self):
        self.init()
        self.intent('N')
        wrong = self.result('N')
        wrong['prompt_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'differs'):
            self.observe('N', 'result', result=wrong)
        wrong = self.result('N', actual_seconds=None)
        with self.assertRaisesRegex(ValueError, 'finite number'):
            self.observe('N', 'result', result=wrong)
        with self.assertRaisesRegex(ValueError, 'Exact visible result'):
            self.observe('N', 'result', result={'key': 'LAST_THUMBNAIL'})

    def test_explicit_adopted_existing_native_can_resume_extension_without_resubmission(self):
        self.init()
        self.observe('N', 'result', result=self.result('N', adopted_preexisting=True))
        self.assertIsNone(self.record()['tasks']['N']['intent'])
        self.check_source()
        self.assertIn('one_use_click_permission', self.intent('E'))

    def test_atomic_save_failure_preserves_old_record_and_never_grants_permission(self):
        self.init()
        before = self.path.read_bytes()
        with patch.object(journal.os, 'replace', side_effect=OSError('SIMULATION: Windows file occupied')):
            with self.assertRaisesRegex(OSError, 'file occupied'):
                self.intent('N')
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(list(self.path.parent.glob('*.tmp')))
        self.assertIsNone(self.record()['tasks']['N']['intent'])

    def test_save_readback_failure_leaves_unresolved_intent_without_replay(self):
        self.init()
        visible = self.visible('N')
        original_read = journal.read
        calls = 0
        def broken_readback(path):
            nonlocal calls
            calls += 1
            value = original_read(path)
            if calls == 2:
                value['updated_at'] = 'SIMULATION: corrupt readback'
            return value
        with patch.object(journal, 'read', side_effect=broken_readback):
            with self.assertRaisesRegex(OSError, 'no click permission'):
                self.event('intent', task_id='N', visible=visible, live=False)
        self.assertEqual(self.record()['tasks']['N']['status'], 'submit_intent')
        with self.assertRaisesRegex(ValueError, 'never retry'):
            self.intent('N')

    def test_cli_read_unicode_path_never_reissues_permission_and_competing_writer_is_blocked(self):
        self.init()
        self.intent('N')
        out = subprocess.run([sys.executable, str(SCRIPT), '--record', str(self.path)], capture_output=True, text=True, check=True)
        value = json.loads(out.stdout)
        self.assertEqual(value['execution'], 'SIMULATION_ONLY')
        self.assertNotIn('one_use_click_permission', value)
        event = self.path.parent / '事件.json'
        event.write_text(json.dumps({'op': 'pause', 'data': {'reason': 'SIMULATION takeover'}}, ensure_ascii=False), encoding='utf-8')
        with journal.editing(self.path):
            out = subprocess.run([sys.executable, str(SCRIPT), '--record', str(self.path), '--event', str(event)],
                                 capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertFalse(self.record()['paused'])
        # The OS lock is released without manual stale-lock removal.
        self.event('pause', reason='SIMULATION: next process can acquire the lock')



class ReviewRepairTests(unittest.TestCase):
    # Share fixtures without duplicating the existing behavior tests.
    setUp = JournalBehaviorTests.setUp
    event = JournalBehaviorTests.event
    init = JournalBehaviorTests.init
    record = JournalBehaviorTests.record
    identity = JournalBehaviorTests.identity
    visible = JournalBehaviorTests.visible
    intent = JournalBehaviorTests.intent
    result = JournalBehaviorTests.result
    observe = JournalBehaviorTests.observe
    complete_native = JournalBehaviorTests.complete_native
    check_source = JournalBehaviorTests.check_source
    def auto_init(self, tasks=None):
        return self.init(authorization={**AUTH, 'review_required': True, 'auto_repair': True, 'review_audio': True}, tasks=tasks)

    def review(self, key, outcome='critical', **extra):
        data = dict(task_id=key, outcome=outcome, evidence='SIMULATION: inspected actual result and sound',
                    result_key=self.record()['tasks'][key].get('result', {}).get('key') if self.record()['tasks'][key].get('result') else None)
        result = self.record()['tasks'][key].get('result')
        if result:
            data['coverage'] = {'visual': [[0, result['actual_seconds']]], 'audio': [[0, result['actual_seconds']]], 'limitations': ''}
        if outcome == 'critical':
            data.update(issue='wrong shoulder injury', cause='prompt', plan='Correct injury placement; preserve dialogue')
        data.update(extra)
        return self.event('review', **data)

    def repair(self, previous, key, **extra):
        old = self.record()['tasks'][previous]
        replacement = task(key, mode=old['mode'], seconds=old['seconds'],
                           **({'source_task': old['source_task']} if old['mode'] == 'extend' else {}))
        return self.event('repair', task_id=previous, replacement=replacement,
                          evidence='SIMULATION: local correction, adopted event and sound unchanged',
                          dialogue_unchanged=True, **extra)

    def test_auto_review_is_required_and_minor_is_not_regenerated(self):
        self.auto_init(tasks=[task('N')])
        self.complete_native()
        self.assertEqual(journal.next_actions(self.record())[0]['action'], 'review_result')
        self.review('N', 'minor')
        self.assertEqual(journal.next_actions(self.record()), [{'action': 'record_results_complete'}])
        with self.assertRaises(ValueError): self.repair('N', 'N2')

    def test_three_repairs_persist_across_versions_issue_names_and_restarts(self):
        self.auto_init(tasks=[task('N')]); self.complete_native(); self.review('N')
        parent = 'N'
        for number in range(1, 4):
            key = 'N' + str(number)
            self.repair(parent, key)
            self.assertEqual(journal._repair_count(self.record(), self.record()['tasks'][key]), number-1)
            self.intent(key)
            self.observe(key, 'result', result=self.result(key))
            self.review(key, issue='renamed problem ' + str(number))
            self.assertEqual(journal._repair_count(journal.read(self.path), self.record()['tasks'][key]), number)
            parent = key
        with self.assertRaises(ValueError): self.repair(parent, 'N4')
        self.assertEqual(journal.next_actions(self.record())[0]['action'], 'user_decision')
        self.assertEqual(len(self.record()['tasks']), 4)

    def test_unknown_outcome_and_unknown_review_never_repair(self):
        self.auto_init(tasks=[task('N'), task('Other')]); self.complete_native(); self.review('N')
        self.intent('Other'); self.observe('Other', 'unknown')
        with self.assertRaises(ValueError): self.repair('N', 'N2')
        with self.assertRaises(ValueError): self.repair('Other', 'Other2')
        with self.assertRaises(ValueError): self.event('history_reconcile', task_id='N', prior_repair_attempts=0, evidence='SIMULATION: pending unknown cannot be cleared')
        self.observe('Other', 'result', result=self.result('Other')); self.review('Other', 'unknown')
        with self.assertRaises(ValueError): self.repair('Other', 'Other2')

    def test_no_repair_without_explicit_authorization_or_dialogue_preservation(self):
        self.init(tasks=[task('N')]); self.complete_native(); self.review('N')
        with self.assertRaises(ValueError): self.repair('N', 'N2')
        self.event('authorize', authorization={**AUTH, 'review_required': True, 'auto_repair': True},
                   current=journal.snapshot(self.record()), evidence='SIMULATION: explicit bounded repair authorization')
        with self.assertRaises(ValueError):
            self.event('repair', task_id='N', replacement=task('N2'), evidence='SIMULATION', dialogue_unchanged=False)

    def test_blocker_attribution_does_not_trigger_repeated_generation(self):
        self.auto_init(tasks=[task('N')]); self.complete_native()
        for cause in ('asset', 'access', 'balance', 'unknown'):
            self.review('N', cause=cause)
            with self.assertRaises(ValueError): self.repair('N', 'N2')
        self.assertEqual(journal.next_actions(self.record())[0]['action'], 'user_decision')

    def test_failed_platform_submission_can_repair_only_after_attributed_review(self):
        self.auto_init(tasks=[task('N')]); self.intent('N'); self.observe('N', 'failed')
        with self.assertRaises(ValueError): self.repair('N', 'N2')
        self.review('N', cause='platform_transient', plan='Visible transient error cleared; resubmit same adopted request')
        self.repair('N', 'N2'); self.intent('N2')
        self.assertEqual(self.record()['tasks']['N']['status'], 'failed')

    def test_extension_repair_reuses_native_but_never_extension_result(self):
        self.auto_init(); self.complete_native(); self.review('N', 'usable'); self.check_source()
        self.intent('E'); self.observe('E', 'result', result=self.result('E', extension_count=1)); self.review('E')
        self.repair('E', 'E2'); self.check_source('E2')
        visible = self.visible('E2')
        with self.assertRaises(ValueError): self.intent('E2', visible)
        visible['source_input'].update(native_origin=True, replaces_task='E')
        self.intent('E2', visible)
        self.assertEqual(self.record()['tasks']['E2']['source_task'], 'N')
        self.assertEqual(journal._repair_count(self.record(), self.record()['tasks']['E2']), 1)
        with self.assertRaises(ValueError):
            self.event('repair', task_id='E', replacement=task('Bad', 'extend', source_task='E'), evidence='SIMULATION', dialogue_unchanged=True)

    def test_repaired_native_rebinds_only_unsubmitted_extension_and_rechecks_source(self):
        self.auto_init(); self.complete_native(); self.review('N'); self.repair('N', 'N2')
        self.intent('N2'); self.observe('N2', 'result', result=self.result('N2')); self.review('N2', 'usable')
        self.event('rebind_source', task_id='E', source_task='N2', current=journal.snapshot(self.record()), evidence='SIMULATION: adopted new qualified native')
        self.assertEqual(self.record()['tasks']['E']['source_task'], 'N2')
        self.assertIsNone(self.record()['tasks']['E']['source_check'])
        unbound = self.visible('N2'); unbound.update(self.identity('E'), seconds=25)
        with self.assertRaises(ValueError): self.intent('E', unbound)
        self.event('source_check', task_id='E', result_key='SIMULATED_RESULT_N2', qualified=True,
                   interval=[0,25], evidence='SIMULATION: actual repaired endpoint', unextended=True)
        self.intent('E')

    def test_legacy_reconciliation_prevents_reset_and_counts_prior_logs(self):
        self.init(tasks=[task('N')]); self.complete_native()
        legacy=self.record(); legacy['schema']=1
        journal.save(self.path, legacy)
        self.event('authorize', authorization={**AUTH, 'review_required': True, 'auto_repair': True},
                   current=journal.snapshot(self.record()), evidence='SIMULATION: reviewed current target')
        self.review('N')
        with self.assertRaises(ValueError): self.repair('N', 'N2')
        self.event('history_reconcile', task_id='N', prior_repair_attempts=2, evidence='SIMULATION: old records A/B contain two correction intents, deduplicated')
        self.repair('N', 'N2'); self.intent('N2'); self.observe('N2', 'result', result=self.result('N2')); self.review('N2')
        with self.assertRaises(ValueError): self.repair('N2', 'N3')
        with self.assertRaises(ValueError): self.event('history_reconcile', task_id='N', prior_repair_attempts=0, evidence='reset')

    def test_repair_intent_save_failure_never_consumes_or_grants_click(self):
        self.auto_init(tasks=[task('N')]); self.complete_native(); self.review('N'); self.repair('N','N2')
        with patch.object(journal, 'save', side_effect=OSError('disk full')):
            with self.assertRaises(OSError): self.intent('N2')
        self.assertEqual(journal._repair_count(self.record(), self.record()['tasks']['N2']), 0)
        self.assertIsNone(self.record()['tasks']['N2']['intent'])

    def test_review_cannot_adopt_wrong_result_or_failed_media(self):
        self.auto_init(tasks=[task('N')]); self.complete_native()
        with self.assertRaises(ValueError): self.review('N', 'usable', result_key='other-result')

    def test_reviewed_source_required_before_extension(self):
        self.auto_init(); self.complete_native()
        with self.assertRaises(ValueError): self.check_source()
        self.review('N', 'usable'); self.check_source()
        self.review('N')
        with self.assertRaises(ValueError): self.intent('E')

    def test_review_coverage_cannot_label_sampled_frames_or_missing_audio_fully_usable(self):
        self.auto_init(tasks=[task('N')]); self.complete_native()
        partial = {'visual': [[0, 1], [29, 30.048]], 'audio': [], 'limitations': 'Only two frame ranges; audio not inspected'}
        with self.assertRaises(ValueError): self.review('N', 'usable', coverage=partial)
        with self.assertRaises(ValueError): self.review('N', 'minor', coverage=partial)
        self.review('N', 'unknown', coverage=partial)
        self.assertFalse(self.record()['tasks']['N']['review']['coverage']['complete']['visual'])
        self.assertEqual(journal.next_actions(self.record())[0]['action'], 'inspect_result')
        with self.assertRaises(ValueError): self.repair('N','N2')
        self.review('N', 'usable')

    def test_replacement_extension_accepts_native_with_prior_candidate_history(self):
        self.auto_init(); self.complete_native(); self.review('N','usable'); self.check_source()
        self.intent('E'); self.observe('E','result',result=self.result('E',extension_count=1)); self.review('E')
        self.repair('E','E2')
        # Simulate reconciled visible original-native history having one branch.
        state=self.record(); state['tasks']['N']['result']['extension_count']=1; journal.save(self.path,state)
        self.check_source('E2')
        visible=self.visible('E2'); visible['source_input'].update(native_origin=True,replaces_task='E')
        self.intent('E2',visible)
        self.assertEqual(self.record()['tasks']['E2']['mode'],'extend')
        self.assertEqual(self.record()['tasks']['N']['mode'],'native')

    def test_repair_cost_budget_counts_all_original_and_repair_attempts(self):
        self.init(authorization={**AUTH,'review_required':True,'auto_repair':True,'max_cost':15,'currency':'credits'},tasks=[task('N')])
        visible=self.visible('N'); visible['cost_quote']={'amount':10,'currency':'credits','evidence':'SIMULATION visible quote'}
        self.intent('N',visible); self.observe('N','result',result=self.result('N')); self.review('N'); self.repair('N','N2')
        visible=self.visible('N2'); visible['cost_quote']={'amount':10,'currency':'credits','evidence':'SIMULATION visible quote'}
        with self.assertRaises(ValueError): self.intent('N2',visible)
        self.assertEqual(journal._repair_count(self.record(),self.record()['tasks']['N2']),0)

    def accept(self, key, **extra):
        data=dict(task_id=key, result_key=self.record()['tasks'][key]['result']['key'],
                  quote='SIMULATION HUMAN: I watched this video, accept the deviation and continue',
                  source='SIMULATION: direct user message, never agent opinion',
                  evidence='SIMULATION: user identifies this exact visible result')
        data.update(extra)
        return self.event('user_accept', **data)

    def test_user_accepts_critical_result_without_erasing_defect_or_review(self):
        self.auto_init(); self.complete_native(); self.review('N')
        old=self.record()['tasks']['N']['review']
        self.accept('N')
        self.assertEqual(self.record()['tasks']['N']['review'], old)
        self.assertEqual(self.record()['tasks']['N']['review']['outcome'], 'critical')
        with self.assertRaises(ValueError): self.repair('N','N2')
        self.assertIn({'task':'E','action':'check_source'},journal.next_actions(self.record()))
        self.check_source(); self.intent('E')

    def test_user_accepts_partial_ai_review_without_fabricating_full_coverage(self):
        self.auto_init(); self.complete_native()
        partial={'visual':[[29,30.048]],'audio':[],'limitations':'AI checked endpoint only; user watched and accepts full result'}
        self.review('N','unknown',coverage=partial)
        self.accept('N'); self.check_source(); self.intent('E')
        review=self.record()['tasks']['N']['review']
        self.assertEqual(review['outcome'],'unknown')
        self.assertFalse(review['coverage']['complete']['audio'])
        self.assertEqual(review['coverage']['audio'],[])

    def test_user_accept_rejects_wrong_result_missing_quote_and_pending_submission(self):
        self.auto_init(); self.complete_native(); self.review('N')
        with self.assertRaises(ValueError): self.accept('N',result_key='different-result')
        with self.assertRaises(ValueError): self.accept('N',quote='')
        with self.assertRaises(ValueError):
            self.event('user_accept',task_id='E',result_key='not-produced',quote='SIMULATION',source='SIMULATION human',evidence='SIMULATION')
        self.assertNotIn('user_acceptance',self.record()['tasks']['N'])

    def test_user_accept_does_not_override_unknown_submission_or_unqualified_local_seam(self):
        self.auto_init(tasks=[task('N'),task('E','extend',source_task='N'),task('Other')])
        self.complete_native(); self.review('N'); self.accept('N')
        self.check_source(qualified=False)
        with self.assertRaises(ValueError): self.intent('E')
        self.check_source(); self.intent('Other'); self.observe('Other','unknown')
        self.accept('N')
        with self.assertRaises(ValueError): self.intent('E')
        self.assertEqual(self.record()['tasks']['Other']['status'],'unknown')

    def test_user_accepted_repaired_native_can_rebind_but_extension_cannot_be_source(self):
        self.auto_init(); self.complete_native(); self.review('N'); self.repair('N','N2')
        self.intent('N2'); self.observe('N2','result',result=self.result('N2')); self.review('N2'); self.accept('N2')
        self.event('rebind_source',task_id='E',source_task='N2',current=journal.snapshot(self.record()),evidence='SIMULATION accepted actual repaired native')
        self.assertIsNone(self.record()['tasks']['E']['source_check'])
        self.accept('N'); self.accept('N2')
        with self.assertRaises(ValueError):
            self.event('rebind_source',task_id='E',source_task='N',current=journal.snapshot(self.record()),evidence='SIMULATION stale previous acceptance')
        self.event('source_check',task_id='E',result_key='SIMULATED_RESULT_N2',qualified=True,interval=[0,25],evidence='SIMULATION actual endpoint',unextended=True)
        self.intent('E'); self.observe('E','result',result=self.result('E',extension_count=1)); self.review('E'); self.accept('E')
        with self.assertRaises(ValueError):
            self.event('rebind_source',task_id='E',source_task='E',current=journal.snapshot(self.record()),evidence='SIMULATION cannot extend extension')

    def test_user_accepts_older_result_stops_prepared_repair_without_erasing_attempts(self):
        self.auto_init(tasks=[task('N')]); self.complete_native(); self.review('N'); self.repair('N','N2')
        self.accept('N')
        self.assertEqual(self.record()['tasks']['N']['superseded_by'],'N2')
        self.assertEqual(self.record()['tasks']['N2']['status'],'prepared')
        self.assertEqual(self.record()['accepted_results']['N'],'N')
        with self.assertRaises(ValueError): self.intent('N2')
        self.assertEqual(journal.next_actions(self.record()),[{'action':'record_results_complete'}])

    def test_user_accepts_older_result_keeps_newer_processing_and_unknown_click(self):
        self.auto_init(tasks=[task('N')]); self.complete_native(); self.review('N'); self.repair('N','N2')
        self.intent('N2'); self.observe('N2','processing'); self.accept('N')
        self.assertEqual(self.record()['tasks']['N2']['status'],'processing')
        self.assertEqual(journal._repair_count(self.record(),self.record()['tasks']['N']),1)
        self.assertEqual(journal.next_actions(self.record())[0]['action'],'lookup_or_wait')
        self.observe('N2','unknown'); self.accept('N')
        self.assertEqual(journal.next_actions(self.record())[0]['action'],'lookup_or_wait')
        self.assertEqual(self.record()['tasks']['N2']['status'],'unknown')

    def test_old_result_acceptance_reports_existing_downstream_without_rewrite(self):
        self.auto_init(); self.complete_native(); self.review('N'); self.repair('N','N2')
        self.intent('N2'); self.observe('N2','result',result=self.result('N2')); self.review('N2','usable')
        self.event('rebind_source',task_id='E',source_task='N2',current=journal.snapshot(self.record()),evidence='SIMULATION repaired source')
        self.event('source_check',task_id='E',result_key='SIMULATED_RESULT_N2',qualified=True,interval=[0,25],evidence='SIMULATION endpoint',unextended=True)
        self.intent('E'); self.observe('E','processing'); self.accept('N')
        actions=journal.next_actions(self.record())
        self.assertTrue(any(item['action']=='review_existing_downstream' for item in actions))
        self.assertTrue(any(item['action']=='lookup_or_wait' for item in actions))
        self.assertEqual(self.record()['tasks']['E']['source_task'],'N2')
        self.assertEqual(self.record()['tasks']['E']['status'],'processing')

    def test_explicit_user_adds_one_repair_after_three_without_reset_or_replay(self):
        self.auto_init(tasks=[task('N')]); self.complete_native(); self.review('N')
        previous='N'
        for number in range(1,4):
            key='N'+str(number); self.repair(previous,key); self.intent(key)
            self.observe(key,'result',result=self.result(key)); self.review(key); previous=key
        with self.assertRaises(ValueError): self.repair('N3','N4')
        decision=dict(task_id='N3',additional_attempts=1,quote='SIMULATION HUMAN: fix this one more time',
                      source='SIMULATION direct user message 2',evidence='SIMULATION exact additional count one')
        self.event('repair_decision',**decision)
        self.event('repair_decision',**decision)
        self.assertEqual(journal._repair_limit(self.record(),self.record()['tasks']['N3']),4)
        self.assertEqual(journal._repair_count(self.record(),self.record()['tasks']['N3']),3)
        self.repair('N3','N4'); self.intent('N4'); self.observe('N4','result',result=self.result('N4')); self.review('N4')
        with self.assertRaises(ValueError): self.repair('N4','N5')
        self.assertEqual(journal._repair_count(self.record(),self.record()['tasks']['N4']),4)

    def test_additional_repair_decision_rejects_missing_human_source_or_unknown_submission(self):
        self.auto_init(tasks=[task('N'),task('Other')]); self.complete_native(); self.review('N')
        decision=dict(task_id='N',additional_attempts=1,quote='SIMULATION HUMAN: one more',source='',evidence='SIMULATION')
        with self.assertRaises(ValueError): self.event('repair_decision',**decision)
        decision['source']='SIMULATION direct user message 3'
        decision['additional_attempts']=True
        with self.assertRaises(ValueError): self.event('repair_decision',**decision)
        decision['additional_attempts']=1
        self.intent('Other'); self.observe('Other','unknown')
        with self.assertRaises(ValueError): self.event('repair_decision',**decision)
        self.assertEqual(journal._repair_limit(self.record(),self.record()['tasks']['N']),3)

    def method_coverage(self):
        return dict(visual=[[0,0.1],[8,8.1],[10,10.1],[18,18.1],[20,20.1],[30,30.048]],
                    audio=[[12,13]], limitations='Frame sequence, not every frame; transcript plus local listening, not full-track listening',
                    visual_method='shot_sequence', audio_method='transcript_and_spotcheck', blocking_unknowns=[],
                    shot_coverage=[dict(interval=[0,10],frame_points=[0.05,8.05],evidence='SIMULATION actual shot 1/cut at 10; action windows checked'),
                                   dict(interval=[10,20],frame_points=[10.05,18.05],evidence='SIMULATION actual shot 2/cut at 20; contact checked'),
                                   dict(interval=[20,30.048],frame_points=[20.05,30.02],evidence='SIMULATION actual shot 3; end seam checked')],
                    visual_evidence='SIMULATION full-range scan, real cut inventory, every shot covered; action/seam windows densified at listed times',
                    transcript_coverage=[[0,30.048]],
                    audio_evidence='SIMULATION complete generated-track transcript compared to authorized lines; speaker and 12-13s doubt checked by listening')

    def test_explicit_sampling_and_transcript_methods_can_adopt_without_false_full_listening(self):
        self.auto_init(tasks=[task('N')]); self.complete_native()
        self.review('N','usable',coverage=self.method_coverage())
        value=self.record()['tasks']['N']['review']['coverage']
        self.assertFalse(value['complete']['visual']); self.assertFalse(value['complete']['audio'])
        self.assertTrue(all(value['assessment_complete'].values()))
        self.assertEqual(value['audio'],[['12','13']])
        self.assertTrue(value['limitations'])
        self.review('N','minor',coverage=self.method_coverage())

    def test_method_blocking_unknowns_cannot_be_adopted(self):
        self.auto_init(tasks=[task('N')]); self.complete_native()
        coverage=self.method_coverage(); coverage['blocking_unknowns']=['Speaker identity at 12s is unresolved']
        with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)
        with self.assertRaises(ValueError): self.review('N','minor',coverage=coverage)
        self.review('N','unknown',coverage=coverage)

    def test_sampling_requires_full_shot_and_transcript_coverage_with_actual_points(self):
        self.auto_init(tasks=[task('N')]); self.complete_native()
        for field in ('shot_coverage','transcript_coverage'):
            coverage=self.method_coverage(); coverage[field]=[]
            with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)
        coverage=self.method_coverage(); coverage['shot_coverage'][0]['frame_points']=[5]
        with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)
        coverage=self.method_coverage(); coverage['visual_evidence']=''
        with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)
        coverage=self.method_coverage(); coverage['audio']=[]
        with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)

    def test_empty_blocking_list_cannot_bypass_legacy_limitations_or_continuous_gaps(self):
        self.auto_init(tasks=[task('N')]); self.complete_native()
        coverage=dict(visual=[[0,30.048]],audio=[[0,30.048]],limitations='Unspecified inspection limitations',blocking_unknowns=[])
        with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)
        coverage.update(visual_method='continuous',audio_method='listening')
        self.review('N','usable',coverage=coverage)
        coverage['visual']=[[0,1],[29,30.048]]
        with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)
        coverage=self.method_coverage(); del coverage['blocking_unknowns']
        with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)

    def test_default_visual_review_allows_source_without_generated_audio_audit(self):
        self.init(authorization={**AUTH, 'review_required': True, 'auto_repair': True})
        self.complete_native()
        self.review('N', 'usable', coverage=dict(visual=[[0,30.048]], visual_method='continuous',
                    blocking_unknowns=[], limitations='Generated audio not reviewed by user policy'))
        review=self.record()['tasks']['N']['review']['coverage']
        self.assertEqual(review['audio'], [])
        self.assertEqual(review['audio_status'], 'not_requested')
        self.assertFalse(review['complete']['audio'])
        self.check_source()
        self.intent('E')

    def test_visual_only_sampling_needs_no_audio_or_transcript_but_still_needs_visual_coverage(self):
        self.init(authorization={**AUTH, 'review_required': True, 'auto_repair': True}, tasks=[task('N')])
        self.complete_native()
        coverage=self.method_coverage()
        for field in ('audio','audio_method','transcript_coverage','audio_evidence'): coverage.pop(field)
        self.review('N','usable',coverage=coverage)
        coverage['shot_coverage']=[]
        with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)
        coverage=self.method_coverage(); coverage['blocking_unknowns']=['Visual identity unresolved']
        with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)

    def test_explicit_audio_audit_remains_opt_in_and_must_not_fake_success(self):
        self.auto_init(tasks=[task('N')]); self.complete_native()
        coverage=dict(visual=[[0,30.048]],audio=[],visual_method='continuous',audio_method='listening',
                      blocking_unknowns=[],limitations='Audio unavailable')
        with self.assertRaises(ValueError): self.review('N','usable',coverage=coverage)

    def test_resume_audio_only_unknown_with_new_visual_policy_preserves_old_evidence(self):
        self.auto_init(); self.complete_native()
        coverage=dict(visual=[[0,30.048]],audio=[],visual_method='continuous',audio_method='listening',
                      blocking_unknowns=['Audio not heard'],limitations='Audio unavailable')
        self.review('N','unknown',coverage=coverage)
        self.event('authorize', authorization={**AUTH,'review_required':True,'auto_repair':True,'review_audio':False},
                   current=journal.snapshot(self.record()),evidence='SIMULATION direct user says skip generated audio review')
        coverage['blocking_unknowns']=[]
        self.review('N','usable',coverage=coverage)
        rows=self.record()['tasks']['N']['reviews']
        self.assertEqual(rows[-2]['outcome'],'unknown')
        self.assertFalse(rows[-1]['coverage']['complete']['audio'])
        self.check_source(); self.intent('E')

    def test_audio_policy_requires_a_real_boolean(self):
        with self.assertRaises(ValueError):
            self.init(authorization={**AUTH,'review_audio':'false'})

    def test_structure_parameter_change_and_duplicate_repair_rejected(self):
        self.auto_init(tasks=[task('N')]); self.complete_native(); self.review('N')
        with self.assertRaises(ValueError):
            self.event('repair', task_id='N', replacement=task('N2', seconds=20), evidence='SIMULATION', dialogue_unchanged=True)
        with self.assertRaises(ValueError):
            self.event('repair', task_id='N', replacement=task('N2', resolution='1080P'), evidence='SIMULATION', dialogue_unchanged=True)
        self.repair('N', 'N2')
        with self.assertRaises(ValueError): self.repair('N', 'N3')


if __name__ == '__main__':
    unittest.main()
