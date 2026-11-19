package dev.kneekura.fivedifficulties.forge.spellcard;

import dev.kneekura.fivedifficulties.forge.spellcard.cards.SimpleCards;
import dev.kneekura.fivedifficulties.forge.spellcard.cards.SpecialCards;

/**
 * X1 CommonProxy.registerSpellCards: registered names and IDs are X1's.
 * Not yet registered (need their own entities, P12): 0 MusouFuuin, 1 MasterSpark, 8 SatuzinDoll,
 * 10 HikouchuuNest, 15 Fafrotskies_no_Kiseki.
 */
public final class X1SpellCards {
    private static boolean done;

    private X1SpellCards() {}

    public static synchronized void registerAll() {
        if (done) return;
        done = true;
        r(SimpleCards.KashoNoEimin::new, "Kasho_no_Eimin", 2);
        r(SimpleCards.MeteonicShower::new, "MeteonicShower", 3);
        r(SimpleCards.NamiToTubuNoKyoukai::new, "Nami_to_Tubu_no_Kyoukai", 4);
        r(SpecialCards.NijuuKokushichou::new, "NijuuKokushichou", 5);
        r(SimpleCards.ScarletShoot::new, "ScarletShoot", 6);
        r(SimpleCards.ZenzinruiNoHisouten::new, "Zenzinrui_no_Hisouten", 7);
        r(SpecialCards.PerfectFreeze::new, "PerfectFreeze", 9);
        r(SpecialCards.KappaPororoca::new, "Kappa'sPororoca", 11);
        r(SpecialCards.StardustReverie::new, "StardustReverie", 12);
        r(SimpleCards.KerochanFuuuNiMakezu::new, "Kerochan_Fuuu_ni_Makezu", 13);
        r(SpecialCards.MiracleFruit::new, "MiracleFruit", 14);
        r(SpecialCards.YouryokuSpoiler::new, "YouryokuSpoiler", 16);
        r(SimpleCards.MosesMiracle::new, "Moses_no_Kiseki", 17);
        r(SimpleCards.YasakaNoKamikaze::new, "Yasaka_no_Kamikaze", 18);
        r(SpecialCards.IcicleFall::new, "IcicleFall", 19);
        r(SpecialCards.StarbowBreak::new, "StarbowBreak", 20);
        r(SimpleCards.Catadioptric::new, "Catadioptric", 21);
        r(SimpleCards.Mishagujisama::new, "Mishagujisama", 22);
        r(SpecialCards.RedMagic::new, "RedMagic", 23);
        r(SimpleCards.EternalMeek::new, "EternalMeek", 24);
        r(SimpleCards.NonDirectionalLaser::new, "Non-DirectionalLaser", 25);
        r(SimpleCards.Kachoufuugetu::new, "KachoufuugetuShoufuurougetu", 26);
        r(SimpleCards.SpearTheGungnir::new, "Spear_the_Gungnir", 27);
        r(SimpleCards.MoonlightRay::new, "MoonlightRay", 28);
        r(SimpleCards.HoukaKenran::new, "HoukaKenran", 29);
        r(SimpleCards.SaikouRanbu::new, "SaikouRanbu", 30);
        r(SpecialCards.FujiyamaVolcano::new, "FujiyamaVolcano", 33);
        r(SpecialCards.LittleBugStorm::new, "LittleBugStorm", 34);
        r(SpecialCards.MeteorOnEarth::new, "Meteor_on_Earth", 35);
        r(SpecialCards.GagoujiCyclone::new, "GagoujiCyclone", 40);
        // X1 registers a card's special shots when the card is first constructed.
        for (X1SpellCardRegistry.Entry e : X1SpellCardRegistry.all()) e.create().registerSpecialShots();
    }

    private static void r(java.util.function.Supplier<X1SpellCard> factory, String name, int id) {
        X1SpellCardRegistry.register(factory, "thkaguyamod", name, id);
    }
}
