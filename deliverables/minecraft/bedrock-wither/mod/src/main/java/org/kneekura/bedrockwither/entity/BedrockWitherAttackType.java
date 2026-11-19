package org.kneekura.bedrockwither.entity;

/**
 * Mirrors the current Bedrock BDS WitherBoss::WitherAttackType symbol names.
 *
 * Values come from the Bedrock-facing generated header, not from Java Wither or BEStyleWither.
 */
public enum BedrockWitherAttackType {
    CHARGE(0),
    HURT_EXPLOSION(1),
    PROJECTILE(2);

    private final int nativeId;

    BedrockWitherAttackType(int nativeId) {
        this.nativeId = nativeId;
    }

    public int nativeId() {
        return nativeId;
    }

    public static BedrockWitherAttackType fromNativeId(int id) {
        for (BedrockWitherAttackType value : values()) {
            if (value.nativeId == id) {
                return value;
            }
        }
        throw new IllegalArgumentException("Unknown Bedrock Wither attack type: " + id);
    }
}
