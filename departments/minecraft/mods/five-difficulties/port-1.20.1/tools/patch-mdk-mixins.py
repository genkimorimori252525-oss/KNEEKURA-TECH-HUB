#!/usr/bin/env python3
"""Idempotently enable Sponge Mixin in an official Forge 1.20.1 MDK build.gradle."""

from __future__ import annotations

import argparse
from pathlib import Path

PLUGIN = "    id 'org.spongepowered.mixin' version '0.7.+'"
FORGE_PLUGIN = "    id 'net.minecraftforge.gradle' version '[6.0,6.2)'"
MARKER = "// five-difficulties-p3-mixin-support"
APPEND = r'''

// five-difficulties-p3-mixin-support
mixin {
    add sourceSets.main, 'five_difficulties_port.refmap.json'
    config 'five_difficulties_port.mixins.json'
    disableTargetValidator = true
}

dependencies {
    annotationProcessor 'org.spongepowered:mixin:0.8.5:processor'
}

tasks.named('jar', Jar).configure {
    manifest {
        attributes([
            'MixinConfigs': 'five_difficulties_port.mixins.json'
        ])
    }
}
'''

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("build_gradle", type=Path)
    args = ap.parse_args()

    path = args.build_gradle
    text = path.read_text(encoding="utf-8")

    if "id 'org.spongepowered.mixin'" not in text:
        if FORGE_PLUGIN not in text:
            raise SystemExit("ForgeGradle plugin anchor not found in MDK build.gradle")
        text = text.replace(FORGE_PLUGIN, FORGE_PLUGIN + "\n" + PLUGIN, 1)

    if MARKER not in text:
        text = text.rstrip() + APPEND + "\n"

    path.write_text(text, encoding="utf-8")
    print(f"PATCHED_MIXIN_BUILD {path}")

if __name__ == "__main__":
    main()
