import unittest
from native_postcopy_contract_ysm_265 import decoded_delta,fixed_predicates
class PostcopyProofTests(unittest.TestCase):
    def test_pinned_scalar(self):self.assertEqual(decoded_delta(0xe1aab868,0xb564a469),0xffe3312a)
    def test_shift_sign_exhaustive(self):self.assertEqual(fixed_predicates()['js_all_65536_dx_sign_flags'],[0])
    def test_btc_mask(self):
        p=fixed_predicates();self.assertEqual((p['jae_bit'],p['jae_old_bit'],p['jae_taken']),(3,0,True))
    def test_signed_branch(self):
        p=fixed_predicates();self.assertEqual((p['sbb_dl_result'],p['sbb_sf'],p['sbb_of'],p['jl_taken']),(234,1,0,True))
    def test_carry_chain(self):
        p=fixed_predicates();self.assertEqual((p['cx_after_shift'],p['adc_r11_carry'],p['sil_shift_carry']),(0x138,0,0))
    def test_rotate_boundary_reference(self):
        for word in (0,1,0x7fffffff,0x80000000,0xffffffff,0x55555555):
            for key in (0,0xffffffff,0xb564a469):
                s=f'{((word^key)+1)&0xffffffff:032b}';s=s[1:]+s[0];s=f'{(int(s,2)-1)&0xffffffff:032b}';s=s[-1]+s[:-1];v=(-int(s,2))&0xffffffff
                ref=int.from_bytes(v.to_bytes(4,'little'),'big');self.assertEqual(decoded_delta(word,key),(ref-1)&0xffffffff)
if __name__=='__main__':unittest.main()
