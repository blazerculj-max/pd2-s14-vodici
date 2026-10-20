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
- ostali buildi: Hiim Mid/Bad in neocenjeni, javni planerji iz Hiim galerije, S13 popularni skilli.

Poleg tega:

- **Predmeti**: wiki vseh predmetov z iskalnikom, filtri, recepti in buildi, ki predmet nosijo,
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
5. `tools/build_data.py`: združi vse v `data/site.json`, `docs/assets/tips.json` in `docs/assets/items.json`
6. `tools/fetch_images.py`: prenese manjkajoče slike v `docs/img`
7. `tools/build_guides.py`: podatki za strani Mape in Crafting (`data/guides.json`)
8. `tools/build_site.py`: zgradi HTML v `docs/`

`data/hiim/maps/map_meta.json` (oznake map za povezave na Hiim postavitve) je izluščen iz Hiim strani in se ne osvežuje samodejno.

Uporablja samo Python 3 in `curl`.

## Viri

- [Hiim PD2](https://hiimpd2.com): S14 tier liste (solo, starter, bossing, party), planerji, galerija buildov, Maps explorer (pošasti in odpornosti), affixi in slike predmetov
- [pd2.tools](https://pd2.tools): S13 statistika likov (predmeti, skilli) in posnetki skozi sezono
- [PD2 wiki](https://wiki.projectdiablo2.com): skilli, predmeti, recepti (Horadric Cube, crafting), mape, korupcije, mehanike imunitet
- S14 Alliance tentative patch notes

Slike predmetov in skillov so last Blizzard Entertainmenta (Diablo II). Stran ni povezana z Blizzardom ali ekipo Project Diablo 2.
