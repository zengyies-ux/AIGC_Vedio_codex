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


if __name__ == '__main__':
    unittest.main()
