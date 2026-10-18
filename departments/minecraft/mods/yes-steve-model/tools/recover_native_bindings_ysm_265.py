#!/usr/bin/env python3
"""Replay isolated metadata callbacks, never the host library or real JNI progression.

Inputs are pinned to the original YSM 2.6.5 ELF/JAR and the documented next6
checkpoint. Each replay has one cloned state; callbacks run sequentially with
fresh synthetic frames. --proof-only and --verify-receipt execute no guest code.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

from native_export_backing_ysm_265 import regions, data_at
from native_java_metadata_ysm_265 import JavaMetadata, _descriptor, _name

IMAGE_SHA = "15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22"
JAR_SHA = "25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f"
CHECKPOINT_SHA = "5910f1c5b52de7aeb2313ae9885bc22fd385a27815885516287cd319e4271d84"
# Expected plaintext digests come from this independently retained observed receipt.
OBSERVATION_RECEIPT_SHA = "c907e34e24f0cca48e4746aee3e92219bd0b8428bcd51a659921fd49d48b1e1d"
RESOURCE_STOPS = {"INSTRUCTION_BUDGET", "TIME_BUDGET", "ENGINE_TIMEOUT"}
PAIRS = [{'callback': 4293952,
  'native': 3940768,
  'source': 283098,
  'length': 97,
  'callback_sha256': '7da482301f9501f1405cb37bf287e6cc3f64a4f73b6aa633c26d110b12410bcb',
  'source_sha256': '36263b08add52e60b3c956926ec05476f17df95c5f53b1db2ee704a077611dae',
  'static': True,
  'stores': [(4275403, '488d056e480000'),
             (4275410, '49894618'),
             (4275414, '488d05c3e4faff'),
             (4275421, '49894620')],
  'payload_sha256': '6bd3ba37d00e1e3909b3c48406f94cddfe86d52df3bcae8b2a8b74291d59ea17'},
 {'callback': 4293984,
  'native': 3941136,
  'source': 289009,
  'length': 80,
  'callback_sha256': 'bac1065d0a9e7a4b35fad2269646e61532d4c0ab56225ccbcbaf5b67ae074309',
  'source_sha256': 'c17bb131963fc16fed53c0e0cceae47c74cfe03dce55078ba0d641a9e25b0cf6',
  'static': True,
  'stores': [(4275585, '488d05d8470000'),
             (4275592, '4989441f18'),
             (4275597, '488d057ce5faff'),
             (4275604, '4989441f20')],
  'payload_sha256': '964f975b8cd6b66fa345db11cade09f626a8ee7e11b6c57cf722efa6f353e528'},
 {'callback': 4294016,
  'native': 3942688,
  'source': 290184,
  'length': 145,
  'callback_sha256': 'f1f9e46c7323aa87a6ff0d45364cb078924105924d2e6385042b152e8f4f931b',
  'source_sha256': 'b8216874c0b94040648e2b945c37f0a178a9d01f519f6689e97f1b6aedde1cec',
  'static': True,
  'stores': [(4275845, '4c8d2df4460000'),
             (4275905, '4c896d18'),
             (4275909, '488d0554eafaff'),
             (4275916, '48894520')],
  'payload_sha256': '7d9f8d6cfb074178670f453bee2609765874e28923af7703cd48a158930cf4da'},
 {'callback': 4294048,
  'native': 3953040,
  'source': 290329,
  'length': 98,
  'callback_sha256': '6c3e65d056b68f94c8823f0165b6a640d7093c5694cf5bdb125f0b467c286bd3',
  'source_sha256': '4efa017368f345e6c2ff6a0a10d98b22eb5e34c28458821708f2b04103e7e65b',
  'static': True,
  'stores': [(4278126, '488d2d2b3e0000'),
             (4278183, '49896d18'),
             (4278187, '488d05de09fbff'),
             (4278194, '49894520')],
  'payload_sha256': '511c199e8b4c746a31583c97dbf814bcc081585c7c855e40fd1fcc8f65207a6f'},
 {'callback': 4294080,
  'native': 3953920,
  'source': 279398,
  'length': 153,
  'callback_sha256': '6db2a1afd53224d0a78b02a40e9821476848a4700aad51345aae872e2b4caca5',
  'source_sha256': 'be2f2fe71b84b2bfc8c443d7baefd3760844483932e03115addbda7cdd8e2281',
  'static': True,
  'stores': [(4278603, '4c8d2d6e3c0000'),
             (4278659, '4c896d18'),
             (4278663, '488d05720bfbff'),
             (4278670, '48894520')],
  'payload_sha256': 'b372108c39149ec7159564283b9bac7a527791c26f7413c650286a15ec46a122'},
 {'callback': 4294112,
  'native': 3959360,
  'source': 261674,
  'length': 117,
  'callback_sha256': 'cca4edeca67e8100846ea8ada60141a318f936484b83e33818f81976aa7bb6a4',
  'source_sha256': '5443cb842cd1cbd20aa5eb3118a63ae4e3b00c92a7305e1145d95533328610be',
  'static': True,
  'stores': [(4279086, '488d2dab3a0000'),
             (4279143, '49896d18'),
             (4279147, '488d05ce1efbff'),
             (4279154, '49894520')],
  'payload_sha256': '8b030168bc2a0d42599723a545e56dd2aa823368a236475f60c5a40328721e28'},
 {'callback': 4294144,
  'native': 3917760,
  'source': 281009,
  'length': 97,
  'callback_sha256': 'eb85399d59ca37078ee6a8a795e0be5201d2c64e1c6cb5fde9a5d828fd3c2fc8',
  'source_sha256': '8857e23b852f38e89c88f76dc38cf94b430e40851f0097c1b4134436ebd0d186',
  'static': True,
  'stores': [(4279555, '4c8d2df6380000'),
             (4279619, '4c896d18'),
             (4279623, '488d05727afaff'),
             (4279630, '48894520')],
  'payload_sha256': 'd425031793116638927a78f23b1218f357c69578b3f07dc0ae65e2e80410ac99'},
 {'callback': 4294176,
  'native': 3927616,
  'source': 289089,
  'length': 101,
  'callback_sha256': '49ea782b234799a09dc57a8127598a95a1c2abe9a6619367e4e8ded9eb03d346',
  'source_sha256': '32072009b6cc28338dbacfd6980cab726a91ccb03ed5883a32c89adc2e02bbea',
  'static': True,
  'stores': [(4280038, '488d2d33370000'),
             (4280103, '49896d18'),
             (4280107, '488d050e9ffaff'),
             (4280114, '49894520')],
  'payload_sha256': '27acf8496c81fe9570e596f8e7a7055631bc334c45bae03a1ca1a021c5c13b3b'},
 {'callback': 4294208,
  'native': 3928256,
  'source': 292883,
  'length': 80,
  'callback_sha256': 'f5060aaa76fb7da82ed917bea59d1ac3b818722b940a5397fc756f6da6039fc8',
  'source_sha256': '13f5a60a42e51406885bf9d544acb59c6826f825f8ba9cfd90b8e00a0a07e8a5',
  'static': False,
  'stores': [(4280515, '4c8d2d76350000'),
             (4280579, '4c896d18'),
             (4280583, '488d05b29ffaff'),
             (4280590, '48894520')],
  'payload_sha256': '13d9e56ac1332de0a9a3bbc898e363232439974fd37287c71d4ae266dcec22e1'},
 {'callback': 4294240,
  'native': 3929408,
  'source': 281106,
  'length': 81,
  'callback_sha256': 'bf1aeeb04346d231a0555446306637a97636748350edaeee50cbc798417ba655',
  'source_sha256': 'c63602daee5ac097cbbc70fafc7f84c052acd6fe9d06608ef7ff210b62eccaf8',
  'static': True,
  'stores': [(4281006, '488d2dab330000'),
             (4281063, '49896d18'),
             (4281067, '488d054ea2faff'),
             (4281074, '49894520')],
  'payload_sha256': '4131880df69763d97f67a3c8c79b4d674899a3b38e34ec543fffca5a5b732fbf'},
 {'callback': 4294272,
  'native': 3936608,
  'source': 255109,
  'length': 81,
  'callback_sha256': '7ecce6b78bbb9bea265756cd20c22e993de201fcc4800d2fe438378e8b95177b',
  'source_sha256': '28453487e7987e530beb12634fd2b64b8b8f240b9f79d6cc57c98afdf69c0785',
  'static': True,
  'stores': [(4281501, '4c8d3ddc310000'),
             (4281565, '4c897d18'),
             (4281569, '488d0578bcfaff'),
             (4281576, '48894520')],
  'payload_sha256': '988f8de001c494518d8789cd37798e8213c0a7f2419b5c9fc6c38d0cac16e458'},
 {'callback': 4294304,
  'native': 3937280,
  'source': 277344,
  'length': 80,
  'callback_sha256': '4f9d4279baedf76f06e4dde49181f6e008fe527b74fbaad44eff3807404cabbd',
  'source_sha256': 'f680adbc7067695097c3f0a418886a5cc2d5d5d98562393f9d3da8a20ae881c9',
  'static': True,
  'stores': [(4281972, '4c8d2d25300000'),
             (4282036, '4d896f18'),
             (4282040, '488d0541bdfaff'),
             (4282047, '49894720')],
  'payload_sha256': 'a0131267e8f23c4fccf2cc46a2c35e6e7d8c72700f2685045d52547b738a3fc9'},
 {'callback': 4294336,
  'native': 3937792,
  'source': 274684,
  'length': 102,
  'callback_sha256': 'cd26c2f2297a884bf1d559f1243f6d1841bd299b7db8e45edd4067024f7b6327',
  'source_sha256': 'e44f4969375654bf6d7603622e1b0467544e0f1f9a5d15e9a6bf792a7caa06dc',
  'static': True,
  'stores': [(4282462, '488d2d5b2e0000'),
             (4282519, '49896d18'),
             (4282523, '488d055ebdfaff'),
             (4282530, '49894520')],
  'payload_sha256': '2adfa99f78872672333887bfeabd5cc137723dc8035cd8284951f72715b07e58'},
 {'callback': 4294368,
  'native': 3938384,
  'source': 290427,
  'length': 102,
  'callback_sha256': 'ee7a98759d8bffd394eeb8b9c3923038e2817fa90f9b0429ed8d9f59a47df483',
  'source_sha256': 'e5bdf6845d88db7fa9bda21b6a7a5319b52c113b9ebf3e66786dbc633ff57896',
  'static': True,
  'stores': [(4282939, '4c8d2d9e2c0000'),
             (4282995, '4c896d18'),
             (4282999, '488d05d2bdfaff'),
             (4283006, '48894520')],
  'payload_sha256': '4478906af5d71f49d97f089c4ddd6ad52b1aa398710ada96f933fd1df4566d3b'},
 {'callback': 4294400,
  'native': 3940560,
  'source': 281187,
  'length': 81,
  'callback_sha256': 'e46b8aeb8fc7a7de5195d4c0c46b549f2f8940fa2d02e1bd164463a9917fa7f1',
  'source_sha256': 'd263be5421837a56050eb18105cd3dc92c53a6d090554313454fc469b8896b54',
  'static': True,
  'stores': [(4283422, '488d2ddb2a0000'),
             (4283479, '49896d18'),
             (4283483, '488d056ec4faff'),
             (4283490, '49894520')],
  'payload_sha256': '32860ce7283e206edc54e13e319b4c3b9fa263f2bb5c5cf9fe9e95b1778c80cb'},
 {'callback': 4294432,
  'native': 3940608,
  'source': 286783,
  'length': 81,
  'callback_sha256': '4193dc426d4e5e65c442ee820468a2d138837cbb03a45e2f86b98f844f3532d5',
  'source_sha256': '31a7ba422b204d3514247681536e2108740f044c715a324e33dcc15e4b259434',
  'static': True,
  'stores': [(4283883, '4c8d2d2e290000'),
             (4283939, '4c896d18'),
             (4283943, '488d05d2c2faff'),
             (4283950, '48894520')],
  'payload_sha256': '67fae5489ff9981d4e4720cda940fe37e98cd29a77ab44bf894752a40cf0a4a7'},
 {'callback': 4294464,
  'native': 3929936,
  'source': 264402,
  'length': 249,
  'callback_sha256': 'd59f889c3a5b5b8215c252f500d5ada19baeef303141b09b48b81ee6fd4b8696',
  'source_sha256': '1f7f30682e76c71870b9ee47606370763c191b65f33c7607fb4057b238968d33',
  'static': True,
  'stores': [(4284342, '488d1d83270000'),
             (4284396, '49895d18'),
             (4284400, '488d055997faff'),
             (4284407, '49894520')],
  'payload_sha256': 'd633c81644638f44deecb597a8cf451e517cd466927f50ce6d07c76c9bdd6f97'}]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pinned(path, expected):
    data = path.read_bytes()
    require(digest(data) == expected, "Pinned input hash mismatch: " + str(path))
    return data


def source_proof(image):
    require(digest(image) == IMAGE_SHA, "Original ELF hash mismatch")
    rs = regions(image)
    result = []
    for i, row in enumerate(PAIRS):
        cb = row["callback"]
        raw = data_at(image, rs, cb, 32)
        require(digest(raw) == row["callback_sha256"], "Callback changed")
        require(cb + 11 + struct.unpack_from("<i", raw, 7)[0] == row["source"], "Source LEA changed")
        require(struct.unpack_from("<I", raw, 19)[0] == row["length"], "Payload length changed")
        require(digest(data_at(image, rs, row["source"], row["length"])) == row["source_sha256"], "Source bytes changed")
        stores = []
        for address, expected in row["stores"]:
            actual = data_at(image, rs, address, len(bytes.fromhex(expected)))
            require(actual.hex() == expected, "Descriptor instruction changed")
            stores.append(dict(address=hex(address), bytes=expected, sha256=digest(actual)))
        result.append(dict(callback=hex(cb), native=hex(row["native"]),
                           registration_flags=0 if i < 6 else 2,
                           source=hex(row["source"]), source_length=row["length"],
                           callback_sha256=row["callback_sha256"],
                           source_sha256=row["source_sha256"],
                           expected_decoded_payload_sha256=row["payload_sha256"], stores=stores))
    return result


def parse_payload(payload, expected_length):
    require(len(payload) == expected_length and payload.endswith(b"\0"), "Payload length/terminator mismatch")
    require(b"\0" not in payload[:-1], "Embedded NUL in payload")
    text = payload[:-1].decode("ascii")
    require(text.startswith("L") and ";" in text and "(" in text, "Invalid binding payload")
    owner, rest = text[1:].split(";", 1)
    name, suffix = rest.split("(", 1)
    require(bool(owner) and bool(name) and not any(c in name for c in ".;/[\\<>"), "Invalid binding member")
    _name(owner)
    descriptor = "(" + suffix
    _descriptor(descriptor)
    return owner, name, descriptor


def declaration_proof(metadata, payload, row):
    if "payload_sha256" in row:
        require(digest(payload) == row["payload_sha256"], "Decoded payload differs from pinned observed evidence")
    owner, name, descriptor = parse_payload(payload, row["length"])
    info = metadata.class_info(owner)
    require(info is not None, "Missing declaring class")
    matches = [m for m in info["methods"] if m["name"] == name and m["descriptor"] == descriptor]
    require(len(matches) == 1, "Exact declared method absent or ambiguous")
    member = matches[0]
    require(bool(member["access"] & 0x100), "Method is not ACC_NATIVE")
    static = bool(member["access"] & 8)
    require(static == row["static"], "Static/instance JNI ABI mismatch")
    lookup = metadata.lookup_method(owner, name, descriptor, static=static)
    require(lookup is not None and lookup["declaring_class"] == owner, "Declaration identity mismatch")
    return dict(owner=owner, name=name, descriptor=descriptor,
                access=member["access"], acc_native=True, static=static,
                jni_second_argument="jclass" if static else "jobject",
                class_sha256=info["class_sha256"], payload=payload[:-1].decode("ascii"),
                payload_sha256=digest(payload))


def original_declarations(metadata, jar):
    result = set()
    with zipfile.ZipFile(jar) as archive:
        for name in archive.namelist():
            if name.startswith("com/elfmcys/") and name.endswith(".class"):
                info = metadata.class_info(name[:-6])
                for member in info["methods"]:
                    if member["access"] & 0x100:
                        result.add((info["name"], member["name"], member["descriptor"]))
    require(len(result) == 17, "Original declaration count changed")
    return result


def exact_set(records, expected):
    triples = [(r["owner"], r["name"], r["descriptor"]) for r in records]
    require(len(triples) == 17 and len(set(triples)) == 17 and set(triples) == expected,
            "Recovered bindings do not exactly cover original declarations")


def verify_saved(saved, metadata, proofs, expected):
    require(saved.get("image_sha256") == IMAGE_SHA and saved.get("jar_sha256") == JAR_SHA
            and saved.get("checkpoint_sha256") == CHECKPOINT_SHA, "Saved evidence input mismatch")
    records = saved.get("bindings", [])
    require(len(records) == 17, "Saved evidence needs 17 records")
    verified = []
    for row, proof, record in zip(PAIRS, proofs, records):
        require(record.get("callback") == proof["callback"] and record.get("native") == proof["native"], "Saved pairing mismatch")
        for key in ("source", "source_length", "source_sha256", "callback_sha256", "registration_flags"):
            require(record.get(key) == proof[key], "Saved source proof mismatch: " + key)
        require(record.get("stop", {}).get("reason") == "ENTRY_RETURN", "Saved callback did not return")
        result = declaration_proof(metadata, record["payload"].encode("ascii") + b"\0", row)
        for key in ("owner", "name", "descriptor", "access", "static", "class_sha256", "payload_sha256"):
            require(record.get(key) == result[key], "Saved declaration proof mismatch: " + key)
        verified.append({**proof, **result})
    exact_set(verified, expected)
    return verified


def run_segments(cpu, maximum):
    require(1 <= maximum <= 2, "Invalid segment count")
    segments = []
    for segment in range(maximum):
        stop = dict(cpu.run(cpu.reg("RIP")))
        segments.append(dict(stop=stop, attempted=cpu.attempted, completed=cpu.completed))
        if stop["reason"] not in RESOURCE_STOPS or segment + 1 == maximum:
            break
        cpu.stop = None
        cpu.attempted = cpu.completed = 0
    return stop, segments


def replay(args, image, metadata, proofs, report, receipt):
    # Lazy imports keep byte-only proof/tests usable without Unicorn installed.
    from native_batched_cpu_ysm_265 import BatchedJni
    from native_guarded_checkpoint_ysm_265 import read_checkpoint
    from native_initializer_sequence_ysm_265 import prepare_call, callback_frames_complete
    with (args.out / "callbacks.tsv").open("x") as log:
        cpu = BatchedJni(log, "proc-fixture", args.steps, args.seconds)
        cpu.batch_size = 256
        cpu.trace_instructions = False
        cpu.load_image(image)
        cpu.configure_loader("image-only")
        read_checkpoint(cpu, args.checkpoint)
        cpu.oracle_enabled = False
        initial_jni_calls = json.dumps(cpu.jni_state["calls"])
        for row, proof in zip(PAIRS, proofs):
            # Explicit new analytical frame, never a resume of interrupted JNI.
            cpu.call_in_progress = False
            cpu.stop = None
            cpu.attempted = cpu.completed = 0
            output = cpu.allocate(16)
            cpu.write_private(output, bytes(16))
            prepare_call(cpu, row["callback"])
            cpu.reg("RDI", output)
            stop, segments = run_segments(cpu, args.segments)
            record = {**proof, "stop": stop, "segments": segments}
            report["bindings"].append(record)
            receipt.write_text(json.dumps(report, indent=2) + "\n")
            if stop["reason"] != "ENTRY_RETURN":
                return False
            require(callback_frames_complete(cpu), "Unfinished callback frame")
            require(all(cpu.reg(k) == v for k, v in cpu.call_saved.items()), "Callee-saved ABI mismatch")
            require(cpu.reg("RAX") == output, "Callback result pointer ABI mismatch")
            require(json.dumps(cpu.jni_state["calls"]) == initial_jni_calls, "Unexpected JNI call during decoder")
            length, pointer = struct.unpack("<QQ", cpu.read_known(output, 16))
            require(length == row["length"], "Returned payload length mismatch")
            record.update(declaration_proof(metadata, cpu.read_known(pointer, length), row))
            receipt.write_text(json.dumps(report, indent=2) + "\n")
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("image", "jar", "checkpoint", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--proof-only", action="store_true")
    group.add_argument("--verify-receipt", type=Path)
    parser.add_argument("--steps", type=int, default=4000000)
    parser.add_argument("--seconds", type=int, default=180)
    parser.add_argument("--segments", type=int, default=2)
    args = parser.parse_args(argv)
    require(0 < args.steps <= 4000000 and 0 < args.seconds <= 180 and 1 <= args.segments <= 2, "Invalid bounded budget")
    image = pinned(args.image, IMAGE_SHA)
    pinned(args.jar, JAR_SHA)
    pinned(args.checkpoint, CHECKPOINT_SHA)
    proofs = source_proof(image)
    metadata = JavaMetadata(jar_path=args.jar)
    expected = original_declarations(metadata, args.jar)
    args.out.mkdir(parents=True, exist_ok=True)
    receipt = args.out / "binding-receipt.json"
    report = dict(format="ysm-native-binding-replay-v1", image_sha256=IMAGE_SHA,
                  jar_sha256=JAR_SHA, checkpoint_sha256=CHECKPOINT_SHA,
                  expected_payload_origin_receipt_sha256=OBSERVATION_RECEIPT_SHA,
                  mode="proof-only" if args.proof_only else "verify-saved" if args.verify_receipt else "isolated-replay",
                  state_model="One checkpoint clone; sequential callbacks; fresh synthetic frame per callback; no interrupted JNI resume",
                  runtime_RegisterNatives_success=False, JNI_OnLoad_completion_proven=False,
                  budgets=dict(steps=args.steps, seconds=args.seconds, max_segments=args.segments),
                  bindings=[], source_proofs=proofs, complete=False)
    with receipt.open("x") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    try:
        if args.proof_only:
            report["complete"] = True
        elif args.verify_receipt:
            saved = args.verify_receipt.read_bytes()
            report["bindings"] = verify_saved(json.loads(saved), metadata, proofs, expected)
            report.update(complete=True, saved_receipt_sha256=digest(saved), guest_replay_repeated=False)
        else:
            report["complete"] = replay(args, image, metadata, proofs, report, receipt)
        if report["complete"] and report["bindings"]:
            exact_set(report["bindings"], expected)
            report["exact_original_native_declaration_set_match"] = True
    except Exception as error:
        report["complete"] = False
        report["failure"] = str(error)
        raise
    finally:
        report["original_inputs_unchanged"] = all(digest(p.read_bytes()) == h for p, h in
                ((args.image, IMAGE_SHA), (args.jar, JAR_SHA), (args.checkpoint, CHECKPOINT_SHA)))
        receipt.write_text(json.dumps(report, indent=2) + "\n")
    require(report["original_inputs_unchanged"], "Original input changed")
    print(json.dumps(dict(complete=report["complete"], mode=report["mode"],
                         bindings=len(report["bindings"]), receipt_sha256=digest(receipt.read_bytes()))))
    return 0 if report["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
