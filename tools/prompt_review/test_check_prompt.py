import unittest
from check_prompt import inspect

def sample(shots=((0,2),(2,3.4),(3.4,5.6)), sound='局部1.0–5.0秒｜甲→乙｜“A complete sentence.”｜一次连续发声', prose=None):
    end=shots[-1][1]
    body=f'【生成任务】\n生成{end}秒，共{len(shots)}个真实镜头。\n【声音时序】\n{sound}\n【镜头设计】\n'
    for i,(a,b) in enumerate(shots,1):
        body+=f'镜头{i:02}【{a}–{b}秒｜紧特写】\n'+(prose or {}).get(i,'甲在画外持续发声，乙收回伸出的手。')+'\n'
    return '制作设置：原轨由后期编排。\n```text\n'+body+'```'

class PromptChecks(unittest.TestCase):
    def codes(self,text): return {x['code'] for x in inspect(text)['errors']}
    def test_continuous_speech_across_three_shots(self):
        self.assertTrue(inspect(sample())['structural_pass'])
        self.assertEqual(inspect(sample())['visual_quality'],'not_assessed')
    def test_long_shot_rejected(self):
        self.assertIn('shot_too_long',self.codes(sample(((0,5.6),))))
    def test_gap_rejected(self):
        self.assertIn('coverage_gap_or_overlap',self.codes(sample(((0,2),(2.1,3.4),(3.4,5.6)))))
    def test_overlap_rejected(self):
        self.assertIn('coverage_gap_or_overlap',self.codes(sample(((0,2),(1.9,3.4),(3.4,5.6)))))
    def test_opening_in_wrong_shot(self):
        self.assertIn('opening_outside_shot',self.codes(sample(prose={2:'现场对白：按声音时序1.0秒开口。'})))
    def test_legal_opening_and_offscreen_continuation(self):
        self.assertTrue(inspect(sample(prose={1:'现场对白：局部1.0秒开口。',2:'甲画外持续同句，乙安静听着。'}))['structural_pass'])
    def test_postproduction_in_body_not_settings(self):
        self.assertNotIn('postproduction_in_body',self.codes(sample()))
        self.assertIn('postproduction_in_body',self.codes(sample(prose={1:'P1092旁白由后期编排。'})))
    def test_hidden_cut_requires_review(self):
        r=inspect(sample(prose={1:'切到乙再回到甲。'}))
        self.assertIn('inspect_hidden_cut',{x['code'] for x in r['warnings']})
    def test_count_and_end(self):
        self.assertIn('shot_count',self.codes(sample().replace('共3个','共9个')))
        self.assertIn('end_coverage',self.codes(sample().replace('生成5.6秒','生成6秒')))
    def test_no_fake_point_eight_minimum(self):
        self.assertTrue(inspect(sample(((0,.6),(.6,3),(3,5.6))))['structural_pass'])
    def test_missing_body_fails_closed(self):
        self.assertFalse(inspect('只有摘要')['structural_pass'])
    def test_other_explicit_upper_limit(self):
        self.assertTrue(inspect(sample(((0,5.6),)),6)['structural_pass'])
    def test_missing_count_rejected(self):
        self.assertIn('shot_count_missing',self.codes(sample().replace('共3个真实镜头','若干镜头')))
    def test_short_count_form(self):
        self.assertTrue(inspect(sample().replace('共3个真实镜头','共3镜'))['structural_pass'])
    def test_invalid_limit(self):
        with self.assertRaises(ValueError): inspect(sample(),float('nan'))

if __name__=='__main__': unittest.main()
