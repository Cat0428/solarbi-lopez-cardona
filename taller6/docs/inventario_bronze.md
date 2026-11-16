# Inventario de la capa Bronze · OpenCEM v1.0.0

Generado: 2026-11-15T18:10:48-05:00

## Integridad (SHA-256)

Verificado en el equipo del autor el 15/11/2026 con `sha256sum` contra
`opencem-v1.0.0-SHA256SUMS.txt` (Zenodo) y contra `manifests/release_manifest.json` (dentro del
`support.zip`) para la base ya descomprimida.

| Archivo | SHA-256 esperado | SHA-256 calculado | Estado |
|---|---|---|---|
| `opencem-v1.0.0.sqlite.zst` (302 059 978 B) | `8e38f982…7b27517` | `8e38f98209029367a3775799ee9a7c0757cc7e8f2742e4df4eccc45dd4b27517` | ✅ OK |
| `opencem-v1.0.0-support.zip` (9 972 654 B) | `5debdbeb…2f460439` | `5debdbebb82ed784e1c11ac70c81fe876400a049a001a8dc2230446e2f460439` | ✅ OK |
| `opencem-v1.0.0.sqlite` descomprimida (4 439 408 640 B) | `5fe1f213…a6283fa` | `5fe1f213a4a6804cdfc75f6173f437772c918f45dc0f127eb7e8936c2c2d9fbb` | ✅ OK |
| `opencem-v1.0.0-sky-2026-0[3-7].tar.zst` | — | — | No descargados (imágenes de cielo, fuera del alcance) |

Descompresión: `zstd -d opencem-v1.0.0.sqlite.zst -o opencem-v1.0.0.sqlite` (zstd 1.4.8 en el equipo del autor, o
`scripts/preparar_bronze.ps1`, que usa zstd dentro de un contenedor alpine). La base se abre siempre
con `mode=ro&immutable=1`: la capa Bronze nunca se modifica.

## Base `opencem-v1.0.0.sqlite` (4,439.4 MB descomprimida)

| Tabla | Filas | Columnas | Periodo |
|---|---:|---:|---|
| `analog_measurements` | 2,989,759 | 44 | read_ts: 2025-07-12T13:31:35.265811+00:00 → 2026-07-13T05:13:53.451776+00:00 |
| `context` | 25,178 | 5 | recorded: 2024-07-27T10:00:00+00:00 → 2026-07-14T10:59:48+00:00<br>start: 2024-04-30T16:00:00+00:00 → 2026-07-19T16:00:00+00:00 |
| `fault_history` | 2,129,517 | 66 | read_ts: 2025-07-12T13:31:35.265811+00:00 → 2026-07-13T05:13:53.451776+00:00 |
| `settings` | 2,284,775 | 176 | read_ts: 2025-07-12T13:31:35.265811+00:00 → 2026-07-13T05:13:53.451776+00:00 |
| `specs` | 1,333,174 | 16 | read_ts: 2025-07-12T13:31:35.265811+00:00 → 2026-02-02T18:40:30.734813+00:00 |
| `statistics` | 2,285,904 | 31 | read_ts: 2025-07-12T13:31:35.265811+00:00 → 2026-07-13T05:13:53.451776+00:00 |
| `status` | 2,240,052 | 20 | read_ts: 2025-07-12T13:31:35.265811+00:00 → 2026-07-13T05:13:53.451776+00:00 |
| `totals` | 2,279,918 | 21 | read_ts: 2025-07-12T13:31:35.265811+00:00 → 2026-07-13T05:13:53.451776+00:00 |

### `analog_measurements` · 2,989,759 filas

| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |
|---|---|---|---:|---:|---|---|---|
| `read_ts` | REAL |  | 0 | 1,613,729 | 2025-07-12T13:31:35.265811+00:00 | 2026-07-13T05:13:53.451776+00:00 |  |
| `inverter` | INTEGER |  | 0 | 2 | 1 | 2 |  |
| `battvolt` | REAL |  | 58,141 | 110 | 0.0 | 57.6 |  |
| `battcurr` | REAL |  | 58,217 | 1,066 | -66.3 | 54.0 |  |
| `battsoc` | INTEGER |  | 57,931 | 95 | 6 | 100 |  |
| `battchgpower` | INTEGER |  | 58,171 | 2,842 | 0 | 3475 |  |
| `linechgcurr` | REAL |  | 58,071 | 163 | 0.0 | 18.7 |  |
| `pvchgcurr` | REAL |  | 58,071 | 577 | 0.0 | 64.1 |  |
| `battreserve` | TEXT |  | 3,828 | 2 |  |  | 2985931/2985931 valores son JSON |
| `pv1volt` | REAL |  | 59,379 | 4,139 | 0.0 | 492.6 |  |
| `pv1curr` | REAL |  | 58,001 | 103 | 0.0 | 10.6 |  |
| `pv1power` | INTEGER |  | 58,660 | 3,292 | 0 | 3933 |  |
| `pvreserve` | TEXT |  | 3,346 | 2 |  |  | 2986413/2986413 valores son JSON |
| `outvolta` | REAL |  | 59,953 | 946 | 0.0 | 242.3 |  |
| `outcurra` | REAL |  | 58,093 | 142 | 0.0 | 19.7 |  |
| `outfreq` | REAL |  | 58,841 | 18 | 0.0 | 50.07 |  |
| `invcurra` | REAL |  | 57,962 | 119 | 0.0 | 16.6 |  |
| `outw_a` | INTEGER |  | 58,521 | 1,931 | 0 | 5539 |  |
| `outva_a` | INTEGER |  | 58,013 | 1,563 | 0 | 5604 |  |
| `loadpercenta` | INTEGER |  | 58,141 | 74 | 0 | 102 |  |
| `normalloadw_a` | INTEGER |  | 58,041 | 1 | 0 | 0 |  |
| `outsumw` | INTEGER |  | 58,153 | 1,909 | 0 | 5502 |  |
| `outsumva` | INTEGER |  | 58,036 | 1,547 | 0 | 5664 |  |
| `sumloadpercent` | INTEGER |  | 58,096 | 70 | 0 | 100 |  |
| `generatedpowerp_a` | INTEGER |  | 58,080 | 1,040 | -1519 | 29 |  |
| `generatedpowers_a` | INTEGER |  | 57,962 | 1 | 0 | 0 |  |
| `generatedpowerq_a` | INTEGER |  | 58,117 | 1 | 0 | 0 |  |
| `linevolta` | REAL |  | 58,083 | 418 | 0.0 | 306.2 |  |
| `linecurra` | REAL |  | 58,149 | 137 | -4.4 | 27.7 |  |
| `linefreq` | REAL |  | 57,959 | 17 | 0.0 | 50.07 |  |
| `linepowerva_a` | INTEGER |  | 58,060 | 2,230 | -1044 | 5014 |  |
| `linepowerw_a` | INTEGER |  | 58,062 | 2,417 | -146 | 6180 |  |
| `busvoltp` | REAL |  | 58,084 | 4,642 | 0.0 | 508.7 |  |
| `busvoltn` | REAL |  | 58,040 | 1 | 0.0 | 0.0 |  |
| `temper1` | REAL |  | 58,299 | 374 | -20.3 | 49.3 |  |
| `temper2` | REAL |  | 58,396 | 362 | 17.2 | 56.5 |  |
| `temper3` | REAL |  | 57,814 | 419 | 19.3 | 61.2 |  |
| `temper4` | REAL |  | 58,036 | 1 | 120.0 | 120.0 |  |
| `sir` | INTEGER |  | 58,111 | 1 | 0 | 0 |  |
| `fanduty` | INTEGER |  | 57,909 | 1 | 0 | 0 |  |
| `otherreserve` | TEXT |  | 4,043 | 2 |  |  | 2985716/2985716 valores son JSON |
| `gridpowerw_a` | INTEGER |  | 58,968 | 184 | -822 | 196 |  |
| `gridcurr_a` | REAL |  | 58,563 | 13 | 0.0 | 25.8 |  |
| `grid_reserve` | TEXT |  | 5,957 | 2 |  |  | 2983802/2983802 valores son JSON |

### `context` · 25,178 filas

| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |
|---|---|---|---:|---:|---|---|---|
| `id` | INTEGER | ✓ | 0 | 25,178 | 1 | 44747 |  |
| `recorded` | INTEGER |  | 0 | 24,614 | 2024-07-27T10:00:00+00:00 | 2026-07-14T10:59:48+00:00 |  |
| `start` | INTEGER |  | 0 | 24,638 | 2024-04-30T16:00:00+00:00 | 2026-07-19T16:00:00+00:00 |  |
| `end` | INTEGER |  | 0 | 24,577 | 2024-05-05T16:00:00+00:00 | 2026-07-22T15:59:59+00:00 |  |
| `value` | TEXT |  | 0 | 13,266 |  |  | 25178/25178 valores son JSON |

### `fault_history` · 2,129,517 filas

| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |
|---|---|---|---:|---:|---|---|---|
| `read_ts` | REAL |  | 0 | 1,178,596 | 2025-07-12T13:31:35.265811+00:00 | 2026-07-13T05:13:53.451776+00:00 |  |
| `inverter` | INTEGER |  | 0 | 2 | 1 | 2 |  |
| `faulthistoryrecord00` | TEXT |  | 5,882 | 2,567 |  |  | 2123635/2123635 valores son JSON |
| `faulthistoryrecord01` | TEXT |  | 5,073 | 2,570 |  |  | 2124444/2124444 valores son JSON |
| `faulthistoryrecord02` | TEXT |  | 5,524 | 2,570 |  |  | 2123993/2123993 valores son JSON |
| `faulthistoryrecord03` | TEXT |  | 2,035,803 | 408 |  |  | 93714/93714 valores son JSON |
| `faulthistoryrecord04` | TEXT |  | 2,035,768 | 408 |  |  | 93749/93749 valores son JSON |
| `faulthistoryrecord05` | TEXT |  | 2,035,789 | 409 |  |  | 93728/93728 valores son JSON |
| `faulthistoryrecord06` | TEXT |  | 2,035,806 | 410 |  |  | 93711/93711 valores son JSON |
| `faulthistoryrecord07` | TEXT |  | 2,035,759 | 410 |  |  | 93758/93758 valores son JSON |
| `faulthistoryrecord08` | TEXT |  | 2,035,811 | 411 |  |  | 93706/93706 valores son JSON |
| `faulthistoryrecord09` | TEXT |  | 2,035,812 | 410 |  |  | 93705/93705 valores son JSON |
| `faulthistoryrecord10` | TEXT |  | 2,035,783 | 410 |  |  | 93734/93734 valores son JSON |
| `faulthistoryrecord11` | TEXT |  | 2,035,822 | 410 |  |  | 93695/93695 valores son JSON |
| `faulthistoryrecord12` | TEXT |  | 2,035,806 | 410 |  |  | 93711/93711 valores son JSON |
| `faulthistoryrecord13` | TEXT |  | 2,035,770 | 410 |  |  | 93747/93747 valores son JSON |
| `faulthistoryrecord14` | TEXT |  | 2,035,815 | 410 |  |  | 93702/93702 valores son JSON |
| `faulthistoryrecord15` | TEXT |  | 2,035,829 | 410 |  |  | 93688/93688 valores son JSON |
| `faulthistoryrecord16` | TEXT |  | 2,035,800 | 409 |  |  | 93717/93717 valores son JSON |
| `faulthistoryrecord17` | TEXT |  | 2,035,789 | 409 |  |  | 93728/93728 valores son JSON |
| `faulthistoryrecord18` | TEXT |  | 2,035,804 | 409 |  |  | 93713/93713 valores son JSON |
| `faulthistoryrecord19` | TEXT |  | 2,035,821 | 408 |  |  | 93696/93696 valores son JSON |
| `faulthistoryrecord20` | TEXT |  | 2,035,835 | 408 |  |  | 93682/93682 valores son JSON |
| `faulthistoryrecord21` | TEXT |  | 2,035,796 | 408 |  |  | 93721/93721 valores son JSON |
| `faulthistoryrecord22` | TEXT |  | 2,035,792 | 408 |  |  | 93725/93725 valores son JSON |
| `faulthistoryrecord23` | TEXT |  | 2,035,801 | 408 |  |  | 93716/93716 valores son JSON |
| `faulthistoryrecord24` | TEXT |  | 2,035,745 | 408 |  |  | 93772/93772 valores son JSON |
| `faulthistoryrecord25` | TEXT |  | 2,035,828 | 408 |  |  | 93689/93689 valores son JSON |
| `faulthistoryrecord26` | TEXT |  | 2,035,833 | 409 |  |  | 93684/93684 valores son JSON |
| `faulthistoryrecord27` | TEXT |  | 2,035,804 | 409 |  |  | 93713/93713 valores son JSON |
| `faulthistoryrecord28` | TEXT |  | 2,035,751 | 409 |  |  | 93766/93766 valores son JSON |
| `faulthistoryrecord29` | TEXT |  | 2,035,807 | 411 |  |  | 93710/93710 valores son JSON |
| `faulthistoryrecord30` | TEXT |  | 2,035,831 | 410 |  |  | 93686/93686 valores son JSON |
| `faulthistoryrecord31` | TEXT |  | 2,035,780 | 408 |  |  | 93737/93737 valores son JSON |
| `faulthistoryrecord00_time` | REAL |  | 84,395 | 2,858 | 1751083387.480223 | 1783913279.785157 |  |
| `faulthistoryrecord01_time` | REAL |  | 83,489 | 2,868 | 1751084491.480223 | 1783913300.785157 |  |
| `faulthistoryrecord02_time` | REAL |  | 83,827 | 2,872 | 1751084491.480223 | 1783913322.785157 |  |
| `faulthistoryrecord03_time` | REAL |  | 2,057,367 | 377 | 1751084491.480223 | 1761260728.868479 |  |
| `faulthistoryrecord04_time` | REAL |  | 2,057,377 | 377 | 1751084557.480223 | 1761260748.868478 |  |
| `faulthistoryrecord05_time` | REAL |  | 2,057,563 | 377 | 1751332377.480223 | 1761260770.868478 |  |
| `faulthistoryrecord06_time` | REAL |  | 2,057,574 | 378 | 1751338641.480223 | 1761260792.868478 |  |
| `faulthistoryrecord07_time` | REAL |  | 2,057,538 | 378 | 1751338790.480223 | 1761260813.868478 |  |
| `faulthistoryrecord08_time` | REAL |  | 2,058,008 | 381 | 1751342863.480223 | 1761260826.868478 |  |
| `faulthistoryrecord09_time` | REAL |  | 2,057,977 | 379 | 1751674756.480223 | 1761261557.679113 |  |
| `faulthistoryrecord10_time` | REAL |  | 2,057,943 | 379 | 1751677192.480223 | 1761261577.679113 |  |
| `faulthistoryrecord11_time` | REAL |  | 2,057,959 | 378 | 1751677195.480223 | 1761261597.679113 |  |
| `faulthistoryrecord12_time` | REAL |  | 2,057,960 | 378 | 1752029221.480223 | 1761261615.679113 |  |
| `faulthistoryrecord13_time` | REAL |  | 2,057,935 | 378 | 1752033650.480223 | 1761261633.679113 |  |
| `faulthistoryrecord14_time` | REAL |  | 2,057,950 | 378 | 1752302130.480223 | 1761261649.176876 |  |
| `faulthistoryrecord15_time` | REAL |  | 2,058,183 | 377 | 1752302152.480223 | 1761261662.176876 |  |
| `faulthistoryrecord16_time` | REAL |  | 2,058,135 | 376 | 1752302221.480223 | 1761254181.434292 |  |
| `faulthistoryrecord17_time` | REAL |  | 2,058,148 | 376 | 1752302223.480223 | 1761254194.434292 |  |
| `faulthistoryrecord18_time` | REAL |  | 2,058,012 | 375 | 1752302609.480223 | 1761256301.893208 |  |
| `faulthistoryrecord19_time` | REAL |  | 2,058,051 | 374 | 1752302921.480223 | 1761256323.644785 |  |
| `faulthistoryrecord20_time` | REAL |  | 2,058,064 | 374 | 1752303732.480223 | 1761256343.644785 |  |
| `faulthistoryrecord21_time` | REAL |  | 2,058,049 | 373 | 1752304007.480223 | 1761256361.644785 |  |
| `faulthistoryrecord22_time` | REAL |  | 2,057,619 | 375 | 1752304133.480223 | 1761256379.644785 |  |
| `faulthistoryrecord23_time` | REAL |  | 2,057,623 | 375 | 1752305019.480223 | 1761256397.644785 |  |
| `faulthistoryrecord24_time` | REAL |  | 2,057,589 | 375 | 1752306059.480223 | 1761260477.417555 |  |
| `faulthistoryrecord25_time` | REAL |  | 2,057,658 | 376 | 1752308246.480223 | 1761260506.417555 |  |
| `faulthistoryrecord26_time` | REAL |  | 2,057,674 | 377 | 1751082968.480223 | 1761260532.868478 |  |
| `faulthistoryrecord27_time` | REAL |  | 2,057,668 | 377 | 1751083000.480223 | 1761260555.868478 |  |
| `faulthistoryrecord28_time` | REAL |  | 2,062,295 | 376 | 1751083000.480223 | 1761260579.868478 |  |
| `faulthistoryrecord29_time` | REAL |  | 2,059,580 | 378 | 1751083141.480223 | 1761260600.868478 |  |
| `faulthistoryrecord30_time` | REAL |  | 2,057,681 | 378 | 1751083141.480223 | 1761260622.868478 |  |
| `faulthistoryrecord31_time` | REAL |  | 2,057,653 | 376 | 1751083142.480223 | 1761260644.868479 |  |

### `settings` · 2,284,775 filas

| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |
|---|---|---|---:|---:|---|---|---|
| `read_ts` | REAL |  | 0 | 1,283,505 | 2025-07-12T13:31:35.265811+00:00 | 2026-07-13T05:13:53.451776+00:00 |  |
| `inverter` | INTEGER |  | 0 | 2 | 1 | 2 |  |
| `outpriority` | INTEGER |  | 58,664 | 2 | 0 | 2 |  |
| `outvoltset` | REAL |  | 58,317 | 1 | 230.0 | 230.0 |  |
| `outfreqset` | REAL |  | 58,409 | 1 | 50.0 | 50.0 |  |
| `linerangeset` | INTEGER |  | 58,785 | 1 | 0 | 0 |  |
| `paramodeset` | INTEGER |  | 58,483 | 1 | 0 | 0 |  |
| `ecoen` | INTEGER |  | 58,602 | 1 | 0 | 0 |  |
| `chgpriority` | INTEGER |  | 58,525 | 2 | 2 | 3 |  |
| `maxchgcurrset` | REAL |  | 58,290 | 1 | 80.0 | 80.0 |  |
| `chgcurrbypvset` | REAL |  | 58,585 | 1 | 80.0 | 80.0 |  |
| `chgcurrbylineset` | REAL |  | 58,394 | 1 | 15.0 | 15.0 |  |
| `commidset` | INTEGER |  | 58,399 | 1 | 1 | 1 |  |
| `muteen` | INTEGER |  | 58,485 | 1 | 0 | 0 |  |
| `ongirdset` | INTEGER |  | 58,617 | 1 | 0 | 0 |  |
| `chgfullcurrset` | REAL |  | 58,342 | 1 | 3.0 | 3.0 |  |
| `ng_funcen` | INTEGER |  | 58,400 | 1 | 0 | 0 |  |
| `leakagechecken` | INTEGER |  | 2,190,730 | 1 | 0 | 0 |  |
| `userpassword` | INTEGER |  | 2,190,736 | 1 | 0 | 0 |  |
| `passwordset` | INTEGER |  | 2,190,741 | 1 | 0 | 0 |  |
| `ctrlflag1` | INTEGER |  | 59,204 | 1 | 0 | 0 |  |
| `battactiveset` | INTEGER |  | 58,859 | 1 | 1 | 1 |  |
| `ongridactivepowerset` | INTEGER |  | 58,804 | 1 | 0 | 0 |  |
| `ongridreactivepowerset` | INTEGER |  | 58,397 | 1 | 0 | 0 |  |
| `hybirdpriorityen` | INTEGER |  | 58,646 | 1 | 0 | 0 |  |
| `ongridpfset` | REAL |  | 58,569 | 1 | 1.0 | 1.0 |  |
| `gridstandardset` | INTEGER |  | 58,272 | 1 | 0 | 0 |  |
| `isodetecten` | INTEGER |  | 58,601 | 1 | 0 | 0 |  |
| `lowisovalue` | INTEGER |  | 58,772 | 1 | 20 | 20 |  |
| `maxlinepower` | INTEGER |  | 58,438 | 2 | 5600 | 6200 |  |
| `extctgethosten` | INTEGER |  | 58,452 | 1 | 0 | 0 |  |
| `outphasediffset` | INTEGER |  | 58,303 | 1 | 0 | 0 |  |
| `powerturboen` | INTEGER |  | 58,342 | 1 | 0 | 0 |  |
| `acoverlaodrestaren` | INTEGER |  | 58,538 | 1 | 1 | 1 |  |
| `gridconnectvoltmax` | INTEGER |  | 58,427 | 1 | 109 | 109 |  |
| `gridconnectvoltmin` | INTEGER |  | 58,684 | 1 | 85 | 85 |  |
| `gridconnectfreqmax` | REAL |  | 58,869 | 1 | 50.1 | 50.1 |  |
| `gridconnectfreqmin` | REAL |  | 58,363 | 1 | 47.5 | 47.5 |  |
| `gridreconnectvoltmax` | INTEGER |  | 58,328 | 1 | 109 | 109 |  |
| `gridreconnectvoltmin` | INTEGER |  | 58,414 | 1 | 85 | 85 |  |
| `gridreconnectfreqmax` | REAL |  | 58,425 | 1 | 50.1 | 50.1 |  |
| `gridreconnectfreqmin` | REAL |  | 58,380 | 1 | 47.5 | 47.5 |  |
| `gridovlevel1` | INTEGER |  | 58,525 | 1 | 115 | 115 |  |
| `gridovdelaytime1` | REAL |  | 58,497 | 1 | 0.12 | 0.12 |  |
| `gridovlevel2` | INTEGER |  | 58,097 | 1 | 115 | 115 |  |
| `gridovdelaytime2` | REAL |  | 58,256 | 1 | 0.12 | 0.12 |  |
| `griduvlevel1` | INTEGER |  | 58,453 | 1 | 80 | 80 |  |
| `griduvdelaytime1` | REAL |  | 58,448 | 1 | 1.5 | 1.5 |  |
| `griduvlevel2` | INTEGER |  | 58,740 | 1 | 25 | 25 |  |
| `griduvdelaytime2` | REAL |  | 58,111 | 1 | 0.0 | 0.0 |  |
| `ov10minprotectvalue` | INTEGER |  | 58,455 | 1 | 110 | 110 |  |
| `gridoflevel1` | REAL |  | 58,499 | 1 | 51.5 | 51.5 |  |
| `gridofdelaytime1` | REAL |  | 58,695 | 1 | 0.1 | 0.1 |  |
| `gridoflevel2` | REAL |  | 58,562 | 1 | 51.5 | 51.5 |  |
| `gridofdelaytime2` | REAL |  | 58,372 | 1 | 0.1 | 0.1 |  |
| `griduflevel1` | REAL |  | 58,575 | 1 | 47.5 | 47.5 |  |
| `gridufdelaytime1` | REAL |  | 58,258 | 1 | 0.1 | 0.1 |  |
| `griduflevel2` | REAL |  | 58,691 | 1 | 47.5 | 47.5 |  |
| `gridufdelaytime2` | REAL |  | 58,278 | 1 | 0.1 | 0.1 |  |
| `startongriddelay` | REAL |  | 58,803 | 1 | 60.0 | 60.0 |  |
| `loadingslope` | INTEGER |  | 58,255 | 1 | 300 | 300 |  |
| `ongridreconnectdelay` | REAL |  | 58,626 | 1 | 300.0 | 300.0 |  |
| `reloadingslope` | INTEGER |  | 58,598 | 1 | 300 | 300 |  |
| `powerdynamicrate` | INTEGER |  | 58,724 | 1 | 300 | 300 |  |
| `islanden` | INTEGER |  | 58,767 | 1 | 1 | 1 |  |
| `hvrten` | INTEGER |  | 58,372 | 1 | 0 | 0 |  |
| `lvrten` | INTEGER |  | 58,365 | 1 | 0 | 0 |  |
| `constreactpoweren` | INTEGER |  | 58,659 | 1 | 0 | 0 |  |
| `constpfen` | INTEGER |  | 58,746 | 1 | 0 | 0 |  |
| `f_pcurveen` | INTEGER |  | 58,391 | 1 | 0 | 0 |  |
| `p_qcurveen` | INTEGER |  | 58,259 | 1 | 0 | 0 |  |
| `u_pcurveen` | INTEGER |  | 58,366 | 1 | 0 | 0 |  |
| `u_qcurveen` | INTEGER |  | 58,691 | 1 | 0 | 0 |  |
| `drmen` | INTEGER |  | 58,629 | 1 | 0 | 0 |  |
| `remoteturnoffen` | INTEGER |  | 58,921 | 1 | 0 | 0 |  |
| `permitservice` | INTEGER |  | 58,324 | 1 | 1 | 1 |  |
| `reactpowerdynamicrate` | INTEGER |  | 58,446 | 1 | 300 | 300 |  |
| `reserve` | TEXT |  | 6,297 | 3 |  |  | 2278478/2278478 valores son JSON |
| `maxongridactivepower` | INTEGER |  | 58,627 | 1 | 0 | 0 |  |
| `maxlinecurr` | REAL |  | 58,781 | 1 | 0.0 | 0.0 |  |
| `smartmeterpower` | INTEGER |  | 58,819 | 1 | 0 | 0 |  |
| `battype` | INTEGER |  | 2,190,892 | 1 | 4 | 4 |  |
| `cvvolt` | REAL |  | 58,504 | 1 | 57.6 | 57.6 |  |
| `floatvolt` | REAL |  | 58,709 | 1 | 57.6 | 57.6 |  |
| `battovervolt` | REAL |  | 58,780 | 1 | 60.0 | 60.0 |  |
| `cvchgtimeset` | INTEGER |  | 58,798 | 1 | 120 | 120 |  |
| `cvchgbackvolt` | REAL |  | 58,780 | 1 | 46.4 | 46.4 |  |
| `inv2linevolt` | REAL |  | 58,791 | 1 | 42.8 | 42.8 |  |
| `lineback2invvolt` | REAL |  | 58,686 | 1 | 50.0 | 50.0 |  |
| `battlowvolt` | REAL |  | 58,579 | 1 | 43.2 | 43.2 |  |
| `battdelayoffvolt` | REAL |  | 58,418 | 2 | 42.0 | 45.2 |  |
| `batteodvolt` | REAL |  | 58,693 | 2 | 40.8 | 44.8 |  |
| `battdelayofftime` | INTEGER |  | 58,706 | 1 | 30 | 30 |  |
| `batteodbackvolt` | REAL |  | 58,441 | 1 | 46.0 | 46.0 |  |
| `bmsset` | INTEGER |  | 58,566 | 1 | 1 | 1 |  |
| `bmsprotocal` | INTEGER |  | 58,347 | 1 | 1 | 1 |  |
| `batsoclowalarm` | INTEGER |  | 58,327 | 1 | 15 | 15 |  |
| `batstopsoc` | INTEGER |  | 58,593 | 1 | 5 | 5 |  |
| `battfullsoc` | INTEGER |  | 58,855 | 2 | 95 | 100 |  |
| `inv2linesoc` | INTEGER |  | 58,784 | 1 | 10 | 10 |  |
| `lineback2invsoc` | INTEGER |  | 58,756 | 1 | 100 | 100 |  |
| `ontimechargeen` | INTEGER |  | 58,721 | 1 | 0 | 0 |  |
| `chargestarttime1` | INTEGER |  | 58,575 | 1 | 0 | 0 |  |
| `chargeendtime1` | INTEGER |  | 59,226 | 1 | 0 | 0 |  |
| `chargestarttime2` | INTEGER |  | 58,508 | 1 | 0 | 0 |  |
| `chargeendtime2` | INTEGER |  | 58,434 | 1 | 0 | 0 |  |
| `chargestarttime3` | INTEGER |  | 58,645 | 1 | 0 | 0 |  |
| `chargeendtime3` | INTEGER |  | 58,787 | 1 | 0 | 0 |  |
| `ontimedischgen` | INTEGER |  | 58,702 | 1 | 0 | 0 |  |
| `dischgstarttime1` | INTEGER |  | 58,439 | 1 | 0 | 0 |  |
| `dischgendtime1` | INTEGER |  | 58,584 | 1 | 0 | 0 |  |
| `dischgstarttime2` | INTEGER |  | 58,645 | 1 | 0 | 0 |  |
| `dischgendtime2` | INTEGER |  | 58,849 | 1 | 0 | 0 |  |
| `dischgstarttime3` | INTEGER |  | 58,813 | 1 | 0 | 0 |  |
| `dischgendtime3` | INTEGER |  | 59,053 | 1 | 0 | 0 |  |
| `battpacknotunion` | INTEGER |  | 58,789 | 1 | 0 | 0 |  |
| `forcechgstopsoc` | INTEGER |  | 58,420 | 1 | 10 | 10 |  |
| `battpackrateah` | INTEGER |  | 58,613 | 2 | 0 | 200 |  |
| `battsetreserve` | TEXT |  | 4,819 | 3 |  |  | 2279956/2279956 valores son JSON |
| `fp_of_start` | REAL |  | 59,478 | 1 | 0.0 | 0.0 |  |
| `fp_uf_start` | REAL |  | 59,187 | 1 | 0.0 | 0.0 |  |
| `fp_of_end` | REAL |  | 59,305 | 1 | 0.0 | 0.0 |  |
| `fp_uf_end` | REAL |  | 59,117 | 1 | 0.0 | 0.0 |  |
| `fp_of_dropslope` | INTEGER |  | 58,305 | 1 | 0 | 0 |  |
| `fp_uf_lodingslope` | INTEGER |  | 58,711 | 1 | 0 | 0 |  |
| `fp_actpowerresptr` | REAL |  | 58,861 | 1 | 0.0 | 0.0 |  |
| `pq_p1` | INTEGER |  | 58,444 | 1 | 0 | 0 |  |
| `pq_q1` | INTEGER |  | 59,124 | 1 | 0 | 0 |  |
| `pq_p2` | INTEGER |  | 58,883 | 1 | 0 | 0 |  |
| `pq_q2` | INTEGER |  | 58,611 | 1 | 0 | 0 |  |
| `pq_p3` | INTEGER |  | 58,753 | 1 | 0 | 0 |  |
| `pq_q3` | INTEGER |  | 58,884 | 1 | 0 | 0 |  |
| `pq_p1n` | INTEGER |  | 58,569 | 1 | 0 | 0 |  |
| `pq_q1n` | INTEGER |  | 58,423 | 1 | 0 | 0 |  |
| `pq_p2n` | INTEGER |  | 58,650 | 1 | 0 | 0 |  |
| `pq_q2n` | INTEGER |  | 58,833 | 1 | 0 | 0 |  |
| `pq_p3n` | INTEGER |  | 58,560 | 1 | 0 | 0 |  |
| `pq_q3n` | INTEGER |  | 58,631 | 1 | 0 | 0 |  |
| `pq_enablevolt` | INTEGER |  | 58,754 | 1 | 0 | 0 |  |
| `pq_disablevolt` | INTEGER |  | 58,764 | 1 | 0 | 0 |  |
| `up_v1` | INTEGER |  | 59,022 | 1 | 0 | 0 |  |
| `up_p1` | INTEGER |  | 58,745 | 1 | 0 | 0 |  |
| `up_v2` | INTEGER |  | 58,711 | 1 | 0 | 0 |  |
| `up_p2` | INTEGER |  | 58,798 | 1 | 0 | 0 |  |
| `up_actpowerresptr` | REAL |  | 58,798 | 1 | 0.0 | 0.0 |  |
| `up_v3` | INTEGER |  | 58,863 | 1 | 0 | 0 |  |
| `up_p3` | INTEGER |  | 59,121 | 1 | 0 | 0 |  |
| `up_v4` | INTEGER |  | 58,961 | 1 | 0 | 0 |  |
| `up_p4` | INTEGER |  | 58,898 | 1 | 0 | 0 |  |
| `uq_vref` | INTEGER |  | 58,932 | 1 | 0 | 0 |  |
| `uq_v1` | INTEGER |  | 58,841 | 1 | 0 | 0 |  |
| `uq_q1` | INTEGER |  | 58,884 | 1 | 0 | 0 |  |
| `uq_v2` | INTEGER |  | 58,662 | 1 | 0 | 0 |  |
| `uq_q2` | INTEGER |  | 59,419 | 1 | 0 | 0 |  |
| `uq_v3` | INTEGER |  | 58,955 | 1 | 0 | 0 |  |
| `uq_q3` | INTEGER |  | 58,677 | 1 | 0 | 0 |  |
| `uq_v4` | INTEGER |  | 58,690 | 1 | 0 | 0 |  |
| `uq_q4` | INTEGER |  | 58,776 | 1 | 0 | 0 |  |
| `uq_reactpowerresptr` | REAL |  | 58,744 | 1 | 0.0 | 0.0 |  |
| `uq_vrefautoen` | INTEGER |  | 58,858 | 1 | 0 | 0 |  |
| `uq_vrefresptr` | REAL |  | 58,760 | 1 | 0.0 | 0.0 |  |
| `uq_enablepower` | INTEGER |  | 58,948 | 1 | 0 | 0 |  |
| `uq_disablepower` | INTEGER |  | 58,785 | 1 | 0 | 0 |  |
| `hvrt_level1` | INTEGER |  | 58,958 | 1 | 0 | 0 |  |
| `hvrt_level1time` | REAL |  | 58,539 | 1 | 0.0 | 0.0 |  |
| `hvrt_level2` | INTEGER |  | 58,875 | 1 | 0 | 0 |  |
| `hvrt_level2time` | REAL |  | 58,850 | 1 | 0.0 | 0.0 |  |
| `hvrt_level3` | INTEGER |  | 58,677 | 1 | 0 | 0 |  |
| `hvrt_level3time` | REAL |  | 58,707 | 1 | 0.0 | 0.0 |  |
| `lvrt_level1` | INTEGER |  | 59,102 | 1 | 0 | 0 |  |
| `lvrt_level1time` | REAL |  | 58,990 | 1 | 0.0 | 0.0 |  |
| `lvrt_level2` | INTEGER |  | 59,223 | 1 | 0 | 0 |  |
| `lvrt_level2time` | REAL |  | 58,647 | 1 | 0.0 | 0.0 |  |
| `lvrt_level3` | INTEGER |  | 58,931 | 1 | 0 | 0 |  |
| `lvrt_level3time` | REAL |  | 58,889 | 1 | 0.0 | 0.0 |  |
| `presenttime` | REAL |  | 80,739 | 106,016 | 1752583208.480223 | 1783919526.662566 |  |

### `specs` · 1,333,174 filas

| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |
|---|---|---|---:|---:|---|---|---|
| `read_ts` | REAL |  | 0 | 688,323 | 2025-07-12T13:31:35.265811+00:00 | 2026-02-02T18:40:30.734813+00:00 |  |
| `inverter` | INTEGER |  | 0 | 2 | 1 | 2 |  |
| `machcode` | INTEGER |  | 1,239,106 | 2 | 0 | 10 |  |
| `producttype` | INTEGER |  | 1,239,104 | 1 | 0 | 0 |  |
| `manufacturename` | TEXT |  | 1,239,475 | 2 |  |  | 93699/93699 valores son JSON |
| `sourcesn` | TEXT |  | 1,240,533 | 4 |  |  | 92641/92641 valores son JSON |
| `hwver_m1` | INTEGER |  | 1,239,048 | 1 | 1 | 1 |  |
| `hwver_m2` | INTEGER |  | 1,239,546 | 1 | 6 | 6 |  |
| `hwver_s1` | INTEGER |  | 1,239,144 | 1 | 0 | 0 |  |
| `hwver_s2` | INTEGER |  | 1,239,379 | 1 | 0 | 0 |  |
| `protocolver` | INTEGER |  | 1,239,118 | 1 | 0 | 0 |  |
| `bmsver` | INTEGER |  | 1,239,206 | 1 | 78 | 78 |  |
| `libver` | TEXT |  | 1,239,199 | 3 |  |  | 93975/93975 valores son JSON |
| `cpubuidtime` | TEXT |  | 6,730 | 3 |  |  | 1326444/1326444 valores son JSON |
| `customsn` | TEXT |  | 6,412 | 4 |  |  | 1326762/1326762 valores son JSON |
| `prdreserve` | TEXT |  | 1,331,836 | 1 |  |  | 1338/1338 valores son JSON |

### `statistics` · 2,285,904 filas

| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |
|---|---|---|---:|---:|---|---|---|
| `read_ts` | REAL |  | 0 | 1,283,225 | 2025-07-12T13:31:35.265811+00:00 | 2026-07-13T05:13:53.451776+00:00 |  |
| `inverter` | INTEGER |  | 0 | 2 | 1 | 2 |  |
| `batchgenergylast7day` | TEXT |  | 4,582 | 505 |  |  | 2281322/2281322 valores son JSON |
| `batdischgenergylast7day` | TEXT |  | 3,991 | 506 |  |  | 2281913/2281913 valores son JSON |
| `linechgenergylast7day` | TEXT |  | 3,961 | 297 |  |  | 2281943/2281943 valores son JSON |
| `loadconsumlast7day` | TEXT |  | 3,823 | 456 |  |  | 2282081/2282081 valores son JSON |
| `loadconsumfromlinelast7day` | TEXT |  | 4,000 | 392 |  |  | 2281904/2281904 valores son JSON |
| `energyreserved0` | TEXT |  | 2,938 | 2 |  |  | 2282966/2282966 valores son JSON |
| `generatedacpowertoday` | REAL |  | 58,433 | 1 | 0.0 | 0.0 |  |
| `batchgenergytoday` | REAL |  | 58,419 | 93 | 0.0 | 10.3 |  |
| `batdischgenergytoday` | REAL |  | 58,166 | 96 | 0.0 | 9.7 |  |
| `pvgeneratenergytoday` | REAL |  | 58,392 | 129 | 0.0 | 12.8 |  |
| `usedenergytoday` | REAL |  | 58,226 | 342 | 0.0 | 34.1 |  |
| `workdaystotal` | INTEGER |  | 58,525 | 1 | 0 | 0 |  |
| `batchgenergytotal` | TEXT |  | 2,594 | 6,988 |  |  | 2283310/2283310 valores son JSON |
| `batdischgenergytotal` | TEXT |  | 3,121 | 7,165 |  |  | 2282783/2282783 valores son JSON |
| `pvgeneratenergytotal` | TEXT |  | 2,554 | 9,807 |  |  | 2283350/2283350 valores son JSON |
| `usedenergytotal` | TEXT |  | 3,351 | 28,897 |  |  | 2282553/2282553 valores son JSON |
| `linechgenergytday` | REAL |  | 58,395 | 84 | 0.0 | 8.3 |  |
| `loadconsumlinetday` | REAL |  | 58,311 | 328 | 0.0 | 34.1 |  |
| `invworktimetoday` | INTEGER |  | 58,289 | 25 | 0 | 24 |  |
| `lineworktimetoday` | INTEGER |  | 58,503 | 25 | 0 | 24 |  |
| `linechgenergytotal` | TEXT |  | 3,953 | 4,080 |  |  | 2281951/2281951 valores son JSON |
| `loadconsumlinetotal` | TEXT |  | 2,741 | 15,675 |  |  | 2283163/2283163 valores son JSON |
| `invworktimetotal` | INTEGER |  | 59,061 | 3,572 | 0 | 3840 |  |
| `lineworktimetotal` | INTEGER |  | 58,937 | 2,720 | 0 | 3225 |  |
| `generatedacpowertotal` | TEXT |  | 3,001 | 2 |  |  | 2282903/2282903 valores son JSON |
| `energyreserved2` | REAL |  | 59,473 | 1 | 0.0 | 0.0 |  |
| `energyreserved1` | TEXT |  | 4,366 | 2 |  |  | 2281538/2281538 valores son JSON |
| `powerontime` | REAL |  | 1,245,785 | 9 | 1752896895.537227 | 1781588477.259869 |  |
| `stactimeback` | REAL |  | 82,025 | 506 | 1752512456.480223 | 1783868767.472918 |  |

### `status` · 2,240,052 filas

| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |
|---|---|---|---:|---:|---|---|---|
| `read_ts` | REAL |  | 0 | 1,236,600 | 2025-07-12T13:31:35.265811+00:00 | 2026-07-13T05:13:53.451776+00:00 |  |
| `inverter` | INTEGER |  | 0 | 2 | 1 | 2 |  |
| `startupstatus` | INTEGER |  | 57,555 | 3 | 1 | 3 |  |
| `outstatus` | INTEGER |  | 58,196 | 3 | 0 | 2 |  |
| `chgstatus` | INTEGER |  | 57,480 | 4 | 0 | 8 |  |
| `paramode` | INTEGER |  | 57,602 | 1 | 0 | 0 |  |
| `ecomode` | INTEGER |  | 57,588 | 1 | 0 | 0 |  |
| `battselfcheck` | INTEGER |  | 57,309 | 1 | 0 | 0 |  |
| `drycontact1` | INTEGER |  | 57,289 | 2 | 0 | 1 |  |
| `drycontact2` | INTEGER |  | 57,420 | 1 | 0 | 0 |  |
| `passwordstatus` | INTEGER |  | 57,281 | 2 | 0 | 4 |  |
| `sysstateflag` | TEXT |  | 3,083 | 111 |  |  | 2236969/2236969 valores son JSON |
| `sysalarmflag` | TEXT |  | 3,064 | 11 |  |  | 2236988/2236988 valores son JSON |
| `deroperationstate` | INTEGER |  | 57,931 | 1 | 0 | 0 |  |
| `derconnectstate` | INTEGER |  | 58,112 | 1 | 0 | 0 |  |
| `deralarmstatus` | INTEGER |  | 57,736 | 1 | 0 | 0 |  |
| `derinverterstate` | INTEGER |  | 2,239,162 | 1 | 0 | 0 |  |
| `derbattstate` | INTEGER |  | 57,469 | 1 | 0 | 0 |  |
| `remotectrlstatus` | INTEGER |  | 57,506 | 1 | 0 | 0 |  |
| `statusreserve` | TEXT |  | 3,430 | 2 |  |  | 2236622/2236622 valores son JSON |

### `totals` · 2,279,918 filas

| Columna | Tipo | PK | Nulos | Distintos | Mín | Máx | Nota |
|---|---|---|---:|---:|---|---|---|
| `read_ts` | REAL |  | 0 | 1,266,438 | 2025-07-12T13:31:35.265811+00:00 | 2026-07-13T05:13:53.451776+00:00 |  |
| `inverter` | INTEGER |  | 0 | 2 | 1 | 2 |  |
| `alarmdetail` | TEXT |  | 1,481,536 | 1 |  |  | 798382/798382 valores son JSON |
| `bmsreqchgvolt` | REAL |  | 2,273,864 | 1 | 57.6 | 57.6 |  |
| `bmsreqeodvolt` | REAL |  | 57,336 | 2 | 0.0 | 44.8 |  |
| `bmsreqchgcurr` | REAL |  | 57,953 | 2 | 90.0 | 180.0 |  |
| `bmsreqdischgcurr` | REAL |  | 57,824 | 3 | 0.0 | 180.0 |  |
| `bmsreserve` | TEXT |  | 2,474 | 2 |  |  | 2277444/2277444 valores son JSON |
| `battsumpower` | REAL |  | 58,418 | 1 | 0.0 | 0.0 |  |
| `sys_battreserve` | TEXT |  | 3,576 | 2 |  |  | 2276342/2276342 valores son JSON |
| `extpvsumoutw_a` | REAL |  | 58,119 | 1 | 0.0 | 0.0 |  |
| `sys_pvreserve` | TEXT |  | 4,489 | 2 |  |  | 2275429/2275429 valores son JSON |
| `backupsumoutw_a` | REAL |  | 57,870 | 73 | 0.0 | 0.97 |  |
| `backupsumoutva_a` | REAL |  | 57,404 | 70 | 0.0 | 1.01 |  |
| `normalsumloadw_a` | REAL |  | 57,664 | 1 | 0.0 | 0.0 |  |
| `normalsumloadva_a` | REAL |  | 57,718 | 1 | 0.0 | 0.0 |  |
| `generatedsumpowerp_a` | REAL |  | 57,765 | 94 | -1.17 | 0.0 |  |
| `generatedsumpowers_a` | REAL |  | 57,476 | 1 | 0.0 | 0.0 |  |
| `sys_outreserve` | TEXT |  | 2,858 | 2 |  |  | 2277060/2277060 valores son JSON |
| `linesumpowerw_a` | REAL |  | 58,367 | 7 | 0.0 | 0.1 |  |
| `sys_linereserve` | TEXT |  | 4,182 | 2 |  |  | 2275736/2275736 valores son JSON |
