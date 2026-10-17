#!/usr/bin/env python3
"""Three additional fixed local flag proofs and bounded prefixes; no native execution or state emulation."""
import argparse,hashlib,json,struct,zipfile
from pathlib import Path
from native_image_metadata_ysm_265 import SHA,IMAGES
from native_export_backing_ysm_265 import regions,data_at,backing
from native_load_parity_proof_ysm_265 import capture as parity_capture
import native_linux_prefix_frontier_ysm_265 as frontier
SEGMENTS=[(0x13b4244,'4c89642418688b3913be66c14c24056a0f8866d9f5ff'),(0x1311bc0,'48894c240056b99b73a8dc488d0df4ffffffbe803a2f3148f7d6660fbaf62f48bec61b310100000000e84b67c1ff'),(0xf28339,'0f82d1353700'),(0x10bf95f,'41ba0126bdd6410fbafa22488d3de8ffffff0f8335ec2100')]
def bit_carry(value,index,width):return (value>>(index%width))&1
def inherited_sign(word):return bool(word&0x8000)
def prove(parts,previous_word):
 if len(parts)!=len(SEGMENTS) or any(b.hex()!=expected for b,(_,expected) in zip(parts,SEGMENTS)):raise ValueError('Changed fixed proof sequence')
 sign=inherited_sign(previous_word);sign_target=SEGMENTS[0][0]+len(parts[0])+struct.unpack_from('<i',parts[0],18)[0]
 imm=struct.unpack_from('<I',parts[1],19)[0];low=(~imm)&0xffff;btr_cf=bit_carry(low,parts[1][30],16)
 call_target=SEGMENTS[1][0]+len(parts[1])+struct.unpack_from('<i',parts[1],42)[0];jb_target=SEGMENTS[2][0]+6+struct.unpack_from('<i',parts[2],2)[0]
 btc_imm=struct.unpack_from('<I',parts[3],2)[0];btc_cf=bit_carry(btc_imm,parts[3][10],32);jae_target=SEGMENTS[3][0]+len(parts[3])+struct.unpack_from('<i',parts[3],20)[0]
 return dict(sign=dict(inherited_dec_word=previous_word,sign_flag=sign,ror_preserves_sf=True,branch_address=0x13b4254,taken=sign,target_address=sign_target),btr=dict(mov_esi_constant=imm,si_after_not=low,encoded_bit_index=parts[1][30],effective_bit_index=parts[1][30]%16,carry_flag=btr_cf,near_call_target=call_target,branch_address=0xf28339,taken=bool(btr_cf),target_address=jb_target),btc=dict(mov_r10d_constant=btc_imm,encoded_bit_index=parts[3][10],effective_bit_index=parts[3][10]%32,carry_flag=btc_cf,branch_address=0x10bf971,taken=not bool(btc_cf),target_address=jae_target))
def capture(jar):
 prior=parity_capture(jar)
 with zipfile.ZipFile(jar) as z:b=z.read('META-INF/native/libysm-core.so')
 if hashlib.sha256(b).hexdigest()!=dict(IMAGES)['libysm-core.so']:raise ValueError('Wrong image')
 rs=regions(b);parts=[data_at(b,rs,a,len(bytes.fromhex(h))) for a,h in SEGMENTS];p=prove(parts,prior['proof']['word_after'])
 if not all(v['taken'] for v in p.values()):raise ValueError('Expected local proof did not hold')
 if [p[k]['target_address'] for k in ['sign','btr','btc']]!=[0x1311bc0,0x129b910,0x12de5ac] or p['btr']['near_call_target']!=0xf28339:raise ValueError('Unexpected target')
 # Configure the existing fixed-byte prefix reader for these explicit new seeds;
 # restore its defaults immediately. No target process or file is modified.
 old=frontier.SEEDS
 try:
  frontier.SEEDS={'after_btr':0x129b910,'after_btc':0x12de5ac};chains=frontier.capture(jar)['chains']
 finally:frontier.SEEDS=old
 if chains[0]['blocks'][-1]['first_transfer']['address']!=p['btc']['branch_address']:raise ValueError('Carry proof not connected to prefix')
 if chains[1]['blocks'][-1]['first_transfer']['address']!=0xfa14e5:raise ValueError('Return frontier moved')
 for item in p.values():item['target_file_backing']=backing(rs,item['target_address'],1)
 return dict(format='kneekura.ysm-native-load-flag-chain.v1',artifact_sha256=SHA,image_sha256=dict(IMAGES)['libysm-core.so'],dependency_parity_proof_sha256=hashlib.sha256(json.dumps(prior,sort_keys=True).encode()).hexdigest(),segments=[dict(address=a,size=len(data),sha256=hashlib.sha256(data).hexdigest()) for (a,_),data in zip(SEGMENTS,parts)],proofs=p,followed_prefix_chains=chains,return_target_resolved=False,assumptions=prior['assumptions']+['Normal unmodified instruction flow follows the proven conditional edges and direct-prefix transfers','Only the explicitly named flag is carried across each proof; undefined flags are not reused'],target_executed=False,native_emulation_run=False,constant_and_flag_analysis_only=True,native_implementations_resolved=False,java_native_bindings_resolved=False,independent_semantic_review='NOT_RUN')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jar',required=True);p.add_argument('--out',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();r=capture(Path(a.jar));out=Path(a.out)
 if a.check:
  if json.loads(out.read_text())!=r:raise SystemExit('Flag-chain mismatch')
 else:out.write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'proofs':len(r['proofs']),'new_prefixes':[len(c['blocks']) for c in r['followed_prefix_chains']],'status':'MATCH' if a.check else 'WRITTEN','target_executed':False}))
if __name__=='__main__':main()
