# PD2 S14 buildi

Neuradna stran z buildi za **Project Diablo 2, Season 14 (Alliance)**. Izbereš razred in vidiš vse viable builde (Hiim tier lista: Top, Good, Decent, Utility in starter buildi) z:

- oceno za mapping (Hiim solo tier lista in najhitrejša mapa),
- oceno za bossing (Diablo Clone, Rathma, Lucion, T0 in T2),
- nasvetom za leveling (direktno ali z respecom, iz S13 posnetkov na pd2.tools),
- planerji z razporeditvijo točk, opremo po fazah, slikami predmetov in mercem,
- S13 statistiko s pd2.tools (koliko likov 90+, kaj nosijo),
- tooltipi: statsi predmetov z razponi (aktualni PD2 wiki) in sinergije skillov (Hiim + wiki), ob premiku miške ali tapu,
- recepti in rune pri vsakem planerju ter seznam run za ves build,
- povzetki video vodičev »Iz videa« (skilli, oprema, merc, nasveti) s primerjavo s Hiim S14 planerjem (`content/videos.json`),
- načrt od 1 do 99: faze (leveling direktno ali z razredno potjo in respecom, zgodnji farming, T1 in T3 mape brez imunitet na glavni element), skill točke po levelih (s quest točkami in respeci), stat točke, kaj iskati na rarih zgodaj, godly rari, S13 affixi in korupcije po slotih ter S14 korupcije iz planerjev,
- ostali buildi: Hiim Mid/Bad in neocenjeni, javni planerji iz Hiim galerije, S13 popularni skilli.

Poleg tega:

- **Tier liste**: Hiim mapping, bossing (DClone, Rathma, Lucion; T0 in T2), budget (starter lista, najdražja runa v najcenejšem planerju, budget video vodiči) in group liste ter DarkHumilityjeva S14 late game tier lista (zavihek, ocena pri vsakem buildu, njegovi starterji in boss priporočila), s filtrom po razredu,
- **Za začetnike**: kaj pobirati za svoj razred (na katerih predmetih so +skilli na posamezne skille, +drevo in +class skills ter od katerega levela, iz Hiim affixov), kaj socketaš za preživetje (gemi od chipped do perfect, nizke rune), zgodnji runewordi iz JuxtAPoserjeve opreme, zgodnji magic in rari po slotih, kje gledaš škodo (orožje, skill, minioni, brca; delež škode orožja s PD2 wikija), questi z nagradami in JuxtAPoserjeva S14 tier lista (leveling, zgodnji farming, cenejši mapperji); pri vsakem buildu je še blok »Za začetnike« z virom škode, predmeti za pobrati in JuxtAPoserjevimi ocenami,
- **Predmeti**: wiki vseh predmetov z iskalnikom, filtri, recepti in buildi, ki predmet nosijo,
- **Runewordi**: filtri po bazi (vrste orožja, oklep, ščit, helm) in socketih ter iskanje po runah, ki jih imaš (kje se uporabijo, kaj lahko sestaviš, kje manjka ena runa); S14 spremembe so v `content/runewords-s14.json`,
- **Mape**: vse S14 mape s pošastmi in imunitetami, filter po elementu, najhitrejši buildi, orbi, affixi, korupcije in eventi,
- **Crafting**: socketi, nadgradnje, korupcija, reroll, S14 craft recepti in affixi z alvl.

Za nekaj buildov je tudi naš podroben vodič (leveling po levelih, oprema s kljukicami), poleg tega pa še druid plan in splošni vodič (loot, runewordi, crafting, recepti, mape).

Stran: `docs/` (GitHub Pages).

## Posodobitev podatkov

Hiim tier liste se med sezono spreminjajo. Vse podatke osvežiš z:

```bash
./tools/update.sh
```

Skripta po vrsti:

1. `tools/fetch_hiim.py --force`: Hiim tier liste, katalog plannerja in vse povezane planerje
2. `tools/fetch_wiki.py`: wiki strani s skilli (predpogoji) in predmeti (statsi za tooltipe)
3. `tools/fetch_pd2tools.py`: pd2.tools statistika za vsak build (S13)
4. `tools/fetch_pd2tools.py --respec`: posnetki najhitrejših likov (traja dlje)
5. `tools/fetch_rares.py`: rari, crafti, magic predmeti in korupcije S13 likov 90+ po slotih za vsak glavni skill → `data/pd2tools/rares.json` (že prebrani buildi ostanejo v predpomnilniku, `--force` vse prebere znova)
6. `tools/fetch_dh.py`: DarkHumilityjeva S14 tier lista (Google Sheet kot xlsx) in podatki o njegovih videih → `data/dh/tierlist.json`; imena njegovih buildov so z našimi povezana v `content/dh-map.json`
7. `tools/fetch_juxt.py`: JuxtAPoserjeva S14 tier lista s pd2guides.pages.dev (njihov API `/api/build-data?class=…`) → `data/juxt/tierlist.json`; imena njegovih buildov so z našimi povezana v `content/juxt-map.json`
8. `tools/build_data.py`: združi vse v `data/site.json`, `docs/assets/tips.json` in `docs/assets/items.json`
9. `tools/fetch_images.py`: prenese manjkajoče slike v `docs/img`
10. `tools/build_guides.py`: podatki za strani Mape in Crafting (`data/guides.json`)
11. `tools/build_site.py`: zgradi HTML v `docs/`

Vsebino za začetnike (stran in blok pri buildu) sestavi `tools/noob.py`.

Načrt od 1 do 99 računa `tools/plan.py` iz Hiim planerjev (cilji po fazah) in skill dreves v Hiim katalogu (level zahteve, predpogoji, sinergije). Tip buildov (caster, melee, lok, metalec, summoner, trapi) in glavni elementi za izbiro map so ročno v `content/build-profiles.json`; razredne leveling poti so v `CLASS_ROUTE` v `tools/build_site.py`.

`data/hiim/maps/map_meta.json` (oznake map za povezave na Hiim postavitve) je izluščen iz Hiim strani in se ne osvežuje samodejno.

Uporablja Python 3, `curl` in za DarkHumilityjevo tabelo `openpyxl`.

## Viri

- [Hiim PD2](https://hiimpd2.com): S14 tier liste (solo, starter, bossing, party), planerji, galerija buildov, Maps explorer (pošasti in odpornosti), affixi in slike predmetov
- [pd2.tools](https://pd2.tools): S13 statistika likov (predmeti, skilli) in posnetki skozi sezono
- [PD2 wiki](https://wiki.projectdiablo2.com): skilli, predmeti, recepti (Horadric Cube, crafting), mape, korupcije, mehanike imunitet
- [DarkHumility](https://docs.google.com/spreadsheets/d/1DLkTz-3gtlBgoyxxAot60Ro_76ct3Oz8Bmyhu7Hbwo4/htmlview): S14 late game mapping tier lista, starterji, boss priporočila, mape in njegovi video vodiči
- [JuxtAPoser](https://pd2guides.pages.dev/): S14 tier lista (leveling, zgodnji farming in bossing, cenejši in endgame mapperji, T2 bossing) z opremo in merci
- S14 Alliance tentative patch notes

Slike predmetov in skillov so last Blizzard Entertainmenta (Diablo II). Stran ni povezana z Blizzardom ali ekipo Project Diablo 2.
