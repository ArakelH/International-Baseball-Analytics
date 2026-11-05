# International-Born MLB Hitters | Reproducible Baseball Data Analysis

**A portfolio project for analytical roles in baseball operations and scouting information.**

This project demonstrates reproducible **Python + SQLite ETL**, relational joins, data-quality checks, baseball rate statistics, and an exploratory country-level report using real, publicly released MLB data. It does **not** purport to identify international free agents, assess prospects, or reproduce a club's proprietary scouting model.

## Business question

How can an analyst transform messy, multi-table historical baseball data into a validated, reproducible dataset for reviewing MLB hitter-season performance among players **born outside the United States**? Which birth-country labels occur most frequently in the sample of qualifying hitter-seasons during 2015–2025?

This is an *information operations demonstration*: reliable, documented data and explicit definitions come before scouting recommendations.

## What the pipeline does

1. Downloads the published **SABR Lahman 2025 CSV release** (`People.csv` and `Batting.csv`) from an attributed GitHub mirror, or accepts copies you download from SABR yourself.
2. Loads player metadata and batting records into an in-memory SQLite database.
3. Validates unique player IDs, batting `(player, year, stint)` keys, nonnegative counting statistics, and sensible hit totals.
4. Joins batting lines to player birth-country labels and **combines multi-team stints before calculating rates**.
5. Selects 2015–2025 hitter-seasons with at least 200 estimated plate appearances and computes OBP, SLG, and OPS.
6. Exports a player-season table, birth-country-by-year counts, data-quality report, and a PNG summary chart.

## Run locally

Requires Python 3.10+ and Internet access on the first run.

```bash
python -m pip install -r requirements.txt
python -m src.pipeline --download
python -m unittest discover -s tests -v
```

You can also download `People.csv` and `Batting.csv` directly from [SABR](https://sabr.org/lahman-database/), place them in `data/`, and run `python -m src.pipeline` without `--download`.

**Outputs** (`outputs/`, generated after running):

- `player_seasons.csv`: one row per qualifying hitter-season, with `birth_country`, `obp`, `slg`, `ops`.
- `country_year_counts.csv`: number of qualifying hitter-seasons per birth-country label and season.
- `quality_report.json`: source coverage, orphaned batting lines, missing-country counts and sample sizes.
- `country_batting_seasons.png`: chart of birth-country counts in the qualifying hitter-season sample.

**Data are not included in this repo** because the original SABR dataset is separately licensed. Downloaded CSVs and generated data are ignored by Git.

## Metric definitions

- `PA proxy = AB + BB + HBP + SF + SH` (batting-stat line estimate; not an exact official PA feed).
- `OBP = (H + BB + HBP) / (AB + BB + HBP + SF)`.
- `SLG = (H + 2B + 2*3B + 3*HR) / AB` (total bases equivalent).
- `OPS = OBP + SLG`.
- **200 PA proxy** is an exploratory filter to reduce extreme small samples, not MLB qualification status.
- Player data are aggregated across team stints **before** calculating rates.

## Caveats and interpretation

- **Birth country is not nationality, signing route, international free-agent eligibility, or where a player was scouted.** Country strings are those used by SABR (e.g., `D.R.`). U.S. territory coding may differ from other definitions of "international".
- Historical MLB outcomes have strong **survivorship and selection bias**; high-performing MLB players are not a representative sample of international prospects.
- Counts are **hitter-seasons, not unique people** across the full period. One athlete can appear in multiple years.
- Data are through 2025 only. No minor-league, international amateur, biomechanical, video, contract, or proprietary information is included.
- An OPS comparison **does not adjust for park effects, league context, era, defensive value, or role**. No causal inference or player-valuation claims should be drawn from this descriptive exercise.
- Some player-country fields can be missing; see generated quality report.

## SQL example

The full query is in [`sql/analysis.sql`](sql/analysis.sql). It demonstrates a `GROUP BY` player-season across stints, a join against player metadata, `NULLIF` denominator protection, and an explicit sample definition.

## How I would extend it for an actual baseball operations workflow

- Add full schema contracts, reproducible data snapshots, more granular source provenance, and automated anomaly alerts.
- Integrate legitimately accessible minor-league/international amateur data and establish consistent identities across vendors and leagues.
- Build park- and league-adjusted performance measures with uncertainty estimates and validation against held-out seasons.
- Create an analyst-facing review interface with links back to source records, not just a ranking.

## Tests

`python -m unittest discover -s tests -v` verifies proper multi-stint aggregation, rate calculations, exclusion of U.S.-born rows, missing-denominator handling, and rejection of invalid or duplicate batting lines. Test cases use **synthetic fixtures only**, clearly separated from the SABR source dataset.

## Data sources and licensing

- Official dataset: [SABR Lahman Baseball Database](https://sabr.org/lahman-database/), 2025 release, © SABR and Sean Lahman; **CC BY-SA 3.0**.
- Script-friendly, attributed mirror: [myceliumdata/lahman-seed](https://github.com/myceliumdata/lahman-seed) (`lahman_1871-2025_csv/`).
- Project source code licensed under MIT; the downloaded dataset retains its separate CC BY-SA terms.

## Portfolio note

This repository is an independently developed educational project, **not affiliated with or endorsed by the Los Angeles Dodgers or MLB**. If using this in a job application, describe what you personally understand and can explain, and be transparent about any assisted code generation.
