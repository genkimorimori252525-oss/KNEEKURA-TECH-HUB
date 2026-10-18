"""Three exact post-initializer maskedCRC loops, with distinct counter registers.

Working-image summaries require input bytes still equal immutable source bytes;
code/table fingerprints and all256 masked entries are checked by shared engine.
"""
P3=dict(entry=0x101c57a,exit=0xf0ca0c,table=0x132c6d8,mask=0xd428332e,steps=29,scratch=40,source_reg='RDX',crc_reg='RAX',table_reg='R11',counter_reg='RCX',working_image_safe=True,table_sha='44bae42b95217d62c643a62031618d2bd4334651959a924b9fb1a31c3f2b35bc',code={
0x101c57a:bytes.fromhex('41b911340f5749c1f925460a0c0a4433c868007680d0e99532f6ff'),
0xf7f82a:bytes.fromhex('66c17c24064d4181e1ff000000f6542401c14c240384478b0c8b66ff4c240466ff442403c1e808e9f9a44100'),
0x1399d4f:bytes.fromhex('4133c1e85594c3ff'),
0xfd31ac:bytes.fromhex('48ffc248c744240013d4a17c66f75c2407352e3328d4c1642409fa680c61b5eae8d9aa3400'),
0x131dcaa:bytes.fromhex('48ffc96894f00885e94aedbeff'),
0xf0ca01:bytes.fromhex('488d6424280f856efb1000')})
P4=dict(entry=0x111f65b,exit=0x10b0895,table=0x13c6368,mask=0x5f380f19,steps=35,scratch=56,source_reg='RDI',crc_reg='R10',table_reg='RCX',counter_reg='RAX',working_image_safe=True,table_sha='a27c8765483563136413f52b56820d525adbc2b9771276fb37917b72a1066e34',code={
0x111f65b:bytes.fromhex('be92fd025748f7d60fbae69c0fb6b43793fd025768931ba717e8c95ef2ff'),
0x1045542:bytes.fromhex('c144240cca4133f2e8a4a10200'),
0x106f6f3:bytes.fromhex('81e6ff00000048ff4c241048c744240096629abe8b34b1c14424108b6813ae33aa48c7442410bbcf9b3641c1ea08f75c24060f8ba791f8ff'),
0xff88d2:bytes.fromhex('6681742407ba204433d6c16c24069068a2e4062ffe4c240c48ffc766c16424168d0f89c2e709000f855c970300'),
0x103205b:bytes.fromhex('4181f2190f385fe85c0e0000'),
0x1032ec3:bytes.fromhex('48ffc8e8b6d90700'),
0x10b0881:bytes.fromhex('48c74424002af1976d488d6424380f85c6ed0600')})
P5=dict(entry=0xfdb44c,exit=0xed0d88,table=0x10fb318,mask=0x7d35b404,steps=24,scratch=48,source_reg='RCX',crc_reg='R11',table_reg='R9',counter_reg='RSI',working_image_safe=True,table_sha='8038de624b8928858517039ac97c9135c74f696fbbb17675c6275483f686bbd1',code={
0xfdb44c:bytes.fromhex('0fb611e956330800'),
0x105e7aa:bytes.fromhex('4133d3e81fca0700'),
0x10db1d1:bytes.fromhex('81e2ff000000418b149148c7442400ad538e7748c14424006c804424043641c1eb084433da680a568de768aa09378468b76b924748ffc14181f304b4357de9c89d2300'),
0x1314fdc:bytes.fromhex('48c1442408fa668154241732d348ffcee887bdbbff'),
0xed0d78:bytes.fromhex('6802d39307488d6424300f85c4a61000')})
JNI_PROFILES=(P3,P4,P5)
