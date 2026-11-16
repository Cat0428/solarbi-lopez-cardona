# Inventario de la capa Bronze · reconstrucción desde GitHub (opencem-github.sqlite)

Generado: 2026-11-14T22:11:04-05:00

## Base `opencem-github.sqlite` (1,081.5 MB descomprimida)

| Tabla | Filas | Columnas | Periodo |
|---|---:|---:|---|
| `analog_measurements` | 4,021,635 | 83 | read_ts: 2025-07-12T13:31:35+00:00 → 2026-04-11T18:29:20+00:00 |
| `context` | 29,990 | 6 | recorded: 2024-07-27T10:00:00+00:00 → 2026-01-11T06:28:04+00:00<br>start: 2024-04-30T16:00:00+00:00 → 2026-07-19T16:00:00+00:00 |

### `analog_measurements` · 4,021,635 filas

| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |
|---|---|---|---:|---:|---|---|---|
| `read_ts` | INTEGER |  | 0 | 1,410,937 | 2025-07-12T13:31:35+00:00 | 2026-04-11T18:29:20+00:00 |  |
| `inverter` | INTEGER |  | 0 | 2 | 1 | 2 |  |
| `battvolt` | REAL |  | 3,503 | 98 | 24.7 | 57.6 |  |
| `battcurr` | REAL |  | 3,722 | 1,494 | -62.8 | 6553.5 |  |
| `battsoc` | REAL |  | 3,278 | 91 | 10.0 | 100.0 |  |
| `battchgpower` | REAL |  | 3,731 | 2,783 | 0.0 | 3475.0 |  |
| `linechgcurr` | REAL |  | 3,462 | 163 | 0.0 | 18.7 |  |
| `pvchgcurr` | REAL |  | 3,472 | 557 | 0.0 | 64.1 |  |
| `battreserve` | TEXT |  | 3,000,008 | 1 |  |  |  |
| `pv1volt` | REAL |  | 5,435 | 4,139 | 0.0 | 492.6 |  |
| `pv1curr` | REAL |  | 3,371 | 100 | 0.0 | 10.6 |  |
| `pv1power` | REAL |  | 4,453 | 3,211 | 0.0 | 3933.0 |  |
| `pv2volt` | REAL |  | 3,835,276 | 1 | 0.0 | 0.0 |  |
| `pv2curr` | REAL |  | 3,835,785 | 1 | 0.0 | 0.0 |  |
| `pv2power` | REAL |  | 3,835,159 | 1 | 0.0 | 0.0 |  |
| `pv3volt` | REAL |  | 3,835,254 | 1 | 0.0 | 0.0 |  |
| `pv3curr` | REAL |  | 3,835,216 | 1 | 0.0 | 0.0 |  |
| `pv3power` | REAL |  | 3,835,290 | 1 | 0.0 | 0.0 |  |
| `pvreserve` | TEXT |  | 2,999,767 | 1 |  |  |  |
| `outvolta` | REAL |  | 6,370 | 167 | 0.0 | 242.3 |  |
| `outcurra` | REAL |  | 3,411 | 142 | 0.0 | 19.7 |  |
| `outfreq` | REAL |  | 4,722 | 18 | 0.0 | 50.07 |  |
| `invcurra` | REAL |  | 3,402 | 115 | 0.0 | 16.6 |  |
| `outw_a` | REAL |  | 4,248 | 1,925 | 0.0 | 5539.0 |  |
| `outva_a` | REAL |  | 3,415 | 1,560 | 0.0 | 5604.0 |  |
| `loadpercenta` | REAL |  | 3,614 | 74 | 0.0 | 102.0 |  |
| `normalloadw_a` | REAL |  | 3,533 | 1 | 0.0 | 0.0 |  |
| `outvoltb` | REAL |  | 3,835,187 | 1 | 0.0 | 0.0 |  |
| `outcurrb` | REAL |  | 3,835,209 | 165 | 0.1 | 35.7 |  |
| `invcurrb` | REAL |  | 3,835,092 | 1 | 0.0 | 0.0 |  |
| `outw_b` | REAL |  | 3,835,144 | 1 | 0.0 | 0.0 |  |
| `outva_b` | REAL |  | 3,835,275 | 1 | 0.0 | 0.0 |  |
| `loadpercentb` | REAL |  | 3,835,158 | 1 | 0.0 | 0.0 |  |
| `normalloadw_b` | REAL |  | 3,835,245 | 1 | 0.0 | 0.0 |  |
| `outvoltc` | REAL |  | 3,835,149 | 1 | 0.0 | 0.0 |  |
| `outcurrc` | REAL |  | 3,835,186 | 1 | 0.0 | 0.0 |  |
| `invcurrc` | REAL |  | 3,835,194 | 1 | 0.0 | 0.0 |  |
| `outw_c` | REAL |  | 3,835,172 | 1 | 0.0 | 0.0 |  |
| `outva_c` | REAL |  | 3,835,223 | 1 | 0.0 | 0.0 |  |
| `loadpercentc` | REAL |  | 3,835,139 | 1 | 0.0 | 0.0 |  |
| `normalloadw_c` | REAL |  | 3,835,177 | 1 | 0.0 | 0.0 |  |
| `outsumw` | REAL |  | 3,597 | 1,903 | 0.0 | 5502.0 |  |
| `outsumva` | REAL |  | 3,479 | 1,544 | 0.0 | 5664.0 |  |
| `sumloadpercent` | REAL |  | 3,498 | 70 | 0.0 | 100.0 |  |
| `generatedpowerp_a` | REAL |  | 3,575 | 2,064 | -1519.0 | 65535.0 |  |
| `generatedpowerp_b` | REAL |  | 3,835,173 | 1 | 0.0 | 0.0 |  |
| `generatedpowerp_c` | REAL |  | 3,835,286 | 1 | 0.0 | 0.0 |  |
| `generatedpowers_a` | REAL |  | 3,360 | 1 | 0.0 | 0.0 |  |
| `generatedpowers_b` | REAL |  | 3,835,269 | 1 | 0.0 | 0.0 |  |
| `generatedpowers_c` | REAL |  | 3,835,190 | 1 | 0.0 | 0.0 |  |
| `generatedpowerq_a` | REAL |  | 3,587 | 1 | 0.0 | 0.0 |  |
| `generatedpowerq_b` | REAL |  | 3,835,227 | 1 | 0.0 | 0.0 |  |
| `generatedpowerq_c` | REAL |  | 3,835,158 | 1 | 0.0 | 0.0 |  |
| `linevolta` | REAL |  | 3,562 | 326 | 72.6 | 241.8 |  |
| `linecurra` | REAL |  | 3,656 | 137 | 0.0 | 6549.2 |  |
| `linefreq` | REAL |  | 3,329 | 16 | 49.92 | 50.07 |  |
| `linevoltb` | REAL |  | 3,835,204 | 1 | 0.0 | 0.0 |  |
| `linecurrb` | REAL |  | 3,835,217 | 1 | 0.0 | 0.0 |  |
| `linevoltc` | REAL |  | 3,835,217 | 1 | 0.0 | 0.0 |  |
| `linecurrc` | REAL |  | 3,835,258 | 1 | 0.0 | 0.0 |  |
| `linepowerva_a` | REAL |  | 3,465 | 2,219 | 0.0 | 64637.0 |  |
| `linepowerva_b` | REAL |  | 3,835,223 | 1 | 0.0 | 0.0 |  |
| `linepowerva_c` | REAL |  | 3,835,215 | 1 | 0.0 | 0.0 |  |
| `linepowerw_a` | REAL |  | 3,489 | 2,399 | 0.0 | 65527.0 |  |
| `linepowerw_b` | REAL |  | 3,835,284 | 1 | 0.0 | 0.0 |  |
| `linepowerw_c` | REAL |  | 3,835,225 | 1 | 0.0 | 0.0 |  |
| `busvoltp` | REAL |  | 3,509 | 1,416 | 26.8 | 508.2 |  |
| `busvoltn` | REAL |  | 3,468 | 1 | 0.0 | 0.0 |  |
| `temper1` | REAL |  | 3,966 | 370 | 10.6 | 48.0 |  |
| `temper2` | REAL |  | 4,253 | 361 | 17.2 | 54.0 |  |
| `temper3` | REAL |  | 3,299 | 419 | 19.3 | 61.2 |  |
| `temper4` | REAL |  | 3,467 | 1 | 120.0 | 120.0 |  |
| `sir` | REAL |  | 3,609 | 1 | 0.0 | 0.0 |  |
| `fanduty` | REAL |  | 3,642 | 1 | 0.0 | 0.0 |  |
| `otherreserve` | TEXT |  | 3,000,035 | 1 |  |  |  |
| `gridpowerw_a` | REAL |  | 4,962 | 157 | 0.0 | 65535.0 |  |
| `gridpowerw_b` | REAL |  | 3,835,060 | 1 | 0.0 | 0.0 |  |
| `gridpowerw_c` | REAL |  | 3,836,019 | 1 | 0.0 | 0.0 |  |
| `gridcurr_a` | REAL |  | 4,058 | 12 | 0.4 | 25.8 |  |
| `gridcurr_b` | REAL |  | 3,835,746 | 1 | 0.0 | 0.0 |  |
| `gridcurr_c` | REAL |  | 3,835,163 | 1 | 0.0 | 0.0 |  |
| `grid_reserve` | TEXT |  | 3,001,014 | 1 |  |  |  |
| `_archivo` | TEXT |  | 0 | 19 |  |  |  |

### `context` · 29,990 filas

| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |
|---|---|---|---:|---:|---|---|---|
| `id` | INTEGER |  | 0 | 14,995 | 1 | 14995 |  |
| `recorded` | INTEGER |  | 0 | 14,938 | 2024-07-27T10:00:00+00:00 | 2026-01-11T06:28:04+00:00 |  |
| `start` | INTEGER |  | 0 | 14,977 | 2024-04-30T16:00:00+00:00 | 2026-07-19T16:00:00+00:00 |  |
| `end` | INTEGER |  | 0 | 14,973 | 2024-05-05T16:00:00+00:00 | 2026-07-22T15:59:59+00:00 |  |
| `value` | TEXT |  | 0 | 3,083 |  |  | 29980/29990 valores son JSON |
| `_archivo` | TEXT |  | 0 | 20 |  |  |  |
