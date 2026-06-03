# Interpretation Scale Readiness Audit

Generated: 2026-06-03

Scope: read-only audit of the current loaded evidence rows and current frontend overview/card-summary code. No interpretation rollout, curated roll-number expansion, frontend behavior change, or merge is included.

Data source: backend read layer against the current local DB using the same evidence joins as the position evidence endpoint. Local HTTP API was not running, so the audit did not start backend/frontend servers.

## Verdict

The system is not ready for broad scaling. It is ready for additional narrow, reviewed slices where the slice has enough interpreted Yes/No rows and known measure-group labels. The blocker is not the overview object shape; it is uneven data/source readiness and generic copy quality outside the two proven slices.

## 1. Coverage by Official/Domain

- Loaded official/domain slices with evidence rows: 3,457
- Total evidence rows audited: 26,763
- Slices with 10+ evidence rows: 868
- Slices with 20+ evidence rows: 430
- Slices with high ambiguous/insufficient share (>=60% and 10+ rows): 437
- Slices with enough interpreted rows for a useful overview (>=3 counted interpreted Yes/No rows): 1,457

### Domain Aggregate

| Domain | Total rows | Interpreted | Counted Yes/No | Ambiguous | Insufficient | Not voting | Distinct facets |
|---|---:|---:|---:|---:|---:|---:|---:|
| Economy & Taxes | 4,297 | 3,427 | 3,359 | 870 | 0 | 89 | 11 |
| Education & Workforce | 2,594 | 1,298 | 1,257 | 0 | 1,296 | 76 | 5 |
| Environment & Energy | 1,299 | 433 | 397 | 0 | 866 | 48 | 2 |
| Health & Social Services | 1,732 | 433 | 416 | 0 | 1,299 | 60 | 3 |
| Immigration & Border Policy | 432 | 432 | 418 | 0 | 0 | 14 | 1 |
| Infrastructure, Tech & Transportation | 700 | 100 | 97 | 600 | 0 | 22 | 2 |
| Justice & Public Safety | 5,721 | 2,696 | 2,625 | 432 | 2,593 | 153 | 7 |
| National Security & Foreign Policy | 9,988 | 1,265 | 1,236 | 1,294 | 7,429 | 166 | 6 |

### Best-Covered Slice Examples

- Aaron Bean (R, FL-04, house) / ECONOMY_TAXES: 9 rows, 7 counted interpreted Yes/No rows, 2 limited rows, 8 facets.
- Adam Smith (D, WA-09, house) / ECONOMY_TAXES: 9 rows, 7 counted interpreted Yes/No rows, 2 limited rows, 8 facets.
- Addison P. McDowell (R, NC-06, house) / ECONOMY_TAXES: 9 rows, 7 counted interpreted Yes/No rows, 2 limited rows, 8 facets.
- Adrian Smith (R, NE-03, house) / ECONOMY_TAXES: 9 rows, 7 counted interpreted Yes/No rows, 2 limited rows, 8 facets.
- Adriano Espaillat (D, NY-13, house) / ECONOMY_TAXES: 9 rows, 7 counted interpreted Yes/No rows, 2 limited rows, 8 facets.
- Al Green (D, TX-09, house) / ECONOMY_TAXES: 9 rows, 7 counted interpreted Yes/No rows, 2 limited rows, 8 facets.
- Alma S. Adams (D, NC-12, house) / ECONOMY_TAXES: 9 rows, 7 counted interpreted Yes/No rows, 2 limited rows, 8 facets.
- Ami Bera (D, CA-06, house) / ECONOMY_TAXES: 9 rows, 7 counted interpreted Yes/No rows, 2 limited rows, 8 facets.
- Andrea Salinas (D, OR-06, house) / ECONOMY_TAXES: 9 rows, 7 counted interpreted Yes/No rows, 2 limited rows, 8 facets.
- Andrew Ogles (R, TN-05, house) / ECONOMY_TAXES: 9 rows, 7 counted interpreted Yes/No rows, 2 limited rows, 8 facets.

### Weak/High-Limited Slice Examples

- Aumua Amata Coleman Radewagen (R, AS-00, house) / NATIONAL_SECURITY_FOREIGN: 17 rows, 0 interpreted, 0 counted, 17 limited (100.0%), facets: Defense authorization amendment.
- Eleanor Holmes Norton (D, DC-00, house) / NATIONAL_SECURITY_FOREIGN: 17 rows, 0 interpreted, 0 counted, 17 limited (100.0%), facets: Defense authorization amendment.
- James C. Moylan (R, GU-00, house) / NATIONAL_SECURITY_FOREIGN: 17 rows, 0 interpreted, 0 counted, 17 limited (100.0%), facets: Defense authorization amendment.
- Kimberlyn King-Hinds (R, MP-00, house) / NATIONAL_SECURITY_FOREIGN: 17 rows, 0 interpreted, 0 counted, 17 limited (100.0%), facets: Defense authorization amendment.
- Pablo José Hernández (D, PR-00, house) / NATIONAL_SECURITY_FOREIGN: 17 rows, 0 interpreted, 0 counted, 17 limited (100.0%), facets: Defense authorization amendment.
- Stacey E. Plaskett (D, VI-00, house) / NATIONAL_SECURITY_FOREIGN: 17 rows, 0 interpreted, 0 counted, 17 limited (100.0%), facets: Defense authorization amendment.
- Sherrill (D, NJ-00, house) / NATIONAL_SECURITY_FOREIGN: 20 rows, 1 interpreted, 0 counted, 19 limited (95.0%), facets: Defense authorization, Defense authorization amendment, House floor procedure.
- Aaron Bean (R, FL-04, house) / NATIONAL_SECURITY_FOREIGN: 22 rows, 2 interpreted, 2 counted, 20 limited (90.9%), facets: Defense authorization, Defense authorization amendment, House floor procedure, Motion to commit, Veterans cemetery administration.
- Abraham J. Hamadeh (R, AZ-08, house) / NATIONAL_SECURITY_FOREIGN: 22 rows, 2 interpreted, 2 counted, 20 limited (90.9%), facets: Defense authorization, Defense authorization amendment, House floor procedure, Motion to commit, Veterans cemetery administration.
- Adam Gray (D, CA-13, house) / NATIONAL_SECURITY_FOREIGN: 22 rows, 2 interpreted, 2 counted, 20 limited (90.9%), facets: Defense authorization, Defense authorization amendment, House floor procedure, Motion to commit, Veterans cemetery administration.

### Full Coverage Appendix

The following CSV-style appendix contains one row for every loaded official/domain with evidence rows.

```csv
official,party,chamber,state,district,domain,total_rows,interpreted_rows,counted_reviewed_yes_no_rows,ambiguous_rows,insufficient_evidence_rows,not_voting_rows,distinct_issue_facet_values
Aaron Bean,R,house,FL,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Aaron Bean,R,house,FL,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Aaron Bean,R,house,FL,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Aaron Bean,R,house,FL,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Aaron Bean,R,house,FL,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Aaron Bean,R,house,FL,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Aaron Bean,R,house,FL,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Abraham J. Hamadeh,R,house,AZ,08,ECONOMY_TAXES,9,7,6,2,0,1,8
Abraham J. Hamadeh,R,house,AZ,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Abraham J. Hamadeh,R,house,AZ,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Abraham J. Hamadeh,R,house,AZ,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Abraham J. Hamadeh,R,house,AZ,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Abraham J. Hamadeh,R,house,AZ,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Abraham J. Hamadeh,R,house,AZ,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Adam B. Schiff,D,senate,CA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Adam B. Schiff,D,senate,CA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Adam B. Schiff,D,senate,CA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Adam B. Schiff,D,senate,CA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Adam Gray,D,house,CA,13,ECONOMY_TAXES,9,7,6,2,0,1,8
Adam Gray,D,house,CA,13,EDUCATION_WORKFORCE,6,3,3,0,3,1,5
Adam Gray,D,house,CA,13,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Adam Gray,D,house,CA,13,HEALTH_SOCIAL,4,1,1,0,3,0,3
Adam Gray,D,house,CA,13,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Adam Gray,D,house,CA,13,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,3,7
Adam Gray,D,house,CA,13,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Adam Smith,D,house,WA,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Adam Smith,D,house,WA,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Adam Smith,D,house,WA,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Adam Smith,D,house,WA,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Adam Smith,D,house,WA,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Adam Smith,D,house,WA,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Adam Smith,D,house,WA,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Addison P. McDowell,R,house,NC,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Addison P. McDowell,R,house,NC,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Addison P. McDowell,R,house,NC,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Addison P. McDowell,R,house,NC,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Addison P. McDowell,R,house,NC,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Addison P. McDowell,R,house,NC,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Addison P. McDowell,R,house,NC,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Adelita S. Grijalva,D,house,AZ,07,ECONOMY_TAXES,2,2,2,0,0,0,2
Adelita S. Grijalva,D,house,AZ,07,EDUCATION_WORKFORCE,5,3,3,0,2,0,4
Adelita S. Grijalva,D,house,AZ,07,ENVIRONMENT_ENERGY,1,1,1,0,0,0,1
Adelita S. Grijalva,D,house,AZ,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Adelita S. Grijalva,D,house,AZ,07,JUSTICE_PUBLIC_SAFETY,3,1,1,0,2,0,2
Adelita S. Grijalva,D,house,AZ,07,NATIONAL_SECURITY_FOREIGN,2,1,1,1,0,0,2
Adrian Smith,R,house,NE,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Adrian Smith,R,house,NE,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Adrian Smith,R,house,NE,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Adrian Smith,R,house,NE,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Adrian Smith,R,house,NE,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Adrian Smith,R,house,NE,03,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,1,7
Adrian Smith,R,house,NE,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Adriano Espaillat,D,house,NY,13,ECONOMY_TAXES,9,7,7,2,0,0,8
Adriano Espaillat,D,house,NY,13,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Adriano Espaillat,D,house,NY,13,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Adriano Espaillat,D,house,NY,13,HEALTH_SOCIAL,4,1,1,0,3,1,3
Adriano Espaillat,D,house,NY,13,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Adriano Espaillat,D,house,NY,13,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Adriano Espaillat,D,house,NY,13,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Al Green,D,house,TX,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Al Green,D,house,TX,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Al Green,D,house,TX,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Al Green,D,house,TX,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Al Green,D,house,TX,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Al Green,D,house,TX,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Al Green,D,house,TX,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Alex Padilla,D,senate,CA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Alex Padilla,D,senate,CA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Alex Padilla,D,senate,CA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Alex Padilla,D,senate,CA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,2,0,0,2,1
Alexandria Ocasio-Cortez,D,house,NY,14,ECONOMY_TAXES,9,7,6,2,0,2,8
Alexandria Ocasio-Cortez,D,house,NY,14,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Alexandria Ocasio-Cortez,D,house,NY,14,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Alexandria Ocasio-Cortez,D,house,NY,14,HEALTH_SOCIAL,4,1,1,0,3,0,3
Alexandria Ocasio-Cortez,D,house,NY,14,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Alexandria Ocasio-Cortez,D,house,NY,14,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Alexandria Ocasio-Cortez,D,house,NY,14,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Alma S. Adams,D,house,NC,12,ECONOMY_TAXES,9,7,7,2,0,0,8
Alma S. Adams,D,house,NC,12,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Alma S. Adams,D,house,NC,12,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Alma S. Adams,D,house,NC,12,HEALTH_SOCIAL,4,1,1,0,3,0,3
Alma S. Adams,D,house,NC,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Alma S. Adams,D,house,NC,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Alma S. Adams,D,house,NC,12,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ami Bera,D,house,CA,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Ami Bera,D,house,CA,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ami Bera,D,house,CA,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ami Bera,D,house,CA,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ami Bera,D,house,CA,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ami Bera,D,house,CA,06,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Ami Bera,D,house,CA,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Amy Klobuchar,D,senate,MN,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Amy Klobuchar,D,senate,MN,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Amy Klobuchar,D,senate,MN,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Amy Klobuchar,D,senate,MN,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Andrea Salinas,D,house,OR,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Andrea Salinas,D,house,OR,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Andrea Salinas,D,house,OR,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Andrea Salinas,D,house,OR,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Andrea Salinas,D,house,OR,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Andrea Salinas,D,house,OR,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Andrea Salinas,D,house,OR,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Andrew Ogles,R,house,TN,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Andrew Ogles,R,house,TN,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Andrew Ogles,R,house,TN,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Andrew Ogles,R,house,TN,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Andrew Ogles,R,house,TN,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Andrew Ogles,R,house,TN,05,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Andrew Ogles,R,house,TN,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Andrew R. Garbarino,R,house,NY,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Andrew R. Garbarino,R,house,NY,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Andrew R. Garbarino,R,house,NY,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Andrew R. Garbarino,R,house,NY,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Andrew R. Garbarino,R,house,NY,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Andrew R. Garbarino,R,house,NY,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Andrew R. Garbarino,R,house,NY,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Andrew S. Clyde,R,house,GA,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Andrew S. Clyde,R,house,GA,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Andrew S. Clyde,R,house,GA,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Andrew S. Clyde,R,house,GA,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Andrew S. Clyde,R,house,GA,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Andrew S. Clyde,R,house,GA,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Andrew S. Clyde,R,house,GA,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
André Carson,D,house,IN,07,ECONOMY_TAXES,9,7,7,2,0,0,8
André Carson,D,house,IN,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
André Carson,D,house,IN,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
André Carson,D,house,IN,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
André Carson,D,house,IN,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
André Carson,D,house,IN,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
André Carson,D,house,IN,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Andy Barr,R,house,KY,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Andy Barr,R,house,KY,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Andy Barr,R,house,KY,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Andy Barr,R,house,KY,06,HEALTH_SOCIAL,4,1,1,0,3,1,3
Andy Barr,R,house,KY,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Andy Barr,R,house,KY,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Andy Barr,R,house,KY,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Andy Biggs,R,house,AZ,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Andy Biggs,R,house,AZ,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Andy Biggs,R,house,AZ,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Andy Biggs,R,house,AZ,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Andy Biggs,R,house,AZ,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Andy Biggs,R,house,AZ,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Andy Biggs,R,house,AZ,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Andy Harris,R,house,MD,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Andy Harris,R,house,MD,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Andy Harris,R,house,MD,01,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Andy Harris,R,house,MD,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Andy Harris,R,house,MD,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Andy Harris,R,house,MD,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Andy Harris,R,house,MD,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Andy Kim,D,senate,NJ,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Andy Kim,D,senate,NJ,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Andy Kim,D,senate,NJ,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Andy Kim,D,senate,NJ,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Angela D. Alsobrooks,D,senate,MD,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Angela D. Alsobrooks,D,senate,MD,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Angela D. Alsobrooks,D,senate,MD,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Angela D. Alsobrooks,D,senate,MD,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Angie Craig,D,house,MN,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Angie Craig,D,house,MN,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Angie Craig,D,house,MN,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Angie Craig,D,house,MN,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Angie Craig,D,house,MN,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Angie Craig,D,house,MN,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Angie Craig,D,house,MN,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Angus S. King,I,senate,ME,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Angus S. King,I,senate,ME,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Angus S. King,I,senate,ME,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Angus S. King,I,senate,ME,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Ann Wagner,R,house,MO,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Ann Wagner,R,house,MO,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ann Wagner,R,house,MO,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ann Wagner,R,house,MO,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ann Wagner,R,house,MO,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ann Wagner,R,house,MO,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ann Wagner,R,house,MO,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Anna Paulina Luna,R,house,FL,13,ECONOMY_TAXES,9,7,7,2,0,0,8
Anna Paulina Luna,R,house,FL,13,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Anna Paulina Luna,R,house,FL,13,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Anna Paulina Luna,R,house,FL,13,HEALTH_SOCIAL,4,1,1,0,3,0,3
Anna Paulina Luna,R,house,FL,13,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Anna Paulina Luna,R,house,FL,13,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Anna Paulina Luna,R,house,FL,13,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
April McClain Delaney,D,house,MD,06,ECONOMY_TAXES,9,7,6,2,0,1,8
April McClain Delaney,D,house,MD,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
April McClain Delaney,D,house,MD,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
April McClain Delaney,D,house,MD,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
April McClain Delaney,D,house,MD,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
April McClain Delaney,D,house,MD,06,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,2,7
April McClain Delaney,D,house,MD,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ashley Hinson,R,house,IA,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Ashley Hinson,R,house,IA,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ashley Hinson,R,house,IA,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ashley Hinson,R,house,IA,02,HEALTH_SOCIAL,4,1,1,0,3,2,3
Ashley Hinson,R,house,IA,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ashley Hinson,R,house,IA,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ashley Hinson,R,house,IA,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ashley Moody,R,senate,FL,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Ashley Moody,R,senate,FL,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Ashley Moody,R,senate,FL,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Ashley Moody,R,senate,FL,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
August Pfluger,R,house,TX,11,ECONOMY_TAXES,9,7,7,2,0,0,8
August Pfluger,R,house,TX,11,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
August Pfluger,R,house,TX,11,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
August Pfluger,R,house,TX,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
August Pfluger,R,house,TX,11,IMMIGRATION_BORDER,1,1,1,0,0,0,1
August Pfluger,R,house,TX,11,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
August Pfluger,R,house,TX,11,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Aumua Amata Coleman Radewagen,R,house,AS,00,ECONOMY_TAXES,1,0,0,1,0,1,1
Aumua Amata Coleman Radewagen,R,house,AS,00,NATIONAL_SECURITY_FOREIGN,17,0,0,0,17,5,1
Austin Scott,R,house,GA,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Austin Scott,R,house,GA,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Austin Scott,R,house,GA,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Austin Scott,R,house,GA,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Austin Scott,R,house,GA,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Austin Scott,R,house,GA,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Austin Scott,R,house,GA,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ayanna Pressley,D,house,MA,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Ayanna Pressley,D,house,MA,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ayanna Pressley,D,house,MA,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ayanna Pressley,D,house,MA,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ayanna Pressley,D,house,MA,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ayanna Pressley,D,house,MA,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ayanna Pressley,D,house,MA,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Barry Loudermilk,R,house,GA,11,ECONOMY_TAXES,9,7,7,2,0,0,8
Barry Loudermilk,R,house,GA,11,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Barry Loudermilk,R,house,GA,11,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Barry Loudermilk,R,house,GA,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
Barry Loudermilk,R,house,GA,11,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Barry Loudermilk,R,house,GA,11,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Barry Loudermilk,R,house,GA,11,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Barry Moore,R,house,AL,01,ECONOMY_TAXES,9,7,6,2,0,1,8
Barry Moore,R,house,AL,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Barry Moore,R,house,AL,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Barry Moore,R,house,AL,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Barry Moore,R,house,AL,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Barry Moore,R,house,AL,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Barry Moore,R,house,AL,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Becca Balint,D,house,VT,00,ECONOMY_TAXES,9,7,7,2,0,0,8
Becca Balint,D,house,VT,00,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Becca Balint,D,house,VT,00,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Becca Balint,D,house,VT,00,HEALTH_SOCIAL,4,1,1,0,3,0,3
Becca Balint,D,house,VT,00,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Becca Balint,D,house,VT,00,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Becca Balint,D,house,VT,00,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ben Cline,R,house,VA,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Ben Cline,R,house,VA,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ben Cline,R,house,VA,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ben Cline,R,house,VA,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ben Cline,R,house,VA,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ben Cline,R,house,VA,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ben Cline,R,house,VA,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ben Ray Lujan,D,senate,NM,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Ben Ray Lujan,D,senate,NM,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Ben Ray Lujan,D,senate,NM,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Ben Ray Lujan,D,senate,NM,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Bennie G. Thompson,D,house,MS,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Bennie G. Thompson,D,house,MS,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Bennie G. Thompson,D,house,MS,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Bennie G. Thompson,D,house,MS,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Bennie G. Thompson,D,house,MS,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Bennie G. Thompson,D,house,MS,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Bennie G. Thompson,D,house,MS,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Bernard Sanders,I,senate,VT,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Bernard Sanders,I,senate,VT,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Bernard Sanders,I,senate,VT,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Bernard Sanders,I,senate,VT,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Bernie Moreno,R,senate,OH,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Bernie Moreno,R,senate,OH,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Bernie Moreno,R,senate,OH,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Bernie Moreno,R,senate,OH,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Beth Van Duyne,R,house,TX,24,ECONOMY_TAXES,9,7,7,2,0,0,8
Beth Van Duyne,R,house,TX,24,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Beth Van Duyne,R,house,TX,24,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Beth Van Duyne,R,house,TX,24,HEALTH_SOCIAL,4,1,1,0,3,0,3
Beth Van Duyne,R,house,TX,24,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Beth Van Duyne,R,house,TX,24,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Beth Van Duyne,R,house,TX,24,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Betty McCollum,D,house,MN,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Betty McCollum,D,house,MN,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Betty McCollum,D,house,MN,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Betty McCollum,D,house,MN,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Betty McCollum,D,house,MN,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Betty McCollum,D,house,MN,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Betty McCollum,D,house,MN,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Bill Cassidy,R,senate,LA,Statewide,ECONOMY_TAXES,4,4,3,0,0,1,3
Bill Cassidy,R,senate,LA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Bill Cassidy,R,senate,LA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Bill Cassidy,R,senate,LA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Bill Foster,D,house,IL,11,ECONOMY_TAXES,9,7,7,2,0,0,8
Bill Foster,D,house,IL,11,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Bill Foster,D,house,IL,11,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Bill Foster,D,house,IL,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
Bill Foster,D,house,IL,11,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Bill Foster,D,house,IL,11,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Bill Foster,D,house,IL,11,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Bill Hagerty,R,senate,TN,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Bill Hagerty,R,senate,TN,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Bill Hagerty,R,senate,TN,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Bill Hagerty,R,senate,TN,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Bill Huizenga,R,house,MI,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Bill Huizenga,R,house,MI,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Bill Huizenga,R,house,MI,04,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Bill Huizenga,R,house,MI,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Bill Huizenga,R,house,MI,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Bill Huizenga,R,house,MI,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Bill Huizenga,R,house,MI,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Blake D. Moore,R,house,UT,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Blake D. Moore,R,house,UT,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Blake D. Moore,R,house,UT,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Blake D. Moore,R,house,UT,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Blake D. Moore,R,house,UT,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Blake D. Moore,R,house,UT,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Blake D. Moore,R,house,UT,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Bonnie Watson Coleman,D,house,NJ,12,ECONOMY_TAXES,9,7,6,2,0,1,8
Bonnie Watson Coleman,D,house,NJ,12,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Bonnie Watson Coleman,D,house,NJ,12,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Bonnie Watson Coleman,D,house,NJ,12,HEALTH_SOCIAL,4,1,1,0,3,0,3
Bonnie Watson Coleman,D,house,NJ,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Bonnie Watson Coleman,D,house,NJ,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Bonnie Watson Coleman,D,house,NJ,12,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Brad Finstad,R,house,MN,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Brad Finstad,R,house,MN,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Brad Finstad,R,house,MN,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Brad Finstad,R,house,MN,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Brad Finstad,R,house,MN,01,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Brad Finstad,R,house,MN,01,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,1,7
Brad Finstad,R,house,MN,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Brad Knott,R,house,NC,13,ECONOMY_TAXES,9,7,7,2,0,0,8
Brad Knott,R,house,NC,13,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Brad Knott,R,house,NC,13,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Brad Knott,R,house,NC,13,HEALTH_SOCIAL,4,1,1,0,3,0,3
Brad Knott,R,house,NC,13,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Brad Knott,R,house,NC,13,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Brad Knott,R,house,NC,13,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Brad Sherman,D,house,CA,32,ECONOMY_TAXES,9,7,7,2,0,0,8
Brad Sherman,D,house,CA,32,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Brad Sherman,D,house,CA,32,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Brad Sherman,D,house,CA,32,HEALTH_SOCIAL,4,1,1,0,3,0,3
Brad Sherman,D,house,CA,32,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Brad Sherman,D,house,CA,32,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Brad Sherman,D,house,CA,32,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Bradley Scott Schneider,D,house,IL,10,ECONOMY_TAXES,9,7,7,2,0,0,8
Bradley Scott Schneider,D,house,IL,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Bradley Scott Schneider,D,house,IL,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Bradley Scott Schneider,D,house,IL,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
Bradley Scott Schneider,D,house,IL,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Bradley Scott Schneider,D,house,IL,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Bradley Scott Schneider,D,house,IL,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Brandon Gill,R,house,TX,26,ECONOMY_TAXES,9,7,7,2,0,0,8
Brandon Gill,R,house,TX,26,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Brandon Gill,R,house,TX,26,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Brandon Gill,R,house,TX,26,HEALTH_SOCIAL,4,1,1,0,3,0,3
Brandon Gill,R,house,TX,26,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Brandon Gill,R,house,TX,26,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,2,7
Brandon Gill,R,house,TX,26,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Brendan F. Boyle,D,house,PA,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Brendan F. Boyle,D,house,PA,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Brendan F. Boyle,D,house,PA,02,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Brendan F. Boyle,D,house,PA,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Brendan F. Boyle,D,house,PA,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Brendan F. Boyle,D,house,PA,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,2,7
Brendan F. Boyle,D,house,PA,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Brett Guthrie,R,house,KY,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Brett Guthrie,R,house,KY,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Brett Guthrie,R,house,KY,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Brett Guthrie,R,house,KY,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Brett Guthrie,R,house,KY,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Brett Guthrie,R,house,KY,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Brett Guthrie,R,house,KY,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Brian Babin,R,house,TX,36,ECONOMY_TAXES,9,7,6,2,0,1,8
Brian Babin,R,house,TX,36,EDUCATION_WORKFORCE,6,3,1,0,3,4,5
Brian Babin,R,house,TX,36,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Brian Babin,R,house,TX,36,HEALTH_SOCIAL,4,1,1,0,3,0,3
Brian Babin,R,house,TX,36,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Brian Babin,R,house,TX,36,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Brian Babin,R,house,TX,36,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Brian J. Mast,R,house,FL,21,ECONOMY_TAXES,9,7,7,2,0,0,8
Brian J. Mast,R,house,FL,21,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Brian J. Mast,R,house,FL,21,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Brian J. Mast,R,house,FL,21,HEALTH_SOCIAL,4,1,1,0,3,0,3
Brian J. Mast,R,house,FL,21,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Brian J. Mast,R,house,FL,21,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Brian J. Mast,R,house,FL,21,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Brian Jack,R,house,GA,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Brian Jack,R,house,GA,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Brian Jack,R,house,GA,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Brian Jack,R,house,GA,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Brian Jack,R,house,GA,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Brian Jack,R,house,GA,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Brian Jack,R,house,GA,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Brian K. Fitzpatrick,R,house,PA,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Brian K. Fitzpatrick,R,house,PA,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Brian K. Fitzpatrick,R,house,PA,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Brian K. Fitzpatrick,R,house,PA,01,HEALTH_SOCIAL,4,1,1,0,3,1,3
Brian K. Fitzpatrick,R,house,PA,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Brian K. Fitzpatrick,R,house,PA,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Brian K. Fitzpatrick,R,house,PA,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Brian Schatz,D,senate,HI,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Brian Schatz,D,senate,HI,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Brian Schatz,D,senate,HI,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Brian Schatz,D,senate,HI,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Brittany Pettersen,D,house,CO,07,ECONOMY_TAXES,9,7,6,2,0,1,8
Brittany Pettersen,D,house,CO,07,EDUCATION_WORKFORCE,6,3,1,0,3,2,5
Brittany Pettersen,D,house,CO,07,ENVIRONMENT_ENERGY,3,1,1,0,2,2,2
Brittany Pettersen,D,house,CO,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Brittany Pettersen,D,house,CO,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Brittany Pettersen,D,house,CO,07,JUSTICE_PUBLIC_SAFETY,13,6,3,1,6,4,7
Brittany Pettersen,D,house,CO,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Bruce Westerman,R,house,AR,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Bruce Westerman,R,house,AR,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Bruce Westerman,R,house,AR,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Bruce Westerman,R,house,AR,04,HEALTH_SOCIAL,4,1,1,0,3,1,3
Bruce Westerman,R,house,AR,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Bruce Westerman,R,house,AR,04,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,1,7
Bruce Westerman,R,house,AR,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Bryan Steil,R,house,WI,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Bryan Steil,R,house,WI,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Bryan Steil,R,house,WI,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Bryan Steil,R,house,WI,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Bryan Steil,R,house,WI,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Bryan Steil,R,house,WI,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Bryan Steil,R,house,WI,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Burgess Owens,R,house,UT,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Burgess Owens,R,house,UT,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Burgess Owens,R,house,UT,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Burgess Owens,R,house,UT,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Burgess Owens,R,house,UT,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Burgess Owens,R,house,UT,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Burgess Owens,R,house,UT,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Byron Donalds,R,house,FL,19,ECONOMY_TAXES,9,7,7,2,0,0,8
Byron Donalds,R,house,FL,19,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Byron Donalds,R,house,FL,19,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Byron Donalds,R,house,FL,19,HEALTH_SOCIAL,4,1,1,0,3,0,3
Byron Donalds,R,house,FL,19,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Byron Donalds,R,house,FL,19,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Byron Donalds,R,house,FL,19,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Carlos A. Gimenez,R,house,FL,28,ECONOMY_TAXES,9,7,6,2,0,2,8
Carlos A. Gimenez,R,house,FL,28,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Carlos A. Gimenez,R,house,FL,28,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Carlos A. Gimenez,R,house,FL,28,HEALTH_SOCIAL,4,1,1,0,3,0,3
Carlos A. Gimenez,R,house,FL,28,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Carlos A. Gimenez,R,house,FL,28,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Carlos A. Gimenez,R,house,FL,28,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,2,5
Carol D. Miller,R,house,WV,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Carol D. Miller,R,house,WV,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Carol D. Miller,R,house,WV,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Carol D. Miller,R,house,WV,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Carol D. Miller,R,house,WV,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Carol D. Miller,R,house,WV,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Carol D. Miller,R,house,WV,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Catherine Cortez Masto,D,senate,NV,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Catherine Cortez Masto,D,senate,NV,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Catherine Cortez Masto,D,senate,NV,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Catherine Cortez Masto,D,senate,NV,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Celeste Maloy,R,house,UT,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Celeste Maloy,R,house,UT,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Celeste Maloy,R,house,UT,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Celeste Maloy,R,house,UT,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Celeste Maloy,R,house,UT,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Celeste Maloy,R,house,UT,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Celeste Maloy,R,house,UT,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Charles E. Schumer,D,senate,NY,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Charles E. Schumer,D,senate,NY,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Charles E. Schumer,D,senate,NY,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Charles E. Schumer,D,senate,NY,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Charles J. "Chuck" Fleischmann,R,house,TN,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Charles J. "Chuck" Fleischmann,R,house,TN,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Charles J. "Chuck" Fleischmann,R,house,TN,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Charles J. "Chuck" Fleischmann,R,house,TN,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Charles J. "Chuck" Fleischmann,R,house,TN,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Charles J. "Chuck" Fleischmann,R,house,TN,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Charles J. "Chuck" Fleischmann,R,house,TN,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Chellie Pingree,D,house,ME,01,ECONOMY_TAXES,9,7,6,2,0,1,8
Chellie Pingree,D,house,ME,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Chellie Pingree,D,house,ME,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Chellie Pingree,D,house,ME,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Chellie Pingree,D,house,ME,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Chellie Pingree,D,house,ME,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Chellie Pingree,D,house,ME,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Chip Roy,R,house,TX,21,ECONOMY_TAXES,9,7,7,2,0,0,8
Chip Roy,R,house,TX,21,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Chip Roy,R,house,TX,21,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Chip Roy,R,house,TX,21,HEALTH_SOCIAL,4,1,1,0,3,0,3
Chip Roy,R,house,TX,21,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Chip Roy,R,house,TX,21,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,3,7
Chip Roy,R,house,TX,21,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Chris Pappas,D,house,NH,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Chris Pappas,D,house,NH,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Chris Pappas,D,house,NH,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Chris Pappas,D,house,NH,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Chris Pappas,D,house,NH,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Chris Pappas,D,house,NH,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Chris Pappas,D,house,NH,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Chris Van Hollen,D,senate,MD,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Chris Van Hollen,D,senate,MD,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Chris Van Hollen,D,senate,MD,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Chris Van Hollen,D,senate,MD,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Chrissy Houlahan,D,house,PA,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Chrissy Houlahan,D,house,PA,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Chrissy Houlahan,D,house,PA,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Chrissy Houlahan,D,house,PA,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Chrissy Houlahan,D,house,PA,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Chrissy Houlahan,D,house,PA,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Chrissy Houlahan,D,house,PA,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Christopher A. Coons,D,senate,DE,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Christopher A. Coons,D,senate,DE,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Christopher A. Coons,D,senate,DE,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Christopher A. Coons,D,senate,DE,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,3,0,0,1,1
Christopher H. Smith,R,house,NJ,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Christopher H. Smith,R,house,NJ,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Christopher H. Smith,R,house,NJ,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Christopher H. Smith,R,house,NJ,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Christopher H. Smith,R,house,NJ,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Christopher H. Smith,R,house,NJ,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Christopher H. Smith,R,house,NJ,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Christopher Murphy,D,senate,CT,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Christopher Murphy,D,senate,CT,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Christopher Murphy,D,senate,CT,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Christopher Murphy,D,senate,CT,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Christopher R. Deluzio,D,house,PA,17,ECONOMY_TAXES,9,7,7,2,0,0,8
Christopher R. Deluzio,D,house,PA,17,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Christopher R. Deluzio,D,house,PA,17,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Christopher R. Deluzio,D,house,PA,17,HEALTH_SOCIAL,4,1,1,0,3,0,3
Christopher R. Deluzio,D,house,PA,17,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Christopher R. Deluzio,D,house,PA,17,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Christopher R. Deluzio,D,house,PA,17,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Chuck Edwards,R,house,NC,11,ECONOMY_TAXES,9,7,7,2,0,0,8
Chuck Edwards,R,house,NC,11,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Chuck Edwards,R,house,NC,11,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Chuck Edwards,R,house,NC,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
Chuck Edwards,R,house,NC,11,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Chuck Edwards,R,house,NC,11,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Chuck Edwards,R,house,NC,11,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Chuck Grassley,R,senate,IA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Chuck Grassley,R,senate,IA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Chuck Grassley,R,senate,IA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Chuck Grassley,R,senate,IA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Cindy Hyde-Smith,R,senate,MS,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Cindy Hyde-Smith,R,senate,MS,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Cindy Hyde-Smith,R,senate,MS,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Cindy Hyde-Smith,R,senate,MS,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Claudia Tenney,R,house,NY,24,ECONOMY_TAXES,9,7,7,2,0,0,8
Claudia Tenney,R,house,NY,24,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Claudia Tenney,R,house,NY,24,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Claudia Tenney,R,house,NY,24,HEALTH_SOCIAL,4,1,1,0,3,0,3
Claudia Tenney,R,house,NY,24,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Claudia Tenney,R,house,NY,24,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Claudia Tenney,R,house,NY,24,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Clay Higgins,R,house,LA,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Clay Higgins,R,house,LA,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Clay Higgins,R,house,LA,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Clay Higgins,R,house,LA,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Clay Higgins,R,house,LA,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Clay Higgins,R,house,LA,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Clay Higgins,R,house,LA,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Cleo Fields,D,house,LA,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Cleo Fields,D,house,LA,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Cleo Fields,D,house,LA,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Cleo Fields,D,house,LA,06,HEALTH_SOCIAL,4,1,0,0,3,1,3
Cleo Fields,D,house,LA,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Cleo Fields,D,house,LA,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Cleo Fields,D,house,LA,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Cliff Bentz,R,house,OR,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Cliff Bentz,R,house,OR,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Cliff Bentz,R,house,OR,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Cliff Bentz,R,house,OR,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Cliff Bentz,R,house,OR,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Cliff Bentz,R,house,OR,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Cliff Bentz,R,house,OR,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Connolly,D,house,VA,00,ECONOMY_TAXES,2,2,2,0,0,0,1
Connolly,D,house,VA,00,ENVIRONMENT_ENERGY,2,0,0,0,2,0,1
Connolly,D,house,VA,00,JUSTICE_PUBLIC_SAFETY,4,3,1,1,0,2,4
Cory A. Booker,D,senate,NJ,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Cory A. Booker,D,senate,NJ,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Cory A. Booker,D,senate,NJ,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Cory A. Booker,D,senate,NJ,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Cory Mills,R,house,FL,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Cory Mills,R,house,FL,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Cory Mills,R,house,FL,07,ENVIRONMENT_ENERGY,3,1,1,0,2,1,2
Cory Mills,R,house,FL,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Cory Mills,R,house,FL,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Cory Mills,R,house,FL,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Cory Mills,R,house,FL,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Craig A. Goldman,R,house,TX,12,ECONOMY_TAXES,9,7,7,2,0,0,8
Craig A. Goldman,R,house,TX,12,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Craig A. Goldman,R,house,TX,12,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Craig A. Goldman,R,house,TX,12,HEALTH_SOCIAL,4,1,1,0,3,0,3
Craig A. Goldman,R,house,TX,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Craig A. Goldman,R,house,TX,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Craig A. Goldman,R,house,TX,12,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Cynthia M. Lummis,R,senate,WY,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Cynthia M. Lummis,R,senate,WY,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Cynthia M. Lummis,R,senate,WY,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Cynthia M. Lummis,R,senate,WY,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Dale W. Strong,R,house,AL,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Dale W. Strong,R,house,AL,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Dale W. Strong,R,house,AL,05,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Dale W. Strong,R,house,AL,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Dale W. Strong,R,house,AL,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Dale W. Strong,R,house,AL,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Dale W. Strong,R,house,AL,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Dan Crenshaw,R,house,TX,02,ECONOMY_TAXES,9,7,6,2,0,1,8
Dan Crenshaw,R,house,TX,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Dan Crenshaw,R,house,TX,02,ENVIRONMENT_ENERGY,3,1,1,0,2,2,2
Dan Crenshaw,R,house,TX,02,HEALTH_SOCIAL,4,1,1,0,3,1,3
Dan Crenshaw,R,house,TX,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Dan Crenshaw,R,house,TX,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Dan Crenshaw,R,house,TX,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Dan Newhouse,R,house,WA,04,ECONOMY_TAXES,9,7,7,2,0,1,8
Dan Newhouse,R,house,WA,04,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Dan Newhouse,R,house,WA,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Dan Newhouse,R,house,WA,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Dan Newhouse,R,house,WA,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Dan Newhouse,R,house,WA,04,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,2,7
Dan Newhouse,R,house,WA,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Dan Sullivan,R,senate,AK,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Dan Sullivan,R,senate,AK,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Dan Sullivan,R,senate,AK,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Dan Sullivan,R,senate,AK,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Daniel Meuser,R,house,PA,09,ECONOMY_TAXES,9,7,6,2,0,1,8
Daniel Meuser,R,house,PA,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Daniel Meuser,R,house,PA,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Daniel Meuser,R,house,PA,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Daniel Meuser,R,house,PA,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Daniel Meuser,R,house,PA,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Daniel Meuser,R,house,PA,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Daniel S. Goldman,D,house,NY,10,ECONOMY_TAXES,9,7,6,2,0,1,8
Daniel S. Goldman,D,house,NY,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Daniel S. Goldman,D,house,NY,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Daniel S. Goldman,D,house,NY,10,HEALTH_SOCIAL,4,1,1,0,3,1,3
Daniel S. Goldman,D,house,NY,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Daniel S. Goldman,D,house,NY,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Daniel S. Goldman,D,house,NY,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Daniel Webster,R,house,FL,11,ECONOMY_TAXES,9,7,7,2,0,0,8
Daniel Webster,R,house,FL,11,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Daniel Webster,R,house,FL,11,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Daniel Webster,R,house,FL,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
Daniel Webster,R,house,FL,11,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Daniel Webster,R,house,FL,11,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Daniel Webster,R,house,FL,11,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Danny K. Davis,D,house,IL,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Danny K. Davis,D,house,IL,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Danny K. Davis,D,house,IL,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Danny K. Davis,D,house,IL,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Danny K. Davis,D,house,IL,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Danny K. Davis,D,house,IL,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Danny K. Davis,D,house,IL,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Darin LaHood,R,house,IL,16,ECONOMY_TAXES,9,7,7,2,0,0,8
Darin LaHood,R,house,IL,16,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Darin LaHood,R,house,IL,16,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Darin LaHood,R,house,IL,16,HEALTH_SOCIAL,4,1,1,0,3,0,3
Darin LaHood,R,house,IL,16,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Darin LaHood,R,house,IL,16,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Darin LaHood,R,house,IL,16,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,20,5
Darrell Issa,R,house,CA,48,ECONOMY_TAXES,9,7,7,2,0,0,8
Darrell Issa,R,house,CA,48,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Darrell Issa,R,house,CA,48,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Darrell Issa,R,house,CA,48,HEALTH_SOCIAL,4,1,1,0,3,0,3
Darrell Issa,R,house,CA,48,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Darrell Issa,R,house,CA,48,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Darrell Issa,R,house,CA,48,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Darren Soto,D,house,FL,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Darren Soto,D,house,FL,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Darren Soto,D,house,FL,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Darren Soto,D,house,FL,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Darren Soto,D,house,FL,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Darren Soto,D,house,FL,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Darren Soto,D,house,FL,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Dave Min,D,house,CA,47,ECONOMY_TAXES,9,7,7,2,0,0,8
Dave Min,D,house,CA,47,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Dave Min,D,house,CA,47,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Dave Min,D,house,CA,47,HEALTH_SOCIAL,4,1,1,0,3,0,3
Dave Min,D,house,CA,47,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Dave Min,D,house,CA,47,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Dave Min,D,house,CA,47,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
David G. Valadao,R,house,CA,22,ECONOMY_TAXES,9,7,6,2,0,1,8
David G. Valadao,R,house,CA,22,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
David G. Valadao,R,house,CA,22,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
David G. Valadao,R,house,CA,22,HEALTH_SOCIAL,4,1,1,0,3,1,3
David G. Valadao,R,house,CA,22,IMMIGRATION_BORDER,1,1,1,0,0,0,1
David G. Valadao,R,house,CA,22,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
David G. Valadao,R,house,CA,22,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
David J. Taylor,R,house,OH,02,ECONOMY_TAXES,9,7,7,2,0,0,8
David J. Taylor,R,house,OH,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
David J. Taylor,R,house,OH,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
David J. Taylor,R,house,OH,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
David J. Taylor,R,house,OH,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
David J. Taylor,R,house,OH,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
David J. Taylor,R,house,OH,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
David Kustoff,R,house,TN,08,ECONOMY_TAXES,9,7,7,2,0,0,8
David Kustoff,R,house,TN,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
David Kustoff,R,house,TN,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
David Kustoff,R,house,TN,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
David Kustoff,R,house,TN,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
David Kustoff,R,house,TN,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
David Kustoff,R,house,TN,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
David McCormick,R,senate,PA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
David McCormick,R,senate,PA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
David McCormick,R,senate,PA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
David McCormick,R,senate,PA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
David P. Joyce,R,house,OH,14,ECONOMY_TAXES,9,7,7,2,0,0,8
David P. Joyce,R,house,OH,14,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
David P. Joyce,R,house,OH,14,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
David P. Joyce,R,house,OH,14,HEALTH_SOCIAL,4,1,1,0,3,0,3
David P. Joyce,R,house,OH,14,IMMIGRATION_BORDER,1,1,1,0,0,0,1
David P. Joyce,R,house,OH,14,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,1,7
David P. Joyce,R,house,OH,14,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
David Rouzer,R,house,NC,07,ECONOMY_TAXES,9,7,7,2,0,0,8
David Rouzer,R,house,NC,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
David Rouzer,R,house,NC,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
David Rouzer,R,house,NC,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
David Rouzer,R,house,NC,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
David Rouzer,R,house,NC,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
David Rouzer,R,house,NC,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
David Schweikert,R,house,AZ,01,ECONOMY_TAXES,9,7,7,2,0,0,8
David Schweikert,R,house,AZ,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
David Schweikert,R,house,AZ,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
David Schweikert,R,house,AZ,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
David Schweikert,R,house,AZ,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
David Schweikert,R,house,AZ,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
David Schweikert,R,house,AZ,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
David Scott,D,house,GA,13,ECONOMY_TAXES,9,7,7,2,0,0,8
David Scott,D,house,GA,13,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
David Scott,D,house,GA,13,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
David Scott,D,house,GA,13,HEALTH_SOCIAL,4,1,1,0,3,0,3
David Scott,D,house,GA,13,IMMIGRATION_BORDER,1,1,1,0,0,0,1
David Scott,D,house,GA,13,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
David Scott,D,house,GA,13,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Deb Fischer,R,senate,NE,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Deb Fischer,R,senate,NE,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Deb Fischer,R,senate,NE,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Deb Fischer,R,senate,NE,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Debbie Dingell,D,house,MI,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Debbie Dingell,D,house,MI,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Debbie Dingell,D,house,MI,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Debbie Dingell,D,house,MI,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Debbie Dingell,D,house,MI,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Debbie Dingell,D,house,MI,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Debbie Dingell,D,house,MI,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Debbie Wasserman Schultz,D,house,FL,25,ECONOMY_TAXES,9,7,7,2,0,0,8
Debbie Wasserman Schultz,D,house,FL,25,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Debbie Wasserman Schultz,D,house,FL,25,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Debbie Wasserman Schultz,D,house,FL,25,HEALTH_SOCIAL,4,1,1,0,3,0,3
Debbie Wasserman Schultz,D,house,FL,25,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Debbie Wasserman Schultz,D,house,FL,25,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Debbie Wasserman Schultz,D,house,FL,25,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Deborah K. Ross,D,house,NC,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Deborah K. Ross,D,house,NC,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Deborah K. Ross,D,house,NC,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Deborah K. Ross,D,house,NC,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Deborah K. Ross,D,house,NC,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Deborah K. Ross,D,house,NC,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Deborah K. Ross,D,house,NC,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Delia C. Ramirez,D,house,IL,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Delia C. Ramirez,D,house,IL,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Delia C. Ramirez,D,house,IL,03,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Delia C. Ramirez,D,house,IL,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Delia C. Ramirez,D,house,IL,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Delia C. Ramirez,D,house,IL,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Delia C. Ramirez,D,house,IL,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Derek Schmidt,R,house,KS,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Derek Schmidt,R,house,KS,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Derek Schmidt,R,house,KS,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Derek Schmidt,R,house,KS,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Derek Schmidt,R,house,KS,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Derek Schmidt,R,house,KS,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Derek Schmidt,R,house,KS,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Derek Tran,D,house,CA,45,ECONOMY_TAXES,9,7,7,2,0,0,8
Derek Tran,D,house,CA,45,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Derek Tran,D,house,CA,45,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Derek Tran,D,house,CA,45,HEALTH_SOCIAL,4,1,1,0,3,0,3
Derek Tran,D,house,CA,45,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Derek Tran,D,house,CA,45,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Derek Tran,D,house,CA,45,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Derrick Van Orden,R,house,WI,03,ECONOMY_TAXES,9,7,6,2,0,1,8
Derrick Van Orden,R,house,WI,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Derrick Van Orden,R,house,WI,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Derrick Van Orden,R,house,WI,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Derrick Van Orden,R,house,WI,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Derrick Van Orden,R,house,WI,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Derrick Van Orden,R,house,WI,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Diana DeGette,D,house,CO,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Diana DeGette,D,house,CO,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Diana DeGette,D,house,CO,01,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Diana DeGette,D,house,CO,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Diana DeGette,D,house,CO,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Diana DeGette,D,house,CO,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Diana DeGette,D,house,CO,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Diana Harshbarger,R,house,TN,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Diana Harshbarger,R,house,TN,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Diana Harshbarger,R,house,TN,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Diana Harshbarger,R,house,TN,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Diana Harshbarger,R,house,TN,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Diana Harshbarger,R,house,TN,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Diana Harshbarger,R,house,TN,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Dina Titus,D,house,NV,01,ECONOMY_TAXES,9,7,7,2,0,1,8
Dina Titus,D,house,NV,01,EDUCATION_WORKFORCE,6,3,3,0,3,1,5
Dina Titus,D,house,NV,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Dina Titus,D,house,NV,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Dina Titus,D,house,NV,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Dina Titus,D,house,NV,01,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,3,7
Dina Titus,D,house,NV,01,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,18,5
Don Bacon,R,house,NE,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Don Bacon,R,house,NE,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Don Bacon,R,house,NE,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Don Bacon,R,house,NE,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Don Bacon,R,house,NE,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Don Bacon,R,house,NE,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Don Bacon,R,house,NE,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Donald G. Davis,D,house,NC,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Donald G. Davis,D,house,NC,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Donald G. Davis,D,house,NC,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Donald G. Davis,D,house,NC,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Donald G. Davis,D,house,NC,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Donald G. Davis,D,house,NC,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Donald G. Davis,D,house,NC,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Donald Norcross,D,house,NJ,01,ECONOMY_TAXES,9,7,5,2,0,2,8
Donald Norcross,D,house,NJ,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Donald Norcross,D,house,NJ,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Donald Norcross,D,house,NJ,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Donald Norcross,D,house,NJ,01,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Donald Norcross,D,house,NJ,01,JUSTICE_PUBLIC_SAFETY,13,6,3,1,6,5,7
Donald Norcross,D,house,NJ,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Donald S. Beyer, Jr.,D,house,VA,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Donald S. Beyer, Jr.,D,house,VA,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Donald S. Beyer, Jr.,D,house,VA,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Donald S. Beyer, Jr.,D,house,VA,08,HEALTH_SOCIAL,4,1,1,0,3,1,3
Donald S. Beyer, Jr.,D,house,VA,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Donald S. Beyer, Jr.,D,house,VA,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,2,7
Donald S. Beyer, Jr.,D,house,VA,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Doris O. Matsui,D,house,CA,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Doris O. Matsui,D,house,CA,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Doris O. Matsui,D,house,CA,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Doris O. Matsui,D,house,CA,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Doris O. Matsui,D,house,CA,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Doris O. Matsui,D,house,CA,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Doris O. Matsui,D,house,CA,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Dusty Johnson,R,house,SD,00,ECONOMY_TAXES,9,7,7,2,0,0,8
Dusty Johnson,R,house,SD,00,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Dusty Johnson,R,house,SD,00,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Dusty Johnson,R,house,SD,00,HEALTH_SOCIAL,4,1,1,0,3,0,3
Dusty Johnson,R,house,SD,00,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Dusty Johnson,R,house,SD,00,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Dusty Johnson,R,house,SD,00,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Dwight Evans,D,house,PA,03,ECONOMY_TAXES,9,7,7,2,0,1,8
Dwight Evans,D,house,PA,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Dwight Evans,D,house,PA,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Dwight Evans,D,house,PA,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Dwight Evans,D,house,PA,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Dwight Evans,D,house,PA,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Dwight Evans,D,house,PA,03,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,18,5
Earl L. "Buddy" Carter,R,house,GA,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Earl L. "Buddy" Carter,R,house,GA,01,EDUCATION_WORKFORCE,6,3,3,0,3,2,5
Earl L. "Buddy" Carter,R,house,GA,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Earl L. "Buddy" Carter,R,house,GA,01,HEALTH_SOCIAL,4,1,0,0,3,1,3
Earl L. "Buddy" Carter,R,house,GA,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Earl L. "Buddy" Carter,R,house,GA,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Earl L. "Buddy" Carter,R,house,GA,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ed Case,D,house,HI,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Ed Case,D,house,HI,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ed Case,D,house,HI,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ed Case,D,house,HI,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ed Case,D,house,HI,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ed Case,D,house,HI,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ed Case,D,house,HI,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Edward J. Markey,D,senate,MA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Edward J. Markey,D,senate,MA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Edward J. Markey,D,senate,MA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Edward J. Markey,D,senate,MA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Eleanor Holmes Norton,D,house,DC,00,ECONOMY_TAXES,1,0,0,1,0,0,1
Eleanor Holmes Norton,D,house,DC,00,NATIONAL_SECURITY_FOREIGN,17,0,0,0,17,0,1
Elijah Crane,R,house,AZ,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Elijah Crane,R,house,AZ,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Elijah Crane,R,house,AZ,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Elijah Crane,R,house,AZ,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Elijah Crane,R,house,AZ,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Elijah Crane,R,house,AZ,02,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,2,7
Elijah Crane,R,house,AZ,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Elise M. Stefanik,R,house,NY,21,ECONOMY_TAXES,9,7,7,2,0,0,8
Elise M. Stefanik,R,house,NY,21,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Elise M. Stefanik,R,house,NY,21,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Elise M. Stefanik,R,house,NY,21,HEALTH_SOCIAL,4,1,0,0,3,1,3
Elise M. Stefanik,R,house,NY,21,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Elise M. Stefanik,R,house,NY,21,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Elise M. Stefanik,R,house,NY,21,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Elissa Slotkin,D,senate,MI,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Elissa Slotkin,D,senate,MI,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Elissa Slotkin,D,senate,MI,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Elissa Slotkin,D,senate,MI,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Elizabeth Warren,D,senate,MA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Elizabeth Warren,D,senate,MA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Elizabeth Warren,D,senate,MA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Elizabeth Warren,D,senate,MA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Emanuel Cleaver,D,house,MO,05,ECONOMY_TAXES,9,7,7,2,0,1,8
Emanuel Cleaver,D,house,MO,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Emanuel Cleaver,D,house,MO,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Emanuel Cleaver,D,house,MO,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Emanuel Cleaver,D,house,MO,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Emanuel Cleaver,D,house,MO,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Emanuel Cleaver,D,house,MO,05,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,1,5
Emilia Strong Sykes,D,house,OH,13,ECONOMY_TAXES,9,7,7,2,0,0,8
Emilia Strong Sykes,D,house,OH,13,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Emilia Strong Sykes,D,house,OH,13,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Emilia Strong Sykes,D,house,OH,13,HEALTH_SOCIAL,4,1,1,0,3,0,3
Emilia Strong Sykes,D,house,OH,13,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Emilia Strong Sykes,D,house,OH,13,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Emilia Strong Sykes,D,house,OH,13,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Emily Randall,D,house,WA,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Emily Randall,D,house,WA,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Emily Randall,D,house,WA,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Emily Randall,D,house,WA,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Emily Randall,D,house,WA,06,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Emily Randall,D,house,WA,06,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,1,7
Emily Randall,D,house,WA,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Eric A. "Rick" Crawford,R,house,AR,01,ECONOMY_TAXES,9,7,7,2,0,1,8
Eric A. "Rick" Crawford,R,house,AR,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Eric A. "Rick" Crawford,R,house,AR,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Eric A. "Rick" Crawford,R,house,AR,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Eric A. "Rick" Crawford,R,house,AR,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Eric A. "Rick" Crawford,R,house,AR,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Eric A. "Rick" Crawford,R,house,AR,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Eric Burlison,R,house,MO,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Eric Burlison,R,house,MO,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Eric Burlison,R,house,MO,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Eric Burlison,R,house,MO,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Eric Burlison,R,house,MO,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Eric Burlison,R,house,MO,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Eric Burlison,R,house,MO,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Eric Schmitt,R,senate,MO,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Eric Schmitt,R,senate,MO,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Eric Schmitt,R,senate,MO,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Eric Schmitt,R,senate,MO,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Eric Sorensen,D,house,IL,17,ECONOMY_TAXES,9,7,7,2,0,0,8
Eric Sorensen,D,house,IL,17,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Eric Sorensen,D,house,IL,17,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Eric Sorensen,D,house,IL,17,HEALTH_SOCIAL,4,1,1,0,3,0,3
Eric Sorensen,D,house,IL,17,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Eric Sorensen,D,house,IL,17,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Eric Sorensen,D,house,IL,17,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Eric Swalwell,D,house,CA,14,ECONOMY_TAXES,9,7,6,2,0,1,8
Eric Swalwell,D,house,CA,14,EDUCATION_WORKFORCE,6,3,0,0,3,5,5
Eric Swalwell,D,house,CA,14,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Eric Swalwell,D,house,CA,14,HEALTH_SOCIAL,4,1,0,0,3,4,3
Eric Swalwell,D,house,CA,14,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Eric Swalwell,D,house,CA,14,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,1,7
Eric Swalwell,D,house,CA,14,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,2,5
Erin Houchin,R,house,IN,09,ECONOMY_TAXES,9,7,7,2,0,1,8
Erin Houchin,R,house,IN,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Erin Houchin,R,house,IN,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Erin Houchin,R,house,IN,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Erin Houchin,R,house,IN,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Erin Houchin,R,house,IN,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Erin Houchin,R,house,IN,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Eugene Simon Vindman,D,house,VA,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Eugene Simon Vindman,D,house,VA,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Eugene Simon Vindman,D,house,VA,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Eugene Simon Vindman,D,house,VA,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Eugene Simon Vindman,D,house,VA,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Eugene Simon Vindman,D,house,VA,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Eugene Simon Vindman,D,house,VA,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Frank D. Lucas,R,house,OK,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Frank D. Lucas,R,house,OK,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Frank D. Lucas,R,house,OK,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Frank D. Lucas,R,house,OK,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Frank D. Lucas,R,house,OK,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Frank D. Lucas,R,house,OK,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Frank D. Lucas,R,house,OK,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Frank J. Mrvan,D,house,IN,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Frank J. Mrvan,D,house,IN,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Frank J. Mrvan,D,house,IN,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Frank J. Mrvan,D,house,IN,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Frank J. Mrvan,D,house,IN,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Frank J. Mrvan,D,house,IN,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Frank J. Mrvan,D,house,IN,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Frank Pallone, Jr.,D,house,NJ,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Frank Pallone, Jr.,D,house,NJ,06,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Frank Pallone, Jr.,D,house,NJ,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Frank Pallone, Jr.,D,house,NJ,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Frank Pallone, Jr.,D,house,NJ,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Frank Pallone, Jr.,D,house,NJ,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Frank Pallone, Jr.,D,house,NJ,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Frederica S. Wilson,D,house,FL,24,ECONOMY_TAXES,9,7,7,2,0,0,8
Frederica S. Wilson,D,house,FL,24,EDUCATION_WORKFORCE,6,3,3,0,3,2,5
Frederica S. Wilson,D,house,FL,24,ENVIRONMENT_ENERGY,3,1,1,0,2,2,2
Frederica S. Wilson,D,house,FL,24,HEALTH_SOCIAL,4,1,1,0,3,0,3
Frederica S. Wilson,D,house,FL,24,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Frederica S. Wilson,D,house,FL,24,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Frederica S. Wilson,D,house,FL,24,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Gabe Amo,D,house,RI,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Gabe Amo,D,house,RI,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Gabe Amo,D,house,RI,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Gabe Amo,D,house,RI,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Gabe Amo,D,house,RI,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Gabe Amo,D,house,RI,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Gabe Amo,D,house,RI,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Gabe Evans,R,house,CO,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Gabe Evans,R,house,CO,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Gabe Evans,R,house,CO,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Gabe Evans,R,house,CO,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Gabe Evans,R,house,CO,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Gabe Evans,R,house,CO,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Gabe Evans,R,house,CO,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Gabe Vasquez,D,house,NM,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Gabe Vasquez,D,house,NM,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Gabe Vasquez,D,house,NM,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Gabe Vasquez,D,house,NM,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Gabe Vasquez,D,house,NM,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Gabe Vasquez,D,house,NM,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Gabe Vasquez,D,house,NM,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Gary C. Peters,D,senate,MI,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Gary C. Peters,D,senate,MI,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Gary C. Peters,D,senate,MI,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Gary C. Peters,D,senate,MI,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Gary J. Palmer,R,house,AL,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Gary J. Palmer,R,house,AL,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Gary J. Palmer,R,house,AL,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Gary J. Palmer,R,house,AL,06,HEALTH_SOCIAL,4,1,1,0,3,1,3
Gary J. Palmer,R,house,AL,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Gary J. Palmer,R,house,AL,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Gary J. Palmer,R,house,AL,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
George Latimer,D,house,NY,16,ECONOMY_TAXES,9,7,7,2,0,0,8
George Latimer,D,house,NY,16,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
George Latimer,D,house,NY,16,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
George Latimer,D,house,NY,16,HEALTH_SOCIAL,4,1,1,0,3,0,3
George Latimer,D,house,NY,16,IMMIGRATION_BORDER,1,1,1,0,0,0,1
George Latimer,D,house,NY,16,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
George Latimer,D,house,NY,16,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
George Whitesides,D,house,CA,27,ECONOMY_TAXES,9,7,7,2,0,0,8
George Whitesides,D,house,CA,27,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
George Whitesides,D,house,CA,27,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
George Whitesides,D,house,CA,27,HEALTH_SOCIAL,4,1,1,0,3,0,3
George Whitesides,D,house,CA,27,IMMIGRATION_BORDER,1,1,1,0,0,0,1
George Whitesides,D,house,CA,27,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
George Whitesides,D,house,CA,27,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Gilbert Ray Cisneros, Jr.,D,house,CA,31,ECONOMY_TAXES,9,7,7,2,0,0,8
Gilbert Ray Cisneros, Jr.,D,house,CA,31,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Gilbert Ray Cisneros, Jr.,D,house,CA,31,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Gilbert Ray Cisneros, Jr.,D,house,CA,31,HEALTH_SOCIAL,4,1,1,0,3,0,3
Gilbert Ray Cisneros, Jr.,D,house,CA,31,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Gilbert Ray Cisneros, Jr.,D,house,CA,31,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Gilbert Ray Cisneros, Jr.,D,house,CA,31,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Glenn Grothman,R,house,WI,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Glenn Grothman,R,house,WI,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Glenn Grothman,R,house,WI,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Glenn Grothman,R,house,WI,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Glenn Grothman,R,house,WI,06,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Glenn Grothman,R,house,WI,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Glenn Grothman,R,house,WI,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Glenn Ivey,D,house,MD,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Glenn Ivey,D,house,MD,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Glenn Ivey,D,house,MD,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Glenn Ivey,D,house,MD,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Glenn Ivey,D,house,MD,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Glenn Ivey,D,house,MD,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Glenn Ivey,D,house,MD,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Glenn Thompson,R,house,PA,15,ECONOMY_TAXES,9,7,7,2,0,0,8
Glenn Thompson,R,house,PA,15,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Glenn Thompson,R,house,PA,15,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Glenn Thompson,R,house,PA,15,HEALTH_SOCIAL,4,1,1,0,3,0,3
Glenn Thompson,R,house,PA,15,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Glenn Thompson,R,house,PA,15,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Glenn Thompson,R,house,PA,15,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Grace Meng,D,house,NY,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Grace Meng,D,house,NY,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Grace Meng,D,house,NY,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Grace Meng,D,house,NY,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Grace Meng,D,house,NY,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Grace Meng,D,house,NY,06,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,1,7
Grace Meng,D,house,NY,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Green (TN),R,house,TN,00,ECONOMY_TAXES,5,4,4,1,0,0,4
Green (TN),R,house,TN,00,ENVIRONMENT_ENERGY,2,0,0,0,2,0,1
Green (TN),R,house,TN,00,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Green (TN),R,house,TN,00,JUSTICE_PUBLIC_SAFETY,7,4,4,1,2,2,5
Greene (GA),R,house,GA,00,ECONOMY_TAXES,9,7,5,2,0,3,8
Greene (GA),R,house,GA,00,EDUCATION_WORKFORCE,6,3,1,0,3,4,5
Greene (GA),R,house,GA,00,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Greene (GA),R,house,GA,00,HEALTH_SOCIAL,4,1,0,0,3,1,3
Greene (GA),R,house,GA,00,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Greene (GA),R,house,GA,00,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Greene (GA),R,house,GA,00,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Greg Casar,D,house,TX,35,ECONOMY_TAXES,9,7,6,2,0,1,8
Greg Casar,D,house,TX,35,EDUCATION_WORKFORCE,6,3,1,0,3,4,5
Greg Casar,D,house,TX,35,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Greg Casar,D,house,TX,35,HEALTH_SOCIAL,4,1,0,0,3,1,3
Greg Casar,D,house,TX,35,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Greg Casar,D,house,TX,35,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,3,7
Greg Casar,D,house,TX,35,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Greg Landsman,D,house,OH,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Greg Landsman,D,house,OH,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Greg Landsman,D,house,OH,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Greg Landsman,D,house,OH,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Greg Landsman,D,house,OH,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Greg Landsman,D,house,OH,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Greg Landsman,D,house,OH,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Greg Stanton,D,house,AZ,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Greg Stanton,D,house,AZ,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Greg Stanton,D,house,AZ,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Greg Stanton,D,house,AZ,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Greg Stanton,D,house,AZ,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Greg Stanton,D,house,AZ,04,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Greg Stanton,D,house,AZ,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Gregory F. Murphy,R,house,NC,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Gregory F. Murphy,R,house,NC,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Gregory F. Murphy,R,house,NC,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Gregory F. Murphy,R,house,NC,03,HEALTH_SOCIAL,4,1,0,0,3,4,3
Gregory F. Murphy,R,house,NC,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Gregory F. Murphy,R,house,NC,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Gregory F. Murphy,R,house,NC,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Gregory W. Meeks,D,house,NY,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Gregory W. Meeks,D,house,NY,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Gregory W. Meeks,D,house,NY,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Gregory W. Meeks,D,house,NY,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Gregory W. Meeks,D,house,NY,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Gregory W. Meeks,D,house,NY,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Gregory W. Meeks,D,house,NY,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Grijalva,D,house,AZ,00,ECONOMY_TAXES,1,1,0,0,0,1,1
Grijalva,D,house,AZ,00,ENVIRONMENT_ENERGY,2,0,0,0,2,2,1
Grijalva,D,house,AZ,00,JUSTICE_PUBLIC_SAFETY,2,1,0,1,0,2,2
Gus M. Bilirakis,R,house,FL,12,ECONOMY_TAXES,9,7,6,2,0,2,8
Gus M. Bilirakis,R,house,FL,12,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Gus M. Bilirakis,R,house,FL,12,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Gus M. Bilirakis,R,house,FL,12,HEALTH_SOCIAL,4,1,1,0,3,0,3
Gus M. Bilirakis,R,house,FL,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Gus M. Bilirakis,R,house,FL,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Gus M. Bilirakis,R,house,FL,12,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Guy Reschenthaler,R,house,PA,14,ECONOMY_TAXES,9,7,7,2,0,0,8
Guy Reschenthaler,R,house,PA,14,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Guy Reschenthaler,R,house,PA,14,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Guy Reschenthaler,R,house,PA,14,HEALTH_SOCIAL,4,1,1,0,3,0,3
Guy Reschenthaler,R,house,PA,14,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Guy Reschenthaler,R,house,PA,14,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Guy Reschenthaler,R,house,PA,14,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Gwen Moore,D,house,WI,04,ECONOMY_TAXES,9,7,6,2,0,1,8
Gwen Moore,D,house,WI,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Gwen Moore,D,house,WI,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Gwen Moore,D,house,WI,04,HEALTH_SOCIAL,4,1,1,0,3,1,3
Gwen Moore,D,house,WI,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Gwen Moore,D,house,WI,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Gwen Moore,D,house,WI,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
H. Morgan Griffith,R,house,VA,09,ECONOMY_TAXES,9,7,7,2,0,0,8
H. Morgan Griffith,R,house,VA,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
H. Morgan Griffith,R,house,VA,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
H. Morgan Griffith,R,house,VA,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
H. Morgan Griffith,R,house,VA,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
H. Morgan Griffith,R,house,VA,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
H. Morgan Griffith,R,house,VA,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Hakeem S. Jeffries,D,house,NY,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Hakeem S. Jeffries,D,house,NY,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Hakeem S. Jeffries,D,house,NY,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Hakeem S. Jeffries,D,house,NY,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Hakeem S. Jeffries,D,house,NY,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Hakeem S. Jeffries,D,house,NY,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Hakeem S. Jeffries,D,house,NY,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Haley M. Stevens,D,house,MI,11,ECONOMY_TAXES,9,7,7,2,0,0,8
Haley M. Stevens,D,house,MI,11,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Haley M. Stevens,D,house,MI,11,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Haley M. Stevens,D,house,MI,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
Haley M. Stevens,D,house,MI,11,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Haley M. Stevens,D,house,MI,11,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Haley M. Stevens,D,house,MI,11,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Harold Rogers,R,house,KY,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Harold Rogers,R,house,KY,05,EDUCATION_WORKFORCE,6,3,3,0,3,1,5
Harold Rogers,R,house,KY,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Harold Rogers,R,house,KY,05,HEALTH_SOCIAL,4,1,1,0,3,1,3
Harold Rogers,R,house,KY,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Harold Rogers,R,house,KY,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Harold Rogers,R,house,KY,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Harriet M. Hageman,R,house,WY,00,ECONOMY_TAXES,9,7,7,2,0,0,8
Harriet M. Hageman,R,house,WY,00,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Harriet M. Hageman,R,house,WY,00,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Harriet M. Hageman,R,house,WY,00,HEALTH_SOCIAL,4,1,1,0,3,0,3
Harriet M. Hageman,R,house,WY,00,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Harriet M. Hageman,R,house,WY,00,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Harriet M. Hageman,R,house,WY,00,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Henry C. "Hank" Johnson, Jr.,D,house,GA,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Henry C. "Hank" Johnson, Jr.,D,house,GA,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Henry C. "Hank" Johnson, Jr.,D,house,GA,04,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Henry C. "Hank" Johnson, Jr.,D,house,GA,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Henry C. "Hank" Johnson, Jr.,D,house,GA,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Henry C. "Hank" Johnson, Jr.,D,house,GA,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Henry C. "Hank" Johnson, Jr.,D,house,GA,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Henry Cuellar,D,house,TX,28,ECONOMY_TAXES,9,7,7,2,0,0,8
Henry Cuellar,D,house,TX,28,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Henry Cuellar,D,house,TX,28,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Henry Cuellar,D,house,TX,28,HEALTH_SOCIAL,4,1,1,0,3,0,3
Henry Cuellar,D,house,TX,28,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Henry Cuellar,D,house,TX,28,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Henry Cuellar,D,house,TX,28,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Herbert C. Conaway, Jr.,D,house,NJ,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Herbert C. Conaway, Jr.,D,house,NJ,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Herbert C. Conaway, Jr.,D,house,NJ,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Herbert C. Conaway, Jr.,D,house,NJ,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Herbert C. Conaway, Jr.,D,house,NJ,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Herbert C. Conaway, Jr.,D,house,NJ,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Herbert C. Conaway, Jr.,D,house,NJ,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Hillary J. Scholten,D,house,MI,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Hillary J. Scholten,D,house,MI,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Hillary J. Scholten,D,house,MI,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Hillary J. Scholten,D,house,MI,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Hillary J. Scholten,D,house,MI,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Hillary J. Scholten,D,house,MI,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Hillary J. Scholten,D,house,MI,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ilhan Omar,D,house,MN,05,ECONOMY_TAXES,9,7,6,2,0,1,8
Ilhan Omar,D,house,MN,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ilhan Omar,D,house,MN,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ilhan Omar,D,house,MN,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ilhan Omar,D,house,MN,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ilhan Omar,D,house,MN,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ilhan Omar,D,house,MN,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
J. French Hill,R,house,AR,02,ECONOMY_TAXES,9,7,7,2,0,0,8
J. French Hill,R,house,AR,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
J. French Hill,R,house,AR,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
J. French Hill,R,house,AR,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
J. French Hill,R,house,AR,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
J. French Hill,R,house,AR,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
J. French Hill,R,house,AR,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
J. Luis Correa,D,house,CA,46,ECONOMY_TAXES,9,7,7,2,0,0,8
J. Luis Correa,D,house,CA,46,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
J. Luis Correa,D,house,CA,46,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
J. Luis Correa,D,house,CA,46,HEALTH_SOCIAL,4,1,1,0,3,0,3
J. Luis Correa,D,house,CA,46,IMMIGRATION_BORDER,1,1,0,0,0,1,1
J. Luis Correa,D,house,CA,46,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,3,7
J. Luis Correa,D,house,CA,46,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Jack Bergman,R,house,MI,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Jack Bergman,R,house,MI,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jack Bergman,R,house,MI,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jack Bergman,R,house,MI,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jack Bergman,R,house,MI,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jack Bergman,R,house,MI,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jack Bergman,R,house,MI,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jack Reed,D,senate,RI,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Jack Reed,D,senate,RI,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Jack Reed,D,senate,RI,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Jack Reed,D,senate,RI,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Jacky Rosen,D,senate,NV,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Jacky Rosen,D,senate,NV,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Jacky Rosen,D,senate,NV,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Jacky Rosen,D,senate,NV,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Jahana Hayes,D,house,CT,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Jahana Hayes,D,house,CT,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jahana Hayes,D,house,CT,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jahana Hayes,D,house,CT,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jahana Hayes,D,house,CT,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jahana Hayes,D,house,CT,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jahana Hayes,D,house,CT,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jake Auchincloss,D,house,MA,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Jake Auchincloss,D,house,MA,04,EDUCATION_WORKFORCE,6,3,3,0,3,2,5
Jake Auchincloss,D,house,MA,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jake Auchincloss,D,house,MA,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jake Auchincloss,D,house,MA,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jake Auchincloss,D,house,MA,04,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,2,7
Jake Auchincloss,D,house,MA,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jake Ellzey,R,house,TX,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Jake Ellzey,R,house,TX,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jake Ellzey,R,house,TX,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jake Ellzey,R,house,TX,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jake Ellzey,R,house,TX,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jake Ellzey,R,house,TX,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jake Ellzey,R,house,TX,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
James  E. Risch,R,senate,ID,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
James  E. Risch,R,senate,ID,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
James  E. Risch,R,senate,ID,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
James  E. Risch,R,senate,ID,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
James A. Himes,D,house,CT,04,ECONOMY_TAXES,9,7,7,2,0,0,8
James A. Himes,D,house,CT,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
James A. Himes,D,house,CT,04,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
James A. Himes,D,house,CT,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
James A. Himes,D,house,CT,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
James A. Himes,D,house,CT,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
James A. Himes,D,house,CT,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
James C. Justice,R,senate,WV,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
James C. Justice,R,senate,WV,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
James C. Justice,R,senate,WV,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
James C. Justice,R,senate,WV,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
James C. Moylan,R,house,GU,00,ECONOMY_TAXES,1,0,0,1,0,0,1
James C. Moylan,R,house,GU,00,NATIONAL_SECURITY_FOREIGN,17,0,0,0,17,0,1
James Comer,R,house,KY,01,ECONOMY_TAXES,9,7,6,2,0,1,8
James Comer,R,house,KY,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
James Comer,R,house,KY,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
James Comer,R,house,KY,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
James Comer,R,house,KY,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
James Comer,R,house,KY,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
James Comer,R,house,KY,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
James E. Clyburn,D,house,SC,06,ECONOMY_TAXES,9,7,7,2,0,0,8
James E. Clyburn,D,house,SC,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
James E. Clyburn,D,house,SC,06,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
James E. Clyburn,D,house,SC,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
James E. Clyburn,D,house,SC,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
James E. Clyburn,D,house,SC,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
James E. Clyburn,D,house,SC,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
James Lankford,R,senate,OK,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
James Lankford,R,senate,OK,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
James Lankford,R,senate,OK,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
James Lankford,R,senate,OK,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
James P. McGovern,D,house,MA,02,ECONOMY_TAXES,9,7,7,2,0,0,8
James P. McGovern,D,house,MA,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
James P. McGovern,D,house,MA,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
James P. McGovern,D,house,MA,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
James P. McGovern,D,house,MA,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
James P. McGovern,D,house,MA,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
James P. McGovern,D,house,MA,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
James R. Baird,R,house,IN,04,ECONOMY_TAXES,9,7,7,2,0,0,8
James R. Baird,R,house,IN,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
James R. Baird,R,house,IN,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
James R. Baird,R,house,IN,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
James R. Baird,R,house,IN,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
James R. Baird,R,house,IN,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
James R. Baird,R,house,IN,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
James R. Walkinshaw,D,house,VA,11,ECONOMY_TAXES,4,3,3,1,0,0,4
James R. Walkinshaw,D,house,VA,11,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
James R. Walkinshaw,D,house,VA,11,ENVIRONMENT_ENERGY,1,1,1,0,0,0,1
James R. Walkinshaw,D,house,VA,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
James R. Walkinshaw,D,house,VA,11,JUSTICE_PUBLIC_SAFETY,6,2,2,0,4,0,3
James R. Walkinshaw,D,house,VA,11,NATIONAL_SECURITY_FOREIGN,19,2,2,1,16,0,4
Jamie Raskin,D,house,MD,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Jamie Raskin,D,house,MD,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jamie Raskin,D,house,MD,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jamie Raskin,D,house,MD,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jamie Raskin,D,house,MD,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jamie Raskin,D,house,MD,08,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,1,7
Jamie Raskin,D,house,MD,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Janelle S. Bynum,D,house,OR,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Janelle S. Bynum,D,house,OR,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Janelle S. Bynum,D,house,OR,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Janelle S. Bynum,D,house,OR,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Janelle S. Bynum,D,house,OR,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Janelle S. Bynum,D,house,OR,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Janelle S. Bynum,D,house,OR,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Janice D. Schakowsky,D,house,IL,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Janice D. Schakowsky,D,house,IL,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Janice D. Schakowsky,D,house,IL,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Janice D. Schakowsky,D,house,IL,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Janice D. Schakowsky,D,house,IL,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Janice D. Schakowsky,D,house,IL,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Janice D. Schakowsky,D,house,IL,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jared F. Golden,D,house,ME,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Jared F. Golden,D,house,ME,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jared F. Golden,D,house,ME,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jared F. Golden,D,house,ME,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jared F. Golden,D,house,ME,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jared F. Golden,D,house,ME,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jared F. Golden,D,house,ME,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jared Huffman,D,house,CA,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Jared Huffman,D,house,CA,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jared Huffman,D,house,CA,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jared Huffman,D,house,CA,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jared Huffman,D,house,CA,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jared Huffman,D,house,CA,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jared Huffman,D,house,CA,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jared Moskowitz,D,house,FL,23,ECONOMY_TAXES,9,7,7,2,0,0,8
Jared Moskowitz,D,house,FL,23,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jared Moskowitz,D,house,FL,23,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Jared Moskowitz,D,house,FL,23,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jared Moskowitz,D,house,FL,23,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jared Moskowitz,D,house,FL,23,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jared Moskowitz,D,house,FL,23,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jasmine Crockett,D,house,TX,30,ECONOMY_TAXES,9,7,6,2,0,1,8
Jasmine Crockett,D,house,TX,30,EDUCATION_WORKFORCE,6,3,1,0,3,2,5
Jasmine Crockett,D,house,TX,30,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Jasmine Crockett,D,house,TX,30,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jasmine Crockett,D,house,TX,30,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jasmine Crockett,D,house,TX,30,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jasmine Crockett,D,house,TX,30,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jason Crow,D,house,CO,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Jason Crow,D,house,CO,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jason Crow,D,house,CO,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jason Crow,D,house,CO,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jason Crow,D,house,CO,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jason Crow,D,house,CO,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jason Crow,D,house,CO,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jason Smith,R,house,MO,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Jason Smith,R,house,MO,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jason Smith,R,house,MO,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jason Smith,R,house,MO,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jason Smith,R,house,MO,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jason Smith,R,house,MO,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Jason Smith,R,house,MO,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jay Obernolte,R,house,CA,23,ECONOMY_TAXES,9,7,7,2,0,0,8
Jay Obernolte,R,house,CA,23,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jay Obernolte,R,house,CA,23,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jay Obernolte,R,house,CA,23,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jay Obernolte,R,house,CA,23,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jay Obernolte,R,house,CA,23,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jay Obernolte,R,house,CA,23,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jeanne Shaheen,D,senate,NH,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Jeanne Shaheen,D,senate,NH,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Jeanne Shaheen,D,senate,NH,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Jeanne Shaheen,D,senate,NH,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Jeff Crank,R,house,CO,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Jeff Crank,R,house,CO,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jeff Crank,R,house,CO,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jeff Crank,R,house,CO,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jeff Crank,R,house,CO,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jeff Crank,R,house,CO,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jeff Crank,R,house,CO,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jeff Hurd,R,house,CO,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Jeff Hurd,R,house,CO,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jeff Hurd,R,house,CO,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jeff Hurd,R,house,CO,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jeff Hurd,R,house,CO,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jeff Hurd,R,house,CO,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jeff Hurd,R,house,CO,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jeff Merkley,D,senate,OR,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Jeff Merkley,D,senate,OR,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Jeff Merkley,D,senate,OR,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Jeff Merkley,D,senate,OR,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Jefferson Shreve,R,house,IN,06,ECONOMY_TAXES,9,7,6,2,0,1,8
Jefferson Shreve,R,house,IN,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jefferson Shreve,R,house,IN,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jefferson Shreve,R,house,IN,06,HEALTH_SOCIAL,4,1,0,0,3,1,3
Jefferson Shreve,R,house,IN,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jefferson Shreve,R,house,IN,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jefferson Shreve,R,house,IN,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Jefferson Van Drew,R,house,NJ,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Jefferson Van Drew,R,house,NJ,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jefferson Van Drew,R,house,NJ,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jefferson Van Drew,R,house,NJ,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jefferson Van Drew,R,house,NJ,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jefferson Van Drew,R,house,NJ,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jefferson Van Drew,R,house,NJ,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jennifer A. Kiggans,R,house,VA,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Jennifer A. Kiggans,R,house,VA,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jennifer A. Kiggans,R,house,VA,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jennifer A. Kiggans,R,house,VA,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jennifer A. Kiggans,R,house,VA,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jennifer A. Kiggans,R,house,VA,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jennifer A. Kiggans,R,house,VA,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jennifer L. McClellan,D,house,VA,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Jennifer L. McClellan,D,house,VA,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jennifer L. McClellan,D,house,VA,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jennifer L. McClellan,D,house,VA,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jennifer L. McClellan,D,house,VA,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jennifer L. McClellan,D,house,VA,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jennifer L. McClellan,D,house,VA,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jerrold Nadler,D,house,NY,12,ECONOMY_TAXES,9,7,6,2,0,1,8
Jerrold Nadler,D,house,NY,12,EDUCATION_WORKFORCE,6,3,0,0,3,5,5
Jerrold Nadler,D,house,NY,12,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Jerrold Nadler,D,house,NY,12,HEALTH_SOCIAL,4,1,1,0,3,2,3
Jerrold Nadler,D,house,NY,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jerrold Nadler,D,house,NY,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jerrold Nadler,D,house,NY,12,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,2,5
Jerry Moran,R,senate,KS,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Jerry Moran,R,senate,KS,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Jerry Moran,R,senate,KS,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Jerry Moran,R,senate,KS,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Jesús G. "Chuy" García,D,house,IL,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Jesús G. "Chuy" García,D,house,IL,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jesús G. "Chuy" García,D,house,IL,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jesús G. "Chuy" García,D,house,IL,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jesús G. "Chuy" García,D,house,IL,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jesús G. "Chuy" García,D,house,IL,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jesús G. "Chuy" García,D,house,IL,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jill N. Tokuda,D,house,HI,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Jill N. Tokuda,D,house,HI,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jill N. Tokuda,D,house,HI,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jill N. Tokuda,D,house,HI,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jill N. Tokuda,D,house,HI,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jill N. Tokuda,D,house,HI,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jill N. Tokuda,D,house,HI,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jim Banks,R,senate,IN,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Jim Banks,R,senate,IN,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Jim Banks,R,senate,IN,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Jim Banks,R,senate,IN,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Jim Costa,D,house,CA,21,ECONOMY_TAXES,9,7,7,2,0,0,8
Jim Costa,D,house,CA,21,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jim Costa,D,house,CA,21,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jim Costa,D,house,CA,21,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jim Costa,D,house,CA,21,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jim Costa,D,house,CA,21,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jim Costa,D,house,CA,21,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,2,5
Jim Jordan,R,house,OH,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Jim Jordan,R,house,OH,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jim Jordan,R,house,OH,04,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Jim Jordan,R,house,OH,04,HEALTH_SOCIAL,4,1,1,0,3,1,3
Jim Jordan,R,house,OH,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jim Jordan,R,house,OH,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jim Jordan,R,house,OH,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jimmy Gomez,D,house,CA,34,ECONOMY_TAXES,9,7,7,2,0,0,8
Jimmy Gomez,D,house,CA,34,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jimmy Gomez,D,house,CA,34,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jimmy Gomez,D,house,CA,34,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jimmy Gomez,D,house,CA,34,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jimmy Gomez,D,house,CA,34,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jimmy Gomez,D,house,CA,34,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jimmy Panetta,D,house,CA,19,ECONOMY_TAXES,9,7,7,2,0,0,8
Jimmy Panetta,D,house,CA,19,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jimmy Panetta,D,house,CA,19,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jimmy Panetta,D,house,CA,19,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jimmy Panetta,D,house,CA,19,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jimmy Panetta,D,house,CA,19,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jimmy Panetta,D,house,CA,19,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jimmy Patronis,R,house,FL,01,ECONOMY_TAXES,8,6,6,2,0,0,8
Jimmy Patronis,R,house,FL,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jimmy Patronis,R,house,FL,01,ENVIRONMENT_ENERGY,1,1,1,0,0,0,1
Jimmy Patronis,R,house,FL,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jimmy Patronis,R,house,FL,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jimmy Patronis,R,house,FL,01,JUSTICE_PUBLIC_SAFETY,11,5,5,0,6,0,6
Jimmy Patronis,R,house,FL,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Joaquin Castro,D,house,TX,20,ECONOMY_TAXES,9,7,7,2,0,0,8
Joaquin Castro,D,house,TX,20,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Joaquin Castro,D,house,TX,20,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Joaquin Castro,D,house,TX,20,HEALTH_SOCIAL,4,1,1,0,3,0,3
Joaquin Castro,D,house,TX,20,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Joaquin Castro,D,house,TX,20,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Joaquin Castro,D,house,TX,20,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Jodey C. Arrington,R,house,TX,19,ECONOMY_TAXES,9,7,7,2,0,0,8
Jodey C. Arrington,R,house,TX,19,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jodey C. Arrington,R,house,TX,19,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jodey C. Arrington,R,house,TX,19,HEALTH_SOCIAL,4,1,1,0,3,1,3
Jodey C. Arrington,R,house,TX,19,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jodey C. Arrington,R,house,TX,19,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Jodey C. Arrington,R,house,TX,19,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Joe Courtney,D,house,CT,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Joe Courtney,D,house,CT,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Joe Courtney,D,house,CT,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Joe Courtney,D,house,CT,02,HEALTH_SOCIAL,4,1,0,0,3,4,3
Joe Courtney,D,house,CT,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Joe Courtney,D,house,CT,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Joe Courtney,D,house,CT,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Joe Neguse,D,house,CO,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Joe Neguse,D,house,CO,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Joe Neguse,D,house,CO,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Joe Neguse,D,house,CO,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Joe Neguse,D,house,CO,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Joe Neguse,D,house,CO,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Joe Neguse,D,house,CO,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Joe Wilson,R,house,SC,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Joe Wilson,R,house,SC,02,EDUCATION_WORKFORCE,6,3,3,0,3,2,5
Joe Wilson,R,house,SC,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Joe Wilson,R,house,SC,02,HEALTH_SOCIAL,4,1,0,0,3,1,3
Joe Wilson,R,house,SC,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Joe Wilson,R,house,SC,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Joe Wilson,R,house,SC,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
John  R. Curtis,R,senate,UT,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
John  R. Curtis,R,senate,UT,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
John  R. Curtis,R,senate,UT,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
John  R. Curtis,R,senate,UT,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
John B. Larson,D,house,CT,01,ECONOMY_TAXES,9,7,7,2,0,0,8
John B. Larson,D,house,CT,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
John B. Larson,D,house,CT,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
John B. Larson,D,house,CT,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
John B. Larson,D,house,CT,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
John B. Larson,D,house,CT,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
John B. Larson,D,house,CT,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
John Barrasso,R,senate,WY,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
John Barrasso,R,senate,WY,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
John Barrasso,R,senate,WY,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
John Barrasso,R,senate,WY,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
John Boozman,R,senate,AR,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
John Boozman,R,senate,AR,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
John Boozman,R,senate,AR,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
John Boozman,R,senate,AR,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
John Cornyn,R,senate,TX,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
John Cornyn,R,senate,TX,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
John Cornyn,R,senate,TX,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
John Cornyn,R,senate,TX,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
John Fetterman,D,senate,PA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
John Fetterman,D,senate,PA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
John Fetterman,D,senate,PA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
John Fetterman,D,senate,PA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
John Garamendi,D,house,CA,08,ECONOMY_TAXES,9,7,6,2,0,1,8
John Garamendi,D,house,CA,08,EDUCATION_WORKFORCE,6,3,1,0,3,4,5
John Garamendi,D,house,CA,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
John Garamendi,D,house,CA,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
John Garamendi,D,house,CA,08,IMMIGRATION_BORDER,1,1,0,0,0,1,1
John Garamendi,D,house,CA,08,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,2,7
John Garamendi,D,house,CA,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
John H. Rutherford,R,house,FL,05,ECONOMY_TAXES,9,7,7,2,0,0,8
John H. Rutherford,R,house,FL,05,EDUCATION_WORKFORCE,6,3,2,0,3,2,5
John H. Rutherford,R,house,FL,05,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
John H. Rutherford,R,house,FL,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
John H. Rutherford,R,house,FL,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
John H. Rutherford,R,house,FL,05,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,4,7
John H. Rutherford,R,house,FL,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
John Hoeven,R,senate,ND,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
John Hoeven,R,senate,ND,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
John Hoeven,R,senate,ND,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
John Hoeven,R,senate,ND,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
John J. McGuire III,R,house,VA,05,ECONOMY_TAXES,9,7,7,2,0,0,8
John J. McGuire III,R,house,VA,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
John J. McGuire III,R,house,VA,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
John J. McGuire III,R,house,VA,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
John J. McGuire III,R,house,VA,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
John J. McGuire III,R,house,VA,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
John J. McGuire III,R,house,VA,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
John James,R,house,MI,10,ECONOMY_TAXES,9,7,7,2,0,0,8
John James,R,house,MI,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
John James,R,house,MI,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
John James,R,house,MI,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
John James,R,house,MI,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
John James,R,house,MI,10,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,2,7
John James,R,house,MI,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
John Joyce,R,house,PA,13,ECONOMY_TAXES,9,7,7,2,0,0,8
John Joyce,R,house,PA,13,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
John Joyce,R,house,PA,13,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
John Joyce,R,house,PA,13,HEALTH_SOCIAL,4,1,1,0,3,0,3
John Joyce,R,house,PA,13,IMMIGRATION_BORDER,1,1,1,0,0,0,1
John Joyce,R,house,PA,13,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
John Joyce,R,house,PA,13,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
John Kennedy,R,senate,LA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
John Kennedy,R,senate,LA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
John Kennedy,R,senate,LA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
John Kennedy,R,senate,LA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
John R. Carter,R,house,TX,31,ECONOMY_TAXES,9,7,7,2,0,0,8
John R. Carter,R,house,TX,31,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
John R. Carter,R,house,TX,31,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
John R. Carter,R,house,TX,31,HEALTH_SOCIAL,4,1,1,0,3,0,3
John R. Carter,R,house,TX,31,IMMIGRATION_BORDER,1,1,1,0,0,0,1
John R. Carter,R,house,TX,31,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
John R. Carter,R,house,TX,31,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
John R. Moolenaar,R,house,MI,02,ECONOMY_TAXES,9,7,7,2,0,0,8
John R. Moolenaar,R,house,MI,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
John R. Moolenaar,R,house,MI,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
John R. Moolenaar,R,house,MI,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
John R. Moolenaar,R,house,MI,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
John R. Moolenaar,R,house,MI,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
John R. Moolenaar,R,house,MI,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
John Thune,R,senate,SD,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
John Thune,R,senate,SD,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
John Thune,R,senate,SD,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
John Thune,R,senate,SD,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
John W. Hickenlooper,D,senate,CO,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
John W. Hickenlooper,D,senate,CO,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,1,2
John W. Hickenlooper,D,senate,CO,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
John W. Hickenlooper,D,senate,CO,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
John W. Mannion,D,house,NY,22,ECONOMY_TAXES,9,7,7,2,0,0,8
John W. Mannion,D,house,NY,22,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
John W. Mannion,D,house,NY,22,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
John W. Mannion,D,house,NY,22,HEALTH_SOCIAL,4,1,1,0,3,0,3
John W. Mannion,D,house,NY,22,IMMIGRATION_BORDER,1,1,1,0,0,0,1
John W. Mannion,D,house,NY,22,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
John W. Mannion,D,house,NY,22,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
John W. Rose,R,house,TN,06,ECONOMY_TAXES,9,7,7,2,0,0,8
John W. Rose,R,house,TN,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
John W. Rose,R,house,TN,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
John W. Rose,R,house,TN,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
John W. Rose,R,house,TN,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
John W. Rose,R,house,TN,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
John W. Rose,R,house,TN,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Johnny Olszewski, Jr.,D,house,MD,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Johnny Olszewski, Jr.,D,house,MD,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Johnny Olszewski, Jr.,D,house,MD,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Johnny Olszewski, Jr.,D,house,MD,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Johnny Olszewski, Jr.,D,house,MD,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Johnny Olszewski, Jr.,D,house,MD,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Johnny Olszewski, Jr.,D,house,MD,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Jon Husted,R,senate,OH,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Jon Husted,R,senate,OH,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Jon Husted,R,senate,OH,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Jon Husted,R,senate,OH,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Jon Ossoff,D,senate,GA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Jon Ossoff,D,senate,GA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Jon Ossoff,D,senate,GA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Jon Ossoff,D,senate,GA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,2,0,0,2,1
Jonathan L. Jackson,D,house,IL,01,ECONOMY_TAXES,9,7,6,2,0,2,8
Jonathan L. Jackson,D,house,IL,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Jonathan L. Jackson,D,house,IL,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Jonathan L. Jackson,D,house,IL,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Jonathan L. Jackson,D,house,IL,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Jonathan L. Jackson,D,house,IL,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Jonathan L. Jackson,D,house,IL,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Joni Ernst,R,senate,IA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Joni Ernst,R,senate,IA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Joni Ernst,R,senate,IA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Joni Ernst,R,senate,IA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Joseph D. Morelle,D,house,NY,25,ECONOMY_TAXES,9,7,7,2,0,0,8
Joseph D. Morelle,D,house,NY,25,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Joseph D. Morelle,D,house,NY,25,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Joseph D. Morelle,D,house,NY,25,HEALTH_SOCIAL,4,1,1,0,3,0,3
Joseph D. Morelle,D,house,NY,25,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Joseph D. Morelle,D,house,NY,25,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Joseph D. Morelle,D,house,NY,25,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Josh Brecheen,R,house,OK,02,ECONOMY_TAXES,9,7,6,2,0,2,8
Josh Brecheen,R,house,OK,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Josh Brecheen,R,house,OK,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Josh Brecheen,R,house,OK,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Josh Brecheen,R,house,OK,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Josh Brecheen,R,house,OK,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Josh Brecheen,R,house,OK,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Josh Gottheimer,D,house,NJ,05,ECONOMY_TAXES,9,7,6,2,0,1,8
Josh Gottheimer,D,house,NJ,05,EDUCATION_WORKFORCE,6,3,3,0,3,1,5
Josh Gottheimer,D,house,NJ,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Josh Gottheimer,D,house,NJ,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Josh Gottheimer,D,house,NJ,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Josh Gottheimer,D,house,NJ,05,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,4,7
Josh Gottheimer,D,house,NJ,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Josh Harder,D,house,CA,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Josh Harder,D,house,CA,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Josh Harder,D,house,CA,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Josh Harder,D,house,CA,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Josh Harder,D,house,CA,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Josh Harder,D,house,CA,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Josh Harder,D,house,CA,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Josh Hawley,R,senate,MO,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Josh Hawley,R,senate,MO,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Josh Hawley,R,senate,MO,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Josh Hawley,R,senate,MO,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Josh Riley,D,house,NY,19,ECONOMY_TAXES,9,7,7,2,0,0,8
Josh Riley,D,house,NY,19,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Josh Riley,D,house,NY,19,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Josh Riley,D,house,NY,19,HEALTH_SOCIAL,4,1,1,0,3,0,3
Josh Riley,D,house,NY,19,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Josh Riley,D,house,NY,19,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Josh Riley,D,house,NY,19,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Joyce Beatty,D,house,OH,03,ECONOMY_TAXES,9,7,6,2,0,2,8
Joyce Beatty,D,house,OH,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Joyce Beatty,D,house,OH,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Joyce Beatty,D,house,OH,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Joyce Beatty,D,house,OH,03,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Joyce Beatty,D,house,OH,03,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,3,7
Joyce Beatty,D,house,OH,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Juan Ciscomani,R,house,AZ,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Juan Ciscomani,R,house,AZ,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Juan Ciscomani,R,house,AZ,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Juan Ciscomani,R,house,AZ,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Juan Ciscomani,R,house,AZ,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Juan Ciscomani,R,house,AZ,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Juan Ciscomani,R,house,AZ,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Juan Vargas,D,house,CA,52,ECONOMY_TAXES,9,7,7,2,0,0,8
Juan Vargas,D,house,CA,52,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Juan Vargas,D,house,CA,52,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Juan Vargas,D,house,CA,52,HEALTH_SOCIAL,4,1,1,0,3,0,3
Juan Vargas,D,house,CA,52,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Juan Vargas,D,house,CA,52,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Juan Vargas,D,house,CA,52,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Judy Chu,D,house,CA,28,ECONOMY_TAXES,9,7,7,2,0,0,8
Judy Chu,D,house,CA,28,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Judy Chu,D,house,CA,28,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Judy Chu,D,house,CA,28,HEALTH_SOCIAL,4,1,1,0,3,0,3
Judy Chu,D,house,CA,28,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Judy Chu,D,house,CA,28,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Judy Chu,D,house,CA,28,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Julia Brownley,D,house,CA,26,ECONOMY_TAXES,9,7,7,2,0,0,8
Julia Brownley,D,house,CA,26,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Julia Brownley,D,house,CA,26,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Julia Brownley,D,house,CA,26,HEALTH_SOCIAL,4,1,1,0,3,0,3
Julia Brownley,D,house,CA,26,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Julia Brownley,D,house,CA,26,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Julia Brownley,D,house,CA,26,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Julia Letlow,R,house,LA,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Julia Letlow,R,house,LA,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Julia Letlow,R,house,LA,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Julia Letlow,R,house,LA,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Julia Letlow,R,house,LA,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Julia Letlow,R,house,LA,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Julia Letlow,R,house,LA,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Julie Fedorchak,R,house,ND,00,ECONOMY_TAXES,9,7,7,2,0,1,8
Julie Fedorchak,R,house,ND,00,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Julie Fedorchak,R,house,ND,00,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Julie Fedorchak,R,house,ND,00,HEALTH_SOCIAL,4,1,1,0,3,0,3
Julie Fedorchak,R,house,ND,00,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Julie Fedorchak,R,house,ND,00,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Julie Fedorchak,R,house,ND,00,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Julie Johnson,D,house,TX,32,ECONOMY_TAXES,9,7,7,2,0,0,8
Julie Johnson,D,house,TX,32,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Julie Johnson,D,house,TX,32,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Julie Johnson,D,house,TX,32,HEALTH_SOCIAL,4,1,1,0,3,0,3
Julie Johnson,D,house,TX,32,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Julie Johnson,D,house,TX,32,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Julie Johnson,D,house,TX,32,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Kat Cammack,R,house,FL,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Kat Cammack,R,house,FL,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Kat Cammack,R,house,FL,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Kat Cammack,R,house,FL,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Kat Cammack,R,house,FL,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Kat Cammack,R,house,FL,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Kat Cammack,R,house,FL,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Katherine M. Clark,D,house,MA,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Katherine M. Clark,D,house,MA,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Katherine M. Clark,D,house,MA,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Katherine M. Clark,D,house,MA,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Katherine M. Clark,D,house,MA,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Katherine M. Clark,D,house,MA,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Katherine M. Clark,D,house,MA,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Kathy Castor,D,house,FL,14,ECONOMY_TAXES,9,7,7,2,0,0,8
Kathy Castor,D,house,FL,14,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Kathy Castor,D,house,FL,14,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Kathy Castor,D,house,FL,14,HEALTH_SOCIAL,4,1,1,0,3,0,3
Kathy Castor,D,house,FL,14,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Kathy Castor,D,house,FL,14,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Kathy Castor,D,house,FL,14,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Katie Boyd Britt,R,senate,AL,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Katie Boyd Britt,R,senate,AL,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Katie Boyd Britt,R,senate,AL,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Katie Boyd Britt,R,senate,AL,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Keith Self,R,house,TX,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Keith Self,R,house,TX,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Keith Self,R,house,TX,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Keith Self,R,house,TX,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Keith Self,R,house,TX,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Keith Self,R,house,TX,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,2,7
Keith Self,R,house,TX,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Kelly Morrison,D,house,MN,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Kelly Morrison,D,house,MN,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Kelly Morrison,D,house,MN,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Kelly Morrison,D,house,MN,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Kelly Morrison,D,house,MN,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Kelly Morrison,D,house,MN,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Kelly Morrison,D,house,MN,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ken Calvert,R,house,CA,41,ECONOMY_TAXES,9,7,7,2,0,0,8
Ken Calvert,R,house,CA,41,EDUCATION_WORKFORCE,6,3,3,0,3,1,5
Ken Calvert,R,house,CA,41,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ken Calvert,R,house,CA,41,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ken Calvert,R,house,CA,41,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ken Calvert,R,house,CA,41,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ken Calvert,R,house,CA,41,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Kevin Cramer,R,senate,ND,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Kevin Cramer,R,senate,ND,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Kevin Cramer,R,senate,ND,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Kevin Cramer,R,senate,ND,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Kevin Hern,R,house,OK,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Kevin Hern,R,house,OK,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Kevin Hern,R,house,OK,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Kevin Hern,R,house,OK,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Kevin Hern,R,house,OK,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Kevin Hern,R,house,OK,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Kevin Hern,R,house,OK,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Kevin Kiley,R,house,CA,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Kevin Kiley,R,house,CA,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Kevin Kiley,R,house,CA,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Kevin Kiley,R,house,CA,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Kevin Kiley,R,house,CA,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Kevin Kiley,R,house,CA,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Kevin Kiley,R,house,CA,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Kevin Mullin,D,house,CA,15,ECONOMY_TAXES,9,7,6,2,0,1,8
Kevin Mullin,D,house,CA,15,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Kevin Mullin,D,house,CA,15,ENVIRONMENT_ENERGY,3,1,0,0,2,3,2
Kevin Mullin,D,house,CA,15,HEALTH_SOCIAL,4,1,1,0,3,0,3
Kevin Mullin,D,house,CA,15,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Kevin Mullin,D,house,CA,15,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Kevin Mullin,D,house,CA,15,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Kim Schrier,D,house,WA,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Kim Schrier,D,house,WA,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Kim Schrier,D,house,WA,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Kim Schrier,D,house,WA,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Kim Schrier,D,house,WA,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Kim Schrier,D,house,WA,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Kim Schrier,D,house,WA,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Kimberlyn King-Hinds,R,house,MP,00,ECONOMY_TAXES,1,0,0,1,0,0,1
Kimberlyn King-Hinds,R,house,MP,00,NATIONAL_SECURITY_FOREIGN,17,0,0,0,17,0,1
Kirsten E. Gillibrand,D,senate,NY,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Kirsten E. Gillibrand,D,senate,NY,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Kirsten E. Gillibrand,D,senate,NY,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Kirsten E. Gillibrand,D,senate,NY,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Kristen McDonald Rivet,D,house,MI,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Kristen McDonald Rivet,D,house,MI,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Kristen McDonald Rivet,D,house,MI,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Kristen McDonald Rivet,D,house,MI,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Kristen McDonald Rivet,D,house,MI,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Kristen McDonald Rivet,D,house,MI,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Kristen McDonald Rivet,D,house,MI,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Kweisi Mfume,D,house,MD,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Kweisi Mfume,D,house,MD,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Kweisi Mfume,D,house,MD,07,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Kweisi Mfume,D,house,MD,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Kweisi Mfume,D,house,MD,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Kweisi Mfume,D,house,MD,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,2,7
Kweisi Mfume,D,house,MD,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
LaMalfa,R,house,CA,00,ECONOMY_TAXES,9,7,7,2,0,0,8
LaMalfa,R,house,CA,00,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
LaMalfa,R,house,CA,00,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
LaMalfa,R,house,CA,00,HEALTH_SOCIAL,4,1,1,0,3,0,3
LaMalfa,R,house,CA,00,IMMIGRATION_BORDER,1,1,1,0,0,0,1
LaMalfa,R,house,CA,00,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
LaMalfa,R,house,CA,00,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
LaMonica McIver,D,house,NJ,10,ECONOMY_TAXES,9,7,7,2,0,0,8
LaMonica McIver,D,house,NJ,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
LaMonica McIver,D,house,NJ,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
LaMonica McIver,D,house,NJ,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
LaMonica McIver,D,house,NJ,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
LaMonica McIver,D,house,NJ,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
LaMonica McIver,D,house,NJ,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Lance Gooden,R,house,TX,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Lance Gooden,R,house,TX,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Lance Gooden,R,house,TX,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lance Gooden,R,house,TX,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Lance Gooden,R,house,TX,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lance Gooden,R,house,TX,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Lance Gooden,R,house,TX,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Lateefah Simon,D,house,CA,12,ECONOMY_TAXES,9,7,7,2,0,0,8
Lateefah Simon,D,house,CA,12,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Lateefah Simon,D,house,CA,12,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lateefah Simon,D,house,CA,12,HEALTH_SOCIAL,4,1,1,0,3,0,3
Lateefah Simon,D,house,CA,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lateefah Simon,D,house,CA,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Lateefah Simon,D,house,CA,12,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Laura Friedman,D,house,CA,30,ECONOMY_TAXES,9,7,7,2,0,0,8
Laura Friedman,D,house,CA,30,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Laura Friedman,D,house,CA,30,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Laura Friedman,D,house,CA,30,HEALTH_SOCIAL,4,1,1,0,3,0,3
Laura Friedman,D,house,CA,30,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Laura Friedman,D,house,CA,30,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Laura Friedman,D,house,CA,30,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Laura Gillen,D,house,NY,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Laura Gillen,D,house,NY,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Laura Gillen,D,house,NY,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Laura Gillen,D,house,NY,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Laura Gillen,D,house,NY,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Laura Gillen,D,house,NY,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Laura Gillen,D,house,NY,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Laurel M. Lee,R,house,FL,15,ECONOMY_TAXES,9,7,6,2,0,1,8
Laurel M. Lee,R,house,FL,15,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Laurel M. Lee,R,house,FL,15,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Laurel M. Lee,R,house,FL,15,HEALTH_SOCIAL,4,1,1,0,3,0,3
Laurel M. Lee,R,house,FL,15,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Laurel M. Lee,R,house,FL,15,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,3,7
Laurel M. Lee,R,house,FL,15,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Lauren Boebert,R,house,CO,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Lauren Boebert,R,house,CO,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Lauren Boebert,R,house,CO,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lauren Boebert,R,house,CO,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Lauren Boebert,R,house,CO,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lauren Boebert,R,house,CO,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Lauren Boebert,R,house,CO,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Lauren Underwood,D,house,IL,14,ECONOMY_TAXES,9,7,7,2,0,0,8
Lauren Underwood,D,house,IL,14,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Lauren Underwood,D,house,IL,14,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lauren Underwood,D,house,IL,14,HEALTH_SOCIAL,4,1,1,0,3,0,3
Lauren Underwood,D,house,IL,14,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lauren Underwood,D,house,IL,14,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Lauren Underwood,D,house,IL,14,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Linda T. Sánchez,D,house,CA,38,ECONOMY_TAXES,9,7,7,2,0,0,8
Linda T. Sánchez,D,house,CA,38,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Linda T. Sánchez,D,house,CA,38,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Linda T. Sánchez,D,house,CA,38,HEALTH_SOCIAL,4,1,1,0,3,0,3
Linda T. Sánchez,D,house,CA,38,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Linda T. Sánchez,D,house,CA,38,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Linda T. Sánchez,D,house,CA,38,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,2,5
Lindsey Graham,R,senate,SC,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Lindsey Graham,R,senate,SC,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Lindsey Graham,R,senate,SC,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Lindsey Graham,R,senate,SC,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Lisa Blunt Rochester,D,senate,DE,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Lisa Blunt Rochester,D,senate,DE,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Lisa Blunt Rochester,D,senate,DE,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Lisa Blunt Rochester,D,senate,DE,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Lisa C. McClain,R,house,MI,09,ECONOMY_TAXES,9,7,6,2,0,1,8
Lisa C. McClain,R,house,MI,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Lisa C. McClain,R,house,MI,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lisa C. McClain,R,house,MI,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Lisa C. McClain,R,house,MI,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lisa C. McClain,R,house,MI,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Lisa C. McClain,R,house,MI,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Lisa Murkowski,R,senate,AK,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Lisa Murkowski,R,senate,AK,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Lisa Murkowski,R,senate,AK,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Lisa Murkowski,R,senate,AK,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Lizzie Fletcher,D,house,TX,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Lizzie Fletcher,D,house,TX,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Lizzie Fletcher,D,house,TX,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lizzie Fletcher,D,house,TX,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Lizzie Fletcher,D,house,TX,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lizzie Fletcher,D,house,TX,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Lizzie Fletcher,D,house,TX,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Lloyd Doggett,D,house,TX,37,ECONOMY_TAXES,9,7,7,2,0,0,8
Lloyd Doggett,D,house,TX,37,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Lloyd Doggett,D,house,TX,37,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lloyd Doggett,D,house,TX,37,HEALTH_SOCIAL,4,1,0,0,3,1,3
Lloyd Doggett,D,house,TX,37,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lloyd Doggett,D,house,TX,37,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,2,7
Lloyd Doggett,D,house,TX,37,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Lloyd Smucker,R,house,PA,11,ECONOMY_TAXES,9,7,7,2,0,0,8
Lloyd Smucker,R,house,PA,11,EDUCATION_WORKFORCE,6,3,3,0,3,1,5
Lloyd Smucker,R,house,PA,11,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lloyd Smucker,R,house,PA,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
Lloyd Smucker,R,house,PA,11,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lloyd Smucker,R,house,PA,11,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Lloyd Smucker,R,house,PA,11,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,2,5
Lois Frankel,D,house,FL,22,ECONOMY_TAXES,9,7,7,2,0,0,8
Lois Frankel,D,house,FL,22,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Lois Frankel,D,house,FL,22,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lois Frankel,D,house,FL,22,HEALTH_SOCIAL,4,1,1,0,3,0,3
Lois Frankel,D,house,FL,22,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lois Frankel,D,house,FL,22,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Lois Frankel,D,house,FL,22,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Lori Trahan,D,house,MA,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Lori Trahan,D,house,MA,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Lori Trahan,D,house,MA,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lori Trahan,D,house,MA,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Lori Trahan,D,house,MA,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lori Trahan,D,house,MA,03,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,4,7
Lori Trahan,D,house,MA,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Lucy McBath,D,house,GA,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Lucy McBath,D,house,GA,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Lucy McBath,D,house,GA,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Lucy McBath,D,house,GA,06,HEALTH_SOCIAL,4,1,0,0,3,4,3
Lucy McBath,D,house,GA,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Lucy McBath,D,house,GA,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Lucy McBath,D,house,GA,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Luz M. Rivas,D,house,CA,29,ECONOMY_TAXES,9,7,7,2,0,0,8
Luz M. Rivas,D,house,CA,29,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Luz M. Rivas,D,house,CA,29,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Luz M. Rivas,D,house,CA,29,HEALTH_SOCIAL,4,1,1,0,3,0,3
Luz M. Rivas,D,house,CA,29,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Luz M. Rivas,D,house,CA,29,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Luz M. Rivas,D,house,CA,29,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Madeleine Dean,D,house,PA,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Madeleine Dean,D,house,PA,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Madeleine Dean,D,house,PA,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Madeleine Dean,D,house,PA,04,HEALTH_SOCIAL,4,1,0,0,3,1,3
Madeleine Dean,D,house,PA,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Madeleine Dean,D,house,PA,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Madeleine Dean,D,house,PA,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Maggie Goodlander,D,house,NH,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Maggie Goodlander,D,house,NH,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Maggie Goodlander,D,house,NH,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Maggie Goodlander,D,house,NH,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Maggie Goodlander,D,house,NH,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Maggie Goodlander,D,house,NH,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Maggie Goodlander,D,house,NH,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Marc A. Veasey,D,house,TX,33,ECONOMY_TAXES,9,7,7,2,0,0,8
Marc A. Veasey,D,house,TX,33,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Marc A. Veasey,D,house,TX,33,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Marc A. Veasey,D,house,TX,33,HEALTH_SOCIAL,4,1,1,0,3,0,3
Marc A. Veasey,D,house,TX,33,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Marc A. Veasey,D,house,TX,33,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Marc A. Veasey,D,house,TX,33,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Marcy Kaptur,D,house,OH,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Marcy Kaptur,D,house,OH,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Marcy Kaptur,D,house,OH,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Marcy Kaptur,D,house,OH,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Marcy Kaptur,D,house,OH,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Marcy Kaptur,D,house,OH,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Marcy Kaptur,D,house,OH,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Margaret Wood Hassan,D,senate,NH,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Margaret Wood Hassan,D,senate,NH,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Margaret Wood Hassan,D,senate,NH,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Margaret Wood Hassan,D,senate,NH,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Maria Cantwell,D,senate,WA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Maria Cantwell,D,senate,WA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Maria Cantwell,D,senate,WA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Maria Cantwell,D,senate,WA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Maria Elvira Salazar,R,house,FL,27,ECONOMY_TAXES,9,7,7,2,0,1,8
Maria Elvira Salazar,R,house,FL,27,EDUCATION_WORKFORCE,6,3,2,0,3,2,5
Maria Elvira Salazar,R,house,FL,27,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Maria Elvira Salazar,R,house,FL,27,HEALTH_SOCIAL,4,1,1,0,3,0,3
Maria Elvira Salazar,R,house,FL,27,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Maria Elvira Salazar,R,house,FL,27,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Maria Elvira Salazar,R,house,FL,27,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,3,5
Mariannette Miller-Meeks,R,house,IA,01,ECONOMY_TAXES,9,7,6,2,0,1,8
Mariannette Miller-Meeks,R,house,IA,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mariannette Miller-Meeks,R,house,IA,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mariannette Miller-Meeks,R,house,IA,01,HEALTH_SOCIAL,4,1,1,0,3,1,3
Mariannette Miller-Meeks,R,house,IA,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mariannette Miller-Meeks,R,house,IA,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mariannette Miller-Meeks,R,house,IA,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Marie Gluesenkamp Perez,D,house,WA,03,ECONOMY_TAXES,9,7,6,2,0,1,8
Marie Gluesenkamp Perez,D,house,WA,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Marie Gluesenkamp Perez,D,house,WA,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Marie Gluesenkamp Perez,D,house,WA,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Marie Gluesenkamp Perez,D,house,WA,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Marie Gluesenkamp Perez,D,house,WA,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Marie Gluesenkamp Perez,D,house,WA,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Marilyn Strickland,D,house,WA,10,ECONOMY_TAXES,9,7,6,2,0,1,8
Marilyn Strickland,D,house,WA,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Marilyn Strickland,D,house,WA,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Marilyn Strickland,D,house,WA,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
Marilyn Strickland,D,house,WA,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Marilyn Strickland,D,house,WA,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Marilyn Strickland,D,house,WA,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mario Diaz-Balart,R,house,FL,26,ECONOMY_TAXES,9,7,7,2,0,0,8
Mario Diaz-Balart,R,house,FL,26,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Mario Diaz-Balart,R,house,FL,26,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mario Diaz-Balart,R,house,FL,26,HEALTH_SOCIAL,4,1,1,0,3,1,3
Mario Diaz-Balart,R,house,FL,26,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mario Diaz-Balart,R,house,FL,26,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Mario Diaz-Balart,R,house,FL,26,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mark Alford,R,house,MO,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Mark Alford,R,house,MO,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mark Alford,R,house,MO,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mark Alford,R,house,MO,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mark Alford,R,house,MO,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mark Alford,R,house,MO,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mark Alford,R,house,MO,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mark B. Messmer,R,house,IN,08,ECONOMY_TAXES,9,7,7,2,0,1,8
Mark B. Messmer,R,house,IN,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mark B. Messmer,R,house,IN,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mark B. Messmer,R,house,IN,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mark B. Messmer,R,house,IN,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mark B. Messmer,R,house,IN,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,2,7
Mark B. Messmer,R,house,IN,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mark DeSaulnier,D,house,CA,10,ECONOMY_TAXES,9,7,7,2,0,0,8
Mark DeSaulnier,D,house,CA,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mark DeSaulnier,D,house,CA,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mark DeSaulnier,D,house,CA,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mark DeSaulnier,D,house,CA,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mark DeSaulnier,D,house,CA,10,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Mark DeSaulnier,D,house,CA,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Mark E. Amodei,R,house,NV,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Mark E. Amodei,R,house,NV,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mark E. Amodei,R,house,NV,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mark E. Amodei,R,house,NV,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mark E. Amodei,R,house,NV,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mark E. Amodei,R,house,NV,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mark E. Amodei,R,house,NV,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mark Harris,R,house,NC,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Mark Harris,R,house,NC,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mark Harris,R,house,NC,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mark Harris,R,house,NC,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mark Harris,R,house,NC,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mark Harris,R,house,NC,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mark Harris,R,house,NC,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mark Kelly,D,senate,AZ,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Mark Kelly,D,senate,AZ,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Mark Kelly,D,senate,AZ,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Mark Kelly,D,senate,AZ,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Mark Pocan,D,house,WI,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Mark Pocan,D,house,WI,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mark Pocan,D,house,WI,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mark Pocan,D,house,WI,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mark Pocan,D,house,WI,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mark Pocan,D,house,WI,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mark Pocan,D,house,WI,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mark R. Warner,D,senate,VA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Mark R. Warner,D,senate,VA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Mark R. Warner,D,senate,VA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Mark R. Warner,D,senate,VA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Mark Takano,D,house,CA,39,ECONOMY_TAXES,9,7,7,2,0,0,8
Mark Takano,D,house,CA,39,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mark Takano,D,house,CA,39,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mark Takano,D,house,CA,39,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mark Takano,D,house,CA,39,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mark Takano,D,house,CA,39,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mark Takano,D,house,CA,39,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Markwayne Mullin,R,senate,OK,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Markwayne Mullin,R,senate,OK,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Markwayne Mullin,R,senate,OK,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Markwayne Mullin,R,senate,OK,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Marlin A. Stutzman,R,house,IN,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Marlin A. Stutzman,R,house,IN,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Marlin A. Stutzman,R,house,IN,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Marlin A. Stutzman,R,house,IN,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Marlin A. Stutzman,R,house,IN,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Marlin A. Stutzman,R,house,IN,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Marlin A. Stutzman,R,house,IN,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Marsha Blackburn,R,senate,TN,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Marsha Blackburn,R,senate,TN,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,0,6,0,7,2
Marsha Blackburn,R,senate,TN,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Marsha Blackburn,R,senate,TN,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,2,0,0,2,1
Martin Heinrich,D,senate,NM,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Martin Heinrich,D,senate,NM,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,0,6,0,7,2
Martin Heinrich,D,senate,NM,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Martin Heinrich,D,senate,NM,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Mary E. Miller,R,house,IL,15,ECONOMY_TAXES,9,7,7,2,0,0,8
Mary E. Miller,R,house,IL,15,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mary E. Miller,R,house,IL,15,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mary E. Miller,R,house,IL,15,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mary E. Miller,R,house,IL,15,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mary E. Miller,R,house,IL,15,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mary E. Miller,R,house,IL,15,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mary Gay Scanlon,D,house,PA,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Mary Gay Scanlon,D,house,PA,05,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Mary Gay Scanlon,D,house,PA,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mary Gay Scanlon,D,house,PA,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mary Gay Scanlon,D,house,PA,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mary Gay Scanlon,D,house,PA,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mary Gay Scanlon,D,house,PA,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Matt Van Epps,R,house,TN,07,EDUCATION_WORKFORCE,2,2,2,0,0,0,2
Matt Van Epps,R,house,TN,07,ENVIRONMENT_ENERGY,1,1,1,0,0,0,1
Matt Van Epps,R,house,TN,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Matt Van Epps,R,house,TN,07,NATIONAL_SECURITY_FOREIGN,2,1,1,1,0,0,2
Max L. Miller,R,house,OH,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Max L. Miller,R,house,OH,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Max L. Miller,R,house,OH,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Max L. Miller,R,house,OH,07,HEALTH_SOCIAL,4,1,0,0,3,1,3
Max L. Miller,R,house,OH,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Max L. Miller,R,house,OH,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Max L. Miller,R,house,OH,07,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,2,5
Maxine Dexter,D,house,OR,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Maxine Dexter,D,house,OR,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Maxine Dexter,D,house,OR,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Maxine Dexter,D,house,OR,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Maxine Dexter,D,house,OR,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Maxine Dexter,D,house,OR,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Maxine Dexter,D,house,OR,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Maxine Waters,D,house,CA,43,ECONOMY_TAXES,9,7,7,2,0,0,8
Maxine Waters,D,house,CA,43,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Maxine Waters,D,house,CA,43,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Maxine Waters,D,house,CA,43,HEALTH_SOCIAL,4,1,1,0,3,0,3
Maxine Waters,D,house,CA,43,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Maxine Waters,D,house,CA,43,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Maxine Waters,D,house,CA,43,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Maxwell Frost,D,house,FL,10,ECONOMY_TAXES,9,7,7,2,0,0,8
Maxwell Frost,D,house,FL,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Maxwell Frost,D,house,FL,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Maxwell Frost,D,house,FL,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
Maxwell Frost,D,house,FL,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Maxwell Frost,D,house,FL,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Maxwell Frost,D,house,FL,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mazie K. Hirono,D,senate,HI,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Mazie K. Hirono,D,senate,HI,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Mazie K. Hirono,D,senate,HI,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Mazie K. Hirono,D,senate,HI,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Melanie A. Stansbury,D,house,NM,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Melanie A. Stansbury,D,house,NM,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Melanie A. Stansbury,D,house,NM,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Melanie A. Stansbury,D,house,NM,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Melanie A. Stansbury,D,house,NM,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Melanie A. Stansbury,D,house,NM,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Melanie A. Stansbury,D,house,NM,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Michael A. Rulli,R,house,OH,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Michael A. Rulli,R,house,OH,06,EDUCATION_WORKFORCE,6,3,3,0,3,1,5
Michael A. Rulli,R,house,OH,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Michael A. Rulli,R,house,OH,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Michael A. Rulli,R,house,OH,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Michael A. Rulli,R,house,OH,06,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,5,7
Michael A. Rulli,R,house,OH,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Michael Baumgartner,R,house,WA,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Michael Baumgartner,R,house,WA,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Michael Baumgartner,R,house,WA,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Michael Baumgartner,R,house,WA,05,HEALTH_SOCIAL,4,1,1,0,3,1,3
Michael Baumgartner,R,house,WA,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Michael Baumgartner,R,house,WA,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Michael Baumgartner,R,house,WA,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Michael Cloud,R,house,TX,27,ECONOMY_TAXES,9,7,7,2,0,0,8
Michael Cloud,R,house,TX,27,EDUCATION_WORKFORCE,6,3,3,0,3,1,5
Michael Cloud,R,house,TX,27,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Michael Cloud,R,house,TX,27,HEALTH_SOCIAL,4,1,1,0,3,0,3
Michael Cloud,R,house,TX,27,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Michael Cloud,R,house,TX,27,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Michael Cloud,R,house,TX,27,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Michael F. Bennet,D,senate,CO,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Michael F. Bennet,D,senate,CO,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Michael F. Bennet,D,senate,CO,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Michael F. Bennet,D,senate,CO,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Michael Guest,R,house,MS,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Michael Guest,R,house,MS,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Michael Guest,R,house,MS,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Michael Guest,R,house,MS,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Michael Guest,R,house,MS,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Michael Guest,R,house,MS,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Michael Guest,R,house,MS,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Michael K. Simpson,R,house,ID,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Michael K. Simpson,R,house,ID,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Michael K. Simpson,R,house,ID,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Michael K. Simpson,R,house,ID,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Michael K. Simpson,R,house,ID,02,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Michael K. Simpson,R,house,ID,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Michael K. Simpson,R,house,ID,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Michael Lawler,R,house,NY,17,ECONOMY_TAXES,9,7,7,2,0,1,8
Michael Lawler,R,house,NY,17,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Michael Lawler,R,house,NY,17,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Michael Lawler,R,house,NY,17,HEALTH_SOCIAL,4,1,1,0,3,0,3
Michael Lawler,R,house,NY,17,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Michael Lawler,R,house,NY,17,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Michael Lawler,R,house,NY,17,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Michael R. Turner,R,house,OH,10,ECONOMY_TAXES,9,7,7,2,0,0,8
Michael R. Turner,R,house,OH,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Michael R. Turner,R,house,OH,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Michael R. Turner,R,house,OH,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
Michael R. Turner,R,house,OH,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Michael R. Turner,R,house,OH,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Michael R. Turner,R,house,OH,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Michael T. McCaul,R,house,TX,10,ECONOMY_TAXES,9,7,6,2,0,1,8
Michael T. McCaul,R,house,TX,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Michael T. McCaul,R,house,TX,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Michael T. McCaul,R,house,TX,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
Michael T. McCaul,R,house,TX,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Michael T. McCaul,R,house,TX,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Michael T. McCaul,R,house,TX,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Michelle Fischbach,R,house,MN,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Michelle Fischbach,R,house,MN,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Michelle Fischbach,R,house,MN,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Michelle Fischbach,R,house,MN,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Michelle Fischbach,R,house,MN,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Michelle Fischbach,R,house,MN,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Michelle Fischbach,R,house,MN,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Bost,R,house,IL,12,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Bost,R,house,IL,12,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Bost,R,house,IL,12,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Bost,R,house,IL,12,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Bost,R,house,IL,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Bost,R,house,IL,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mike Bost,R,house,IL,12,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Carey,R,house,OH,15,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Carey,R,house,OH,15,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Carey,R,house,OH,15,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Carey,R,house,OH,15,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Carey,R,house,OH,15,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Carey,R,house,OH,15,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Mike Carey,R,house,OH,15,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Collins,R,house,GA,10,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Collins,R,house,GA,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Collins,R,house,GA,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Collins,R,house,GA,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Collins,R,house,GA,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Collins,R,house,GA,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mike Collins,R,house,GA,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Crapo,R,senate,ID,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Mike Crapo,R,senate,ID,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Mike Crapo,R,senate,ID,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Mike Crapo,R,senate,ID,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Mike Ezell,R,house,MS,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Ezell,R,house,MS,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Ezell,R,house,MS,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Ezell,R,house,MS,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Ezell,R,house,MS,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Ezell,R,house,MS,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Mike Ezell,R,house,MS,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Flood,R,house,NE,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Flood,R,house,NE,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Flood,R,house,NE,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Flood,R,house,NE,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Flood,R,house,NE,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Flood,R,house,NE,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mike Flood,R,house,NE,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Haridopolos,R,house,FL,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Haridopolos,R,house,FL,08,EDUCATION_WORKFORCE,6,3,3,0,3,2,5
Mike Haridopolos,R,house,FL,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Haridopolos,R,house,FL,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Haridopolos,R,house,FL,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Haridopolos,R,house,FL,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mike Haridopolos,R,house,FL,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Johnson,R,house,LA,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Johnson,R,house,LA,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Johnson,R,house,LA,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Johnson,R,house,LA,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Johnson,R,house,LA,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Johnson,R,house,LA,04,JUSTICE_PUBLIC_SAFETY,11,6,6,0,5,0,6
Mike Johnson,R,house,LA,04,NATIONAL_SECURITY_FOREIGN,5,2,2,2,1,0,5
Mike Kelly,R,house,PA,16,ECONOMY_TAXES,9,7,6,2,0,1,8
Mike Kelly,R,house,PA,16,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Mike Kelly,R,house,PA,16,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Kelly,R,house,PA,16,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Kelly,R,house,PA,16,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Kelly,R,house,PA,16,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mike Kelly,R,house,PA,16,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Kennedy,R,house,UT,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Kennedy,R,house,UT,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Kennedy,R,house,UT,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Kennedy,R,house,UT,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Kennedy,R,house,UT,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Kennedy,R,house,UT,03,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,1,7
Mike Kennedy,R,house,UT,03,NATIONAL_SECURITY_FOREIGN,22,2,1,3,17,1,5
Mike Lee,R,senate,UT,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Mike Lee,R,senate,UT,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Mike Lee,R,senate,UT,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Mike Lee,R,senate,UT,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Mike Levin,D,house,CA,49,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Levin,D,house,CA,49,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Levin,D,house,CA,49,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Levin,D,house,CA,49,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Levin,D,house,CA,49,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Levin,D,house,CA,49,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mike Levin,D,house,CA,49,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Quigley,D,house,IL,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Quigley,D,house,IL,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Quigley,D,house,IL,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Quigley,D,house,IL,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Quigley,D,house,IL,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Quigley,D,house,IL,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mike Quigley,D,house,IL,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Rogers,R,house,AL,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Rogers,R,house,AL,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Rogers,R,house,AL,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Rogers,R,house,AL,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Rogers,R,house,AL,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Rogers,R,house,AL,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mike Rogers,R,house,AL,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mike Rounds,R,senate,SD,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Mike Rounds,R,senate,SD,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Mike Rounds,R,senate,SD,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Mike Rounds,R,senate,SD,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Mike Thompson,D,house,CA,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Mike Thompson,D,house,CA,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Mike Thompson,D,house,CA,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Mike Thompson,D,house,CA,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Mike Thompson,D,house,CA,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Mike Thompson,D,house,CA,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Mike Thompson,D,house,CA,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Mitch McConnell,R,senate,KY,Statewide,ECONOMY_TAXES,4,4,2,0,0,2,3
Mitch McConnell,R,senate,KY,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Mitch McConnell,R,senate,KY,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Mitch McConnell,R,senate,KY,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Monica De La Cruz,R,house,TX,15,ECONOMY_TAXES,9,7,6,2,0,1,8
Monica De La Cruz,R,house,TX,15,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Monica De La Cruz,R,house,TX,15,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Monica De La Cruz,R,house,TX,15,HEALTH_SOCIAL,4,1,1,0,3,0,3
Monica De La Cruz,R,house,TX,15,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Monica De La Cruz,R,house,TX,15,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Monica De La Cruz,R,house,TX,15,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Morgan Luttrell,R,house,TX,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Morgan Luttrell,R,house,TX,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Morgan Luttrell,R,house,TX,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Morgan Luttrell,R,house,TX,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Morgan Luttrell,R,house,TX,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Morgan Luttrell,R,house,TX,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Morgan Luttrell,R,house,TX,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Morgan McGarvey,D,house,KY,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Morgan McGarvey,D,house,KY,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Morgan McGarvey,D,house,KY,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Morgan McGarvey,D,house,KY,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Morgan McGarvey,D,house,KY,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Morgan McGarvey,D,house,KY,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Morgan McGarvey,D,house,KY,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nancy Mace,R,house,SC,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Nancy Mace,R,house,SC,01,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Nancy Mace,R,house,SC,01,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Nancy Mace,R,house,SC,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Nancy Mace,R,house,SC,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nancy Mace,R,house,SC,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nancy Mace,R,house,SC,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nancy Pelosi,D,house,CA,11,ECONOMY_TAXES,9,7,7,2,0,0,8
Nancy Pelosi,D,house,CA,11,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Nancy Pelosi,D,house,CA,11,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nancy Pelosi,D,house,CA,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
Nancy Pelosi,D,house,CA,11,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Nancy Pelosi,D,house,CA,11,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nancy Pelosi,D,house,CA,11,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nanette Diaz Barragán,D,house,CA,44,ECONOMY_TAXES,9,7,7,2,0,0,8
Nanette Diaz Barragán,D,house,CA,44,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Nanette Diaz Barragán,D,house,CA,44,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nanette Diaz Barragán,D,house,CA,44,HEALTH_SOCIAL,4,1,1,0,3,0,3
Nanette Diaz Barragán,D,house,CA,44,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nanette Diaz Barragán,D,house,CA,44,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nanette Diaz Barragán,D,house,CA,44,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nathaniel Moran,R,house,TX,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Nathaniel Moran,R,house,TX,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Nathaniel Moran,R,house,TX,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nathaniel Moran,R,house,TX,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Nathaniel Moran,R,house,TX,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nathaniel Moran,R,house,TX,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nathaniel Moran,R,house,TX,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Neal P. Dunn,R,house,FL,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Neal P. Dunn,R,house,FL,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Neal P. Dunn,R,house,FL,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Neal P. Dunn,R,house,FL,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Neal P. Dunn,R,house,FL,02,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Neal P. Dunn,R,house,FL,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Neal P. Dunn,R,house,FL,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nellie Pou,D,house,NJ,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Nellie Pou,D,house,NJ,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Nellie Pou,D,house,NJ,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nellie Pou,D,house,NJ,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Nellie Pou,D,house,NJ,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nellie Pou,D,house,NJ,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nellie Pou,D,house,NJ,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nicholas A. Langworthy,R,house,NY,23,ECONOMY_TAXES,9,7,7,2,0,0,8
Nicholas A. Langworthy,R,house,NY,23,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Nicholas A. Langworthy,R,house,NY,23,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nicholas A. Langworthy,R,house,NY,23,HEALTH_SOCIAL,4,1,1,0,3,0,3
Nicholas A. Langworthy,R,house,NY,23,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nicholas A. Langworthy,R,house,NY,23,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nicholas A. Langworthy,R,house,NY,23,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nicholas J. Begich III,R,house,AK,00,ECONOMY_TAXES,9,7,7,2,0,0,8
Nicholas J. Begich III,R,house,AK,00,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Nicholas J. Begich III,R,house,AK,00,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nicholas J. Begich III,R,house,AK,00,HEALTH_SOCIAL,4,1,1,0,3,0,3
Nicholas J. Begich III,R,house,AK,00,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nicholas J. Begich III,R,house,AK,00,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nicholas J. Begich III,R,house,AK,00,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nick LaLota,R,house,NY,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Nick LaLota,R,house,NY,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Nick LaLota,R,house,NY,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nick LaLota,R,house,NY,01,HEALTH_SOCIAL,4,1,1,0,3,1,3
Nick LaLota,R,house,NY,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nick LaLota,R,house,NY,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nick LaLota,R,house,NY,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nicole Malliotakis,R,house,NY,11,ECONOMY_TAXES,9,7,7,2,0,0,8
Nicole Malliotakis,R,house,NY,11,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Nicole Malliotakis,R,house,NY,11,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nicole Malliotakis,R,house,NY,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
Nicole Malliotakis,R,house,NY,11,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nicole Malliotakis,R,house,NY,11,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nicole Malliotakis,R,house,NY,11,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nikema Williams,D,house,GA,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Nikema Williams,D,house,GA,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Nikema Williams,D,house,GA,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nikema Williams,D,house,GA,05,HEALTH_SOCIAL,4,1,0,0,3,1,3
Nikema Williams,D,house,GA,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nikema Williams,D,house,GA,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nikema Williams,D,house,GA,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Nikki Budzinski,D,house,IL,13,ECONOMY_TAXES,9,7,7,2,0,0,8
Nikki Budzinski,D,house,IL,13,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Nikki Budzinski,D,house,IL,13,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nikki Budzinski,D,house,IL,13,HEALTH_SOCIAL,4,1,1,0,3,0,3
Nikki Budzinski,D,house,IL,13,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nikki Budzinski,D,house,IL,13,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nikki Budzinski,D,house,IL,13,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Norma J. Torres,D,house,CA,35,ECONOMY_TAXES,9,7,7,2,0,0,8
Norma J. Torres,D,house,CA,35,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Norma J. Torres,D,house,CA,35,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Norma J. Torres,D,house,CA,35,HEALTH_SOCIAL,4,1,1,0,3,0,3
Norma J. Torres,D,house,CA,35,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Norma J. Torres,D,house,CA,35,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Norma J. Torres,D,house,CA,35,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Nydia M. Velázquez,D,house,NY,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Nydia M. Velázquez,D,house,NY,07,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Nydia M. Velázquez,D,house,NY,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Nydia M. Velázquez,D,house,NY,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Nydia M. Velázquez,D,house,NY,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Nydia M. Velázquez,D,house,NY,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Nydia M. Velázquez,D,house,NY,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Pablo José Hernández,D,house,PR,00,ECONOMY_TAXES,1,0,0,1,0,0,1
Pablo José Hernández,D,house,PR,00,NATIONAL_SECURITY_FOREIGN,17,0,0,0,17,0,1
Pat Fallon,R,house,TX,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Pat Fallon,R,house,TX,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Pat Fallon,R,house,TX,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Pat Fallon,R,house,TX,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Pat Fallon,R,house,TX,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Pat Fallon,R,house,TX,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Pat Fallon,R,house,TX,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Pat Harrigan,R,house,NC,10,ECONOMY_TAXES,9,7,7,2,0,0,8
Pat Harrigan,R,house,NC,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Pat Harrigan,R,house,NC,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Pat Harrigan,R,house,NC,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
Pat Harrigan,R,house,NC,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Pat Harrigan,R,house,NC,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,2,7
Pat Harrigan,R,house,NC,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Patrick Ryan,D,house,NY,18,ECONOMY_TAXES,9,7,7,2,0,0,8
Patrick Ryan,D,house,NY,18,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Patrick Ryan,D,house,NY,18,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Patrick Ryan,D,house,NY,18,HEALTH_SOCIAL,4,1,1,0,3,0,3
Patrick Ryan,D,house,NY,18,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Patrick Ryan,D,house,NY,18,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Patrick Ryan,D,house,NY,18,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Patty Murray,D,senate,WA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Patty Murray,D,senate,WA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Patty Murray,D,senate,WA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Patty Murray,D,senate,WA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,2,0,0,2,1
Paul A. Gosar,R,house,AZ,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Paul A. Gosar,R,house,AZ,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Paul A. Gosar,R,house,AZ,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Paul A. Gosar,R,house,AZ,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Paul A. Gosar,R,house,AZ,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Paul A. Gosar,R,house,AZ,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Paul A. Gosar,R,house,AZ,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Paul Tonko,D,house,NY,20,ECONOMY_TAXES,9,7,7,2,0,0,8
Paul Tonko,D,house,NY,20,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Paul Tonko,D,house,NY,20,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Paul Tonko,D,house,NY,20,HEALTH_SOCIAL,4,1,1,0,3,0,3
Paul Tonko,D,house,NY,20,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Paul Tonko,D,house,NY,20,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Paul Tonko,D,house,NY,20,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Pete Aguilar,D,house,CA,33,ECONOMY_TAXES,9,7,7,2,0,0,8
Pete Aguilar,D,house,CA,33,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Pete Aguilar,D,house,CA,33,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Pete Aguilar,D,house,CA,33,HEALTH_SOCIAL,4,1,1,0,3,0,3
Pete Aguilar,D,house,CA,33,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Pete Aguilar,D,house,CA,33,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Pete Aguilar,D,house,CA,33,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Pete Ricketts,R,senate,NE,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Pete Ricketts,R,senate,NE,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Pete Ricketts,R,senate,NE,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Pete Ricketts,R,senate,NE,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Pete Sessions,R,house,TX,17,ECONOMY_TAXES,9,7,7,2,0,0,8
Pete Sessions,R,house,TX,17,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Pete Sessions,R,house,TX,17,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Pete Sessions,R,house,TX,17,HEALTH_SOCIAL,4,1,1,0,3,0,3
Pete Sessions,R,house,TX,17,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Pete Sessions,R,house,TX,17,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Pete Sessions,R,house,TX,17,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Pete Stauber,R,house,MN,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Pete Stauber,R,house,MN,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Pete Stauber,R,house,MN,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Pete Stauber,R,house,MN,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Pete Stauber,R,house,MN,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Pete Stauber,R,house,MN,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Pete Stauber,R,house,MN,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Peter Welch,D,senate,VT,Statewide,ECONOMY_TAXES,4,4,3,0,0,1,3
Peter Welch,D,senate,VT,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Peter Welch,D,senate,VT,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Peter Welch,D,senate,VT,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Pramila Jayapal,D,house,WA,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Pramila Jayapal,D,house,WA,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Pramila Jayapal,D,house,WA,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Pramila Jayapal,D,house,WA,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Pramila Jayapal,D,house,WA,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Pramila Jayapal,D,house,WA,07,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Pramila Jayapal,D,house,WA,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Raja Krishnamoorthi,D,house,IL,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Raja Krishnamoorthi,D,house,IL,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Raja Krishnamoorthi,D,house,IL,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Raja Krishnamoorthi,D,house,IL,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Raja Krishnamoorthi,D,house,IL,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Raja Krishnamoorthi,D,house,IL,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Raja Krishnamoorthi,D,house,IL,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ralph Norman,R,house,SC,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Ralph Norman,R,house,SC,05,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Ralph Norman,R,house,SC,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ralph Norman,R,house,SC,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ralph Norman,R,house,SC,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ralph Norman,R,house,SC,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ralph Norman,R,house,SC,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Rand Paul,R,senate,KY,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Rand Paul,R,senate,KY,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,1,2
Rand Paul,R,senate,KY,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Rand Paul,R,senate,KY,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,2,0,0,0,1
Randy Feenstra,R,house,IA,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Randy Feenstra,R,house,IA,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Randy Feenstra,R,house,IA,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Randy Feenstra,R,house,IA,04,HEALTH_SOCIAL,4,1,1,0,3,2,3
Randy Feenstra,R,house,IA,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Randy Feenstra,R,house,IA,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Randy Feenstra,R,house,IA,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Randy Fine,R,house,FL,06,ECONOMY_TAXES,8,6,6,2,0,0,8
Randy Fine,R,house,FL,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Randy Fine,R,house,FL,06,ENVIRONMENT_ENERGY,1,1,1,0,0,0,1
Randy Fine,R,house,FL,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Randy Fine,R,house,FL,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Randy Fine,R,house,FL,06,JUSTICE_PUBLIC_SAFETY,11,5,5,0,6,0,6
Randy Fine,R,house,FL,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Randy K. Weber, Sr.,R,house,TX,14,ECONOMY_TAXES,9,7,7,2,0,0,8
Randy K. Weber, Sr.,R,house,TX,14,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Randy K. Weber, Sr.,R,house,TX,14,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Randy K. Weber, Sr.,R,house,TX,14,HEALTH_SOCIAL,4,1,1,0,3,0,3
Randy K. Weber, Sr.,R,house,TX,14,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Randy K. Weber, Sr.,R,house,TX,14,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Randy K. Weber, Sr.,R,house,TX,14,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Raphael G. Warnock,D,senate,GA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Raphael G. Warnock,D,senate,GA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Raphael G. Warnock,D,senate,GA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Raphael G. Warnock,D,senate,GA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Rashida Tlaib,D,house,MI,12,ECONOMY_TAXES,9,7,6,2,0,1,8
Rashida Tlaib,D,house,MI,12,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Rashida Tlaib,D,house,MI,12,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Rashida Tlaib,D,house,MI,12,HEALTH_SOCIAL,4,1,1,0,3,0,3
Rashida Tlaib,D,house,MI,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Rashida Tlaib,D,house,MI,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Rashida Tlaib,D,house,MI,12,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Raul Ruiz,D,house,CA,25,ECONOMY_TAXES,9,7,7,2,0,0,8
Raul Ruiz,D,house,CA,25,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Raul Ruiz,D,house,CA,25,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Raul Ruiz,D,house,CA,25,HEALTH_SOCIAL,4,1,1,0,3,1,3
Raul Ruiz,D,house,CA,25,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Raul Ruiz,D,house,CA,25,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Raul Ruiz,D,house,CA,25,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Richard Blumenthal,D,senate,CT,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Richard Blumenthal,D,senate,CT,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Richard Blumenthal,D,senate,CT,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Richard Blumenthal,D,senate,CT,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Richard E. Neal,D,house,MA,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Richard E. Neal,D,house,MA,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Richard E. Neal,D,house,MA,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Richard E. Neal,D,house,MA,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Richard E. Neal,D,house,MA,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Richard E. Neal,D,house,MA,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Richard E. Neal,D,house,MA,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Richard Hudson,R,house,NC,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Richard Hudson,R,house,NC,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Richard Hudson,R,house,NC,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Richard Hudson,R,house,NC,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Richard Hudson,R,house,NC,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Richard Hudson,R,house,NC,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,2,7
Richard Hudson,R,house,NC,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Richard J. Durbin,D,senate,IL,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Richard J. Durbin,D,senate,IL,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Richard J. Durbin,D,senate,IL,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Richard J. Durbin,D,senate,IL,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Richard McCormick,R,house,GA,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Richard McCormick,R,house,GA,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Richard McCormick,R,house,GA,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Richard McCormick,R,house,GA,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Richard McCormick,R,house,GA,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Richard McCormick,R,house,GA,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Richard McCormick,R,house,GA,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Rick Larsen,D,house,WA,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Rick Larsen,D,house,WA,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Rick Larsen,D,house,WA,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Rick Larsen,D,house,WA,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Rick Larsen,D,house,WA,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Rick Larsen,D,house,WA,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Rick Larsen,D,house,WA,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Rick Scott,R,senate,FL,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Rick Scott,R,senate,FL,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Rick Scott,R,senate,FL,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Rick Scott,R,senate,FL,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Rick W. Allen,R,house,GA,12,ECONOMY_TAXES,9,7,7,2,0,0,8
Rick W. Allen,R,house,GA,12,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Rick W. Allen,R,house,GA,12,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Rick W. Allen,R,house,GA,12,HEALTH_SOCIAL,4,1,1,0,3,0,3
Rick W. Allen,R,house,GA,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Rick W. Allen,R,house,GA,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Rick W. Allen,R,house,GA,12,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Riley M. Moore,R,house,WV,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Riley M. Moore,R,house,WV,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Riley M. Moore,R,house,WV,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Riley M. Moore,R,house,WV,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Riley M. Moore,R,house,WV,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Riley M. Moore,R,house,WV,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Riley M. Moore,R,house,WV,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ritchie Torres,D,house,NY,15,ECONOMY_TAXES,9,7,7,2,0,0,8
Ritchie Torres,D,house,NY,15,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ritchie Torres,D,house,NY,15,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ritchie Torres,D,house,NY,15,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ritchie Torres,D,house,NY,15,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ritchie Torres,D,house,NY,15,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ritchie Torres,D,house,NY,15,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ro Khanna,D,house,CA,17,ECONOMY_TAXES,9,7,7,2,0,0,8
Ro Khanna,D,house,CA,17,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ro Khanna,D,house,CA,17,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ro Khanna,D,house,CA,17,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ro Khanna,D,house,CA,17,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ro Khanna,D,house,CA,17,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ro Khanna,D,house,CA,17,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Robert B. Aderholt,R,house,AL,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Robert B. Aderholt,R,house,AL,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Robert B. Aderholt,R,house,AL,04,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Robert B. Aderholt,R,house,AL,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Robert B. Aderholt,R,house,AL,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Robert B. Aderholt,R,house,AL,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Robert B. Aderholt,R,house,AL,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Robert C. "Bobby" Scott,D,house,VA,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Robert C. "Bobby" Scott,D,house,VA,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Robert C. "Bobby" Scott,D,house,VA,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Robert C. "Bobby" Scott,D,house,VA,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Robert C. "Bobby" Scott,D,house,VA,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Robert C. "Bobby" Scott,D,house,VA,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Robert C. "Bobby" Scott,D,house,VA,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Robert E. Latta,R,house,OH,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Robert E. Latta,R,house,OH,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Robert E. Latta,R,house,OH,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Robert E. Latta,R,house,OH,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Robert E. Latta,R,house,OH,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Robert E. Latta,R,house,OH,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Robert E. Latta,R,house,OH,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Robert F. Onder, Jr.,R,house,MO,03,ECONOMY_TAXES,9,7,6,2,0,1,8
Robert F. Onder, Jr.,R,house,MO,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Robert F. Onder, Jr.,R,house,MO,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Robert F. Onder, Jr.,R,house,MO,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Robert F. Onder, Jr.,R,house,MO,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Robert F. Onder, Jr.,R,house,MO,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Robert F. Onder, Jr.,R,house,MO,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Robert Garcia,D,house,CA,42,ECONOMY_TAXES,9,7,7,2,0,0,8
Robert Garcia,D,house,CA,42,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Robert Garcia,D,house,CA,42,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Robert Garcia,D,house,CA,42,HEALTH_SOCIAL,4,1,1,0,3,0,3
Robert Garcia,D,house,CA,42,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Robert Garcia,D,house,CA,42,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Robert Garcia,D,house,CA,42,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Robert J. Wittman,R,house,VA,01,ECONOMY_TAXES,9,7,7,2,0,1,8
Robert J. Wittman,R,house,VA,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Robert J. Wittman,R,house,VA,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Robert J. Wittman,R,house,VA,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Robert J. Wittman,R,house,VA,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Robert J. Wittman,R,house,VA,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Robert J. Wittman,R,house,VA,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Robert Menendez,D,house,NJ,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Robert Menendez,D,house,NJ,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Robert Menendez,D,house,NJ,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Robert Menendez,D,house,NJ,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Robert Menendez,D,house,NJ,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Robert Menendez,D,house,NJ,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Robert Menendez,D,house,NJ,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Robert P. Bresnahan, Jr.,R,house,PA,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Robert P. Bresnahan, Jr.,R,house,PA,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Robert P. Bresnahan, Jr.,R,house,PA,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Robert P. Bresnahan, Jr.,R,house,PA,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Robert P. Bresnahan, Jr.,R,house,PA,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Robert P. Bresnahan, Jr.,R,house,PA,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Robert P. Bresnahan, Jr.,R,house,PA,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Robin L. Kelly,D,house,IL,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Robin L. Kelly,D,house,IL,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Robin L. Kelly,D,house,IL,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Robin L. Kelly,D,house,IL,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Robin L. Kelly,D,house,IL,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Robin L. Kelly,D,house,IL,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Robin L. Kelly,D,house,IL,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Roger F. Wicker,R,senate,MS,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Roger F. Wicker,R,senate,MS,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Roger F. Wicker,R,senate,MS,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Roger F. Wicker,R,senate,MS,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Roger Marshall,R,senate,KS,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Roger Marshall,R,senate,KS,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Roger Marshall,R,senate,KS,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Roger Marshall,R,senate,KS,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Roger Williams,R,house,TX,25,ECONOMY_TAXES,9,7,6,2,0,1,8
Roger Williams,R,house,TX,25,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Roger Williams,R,house,TX,25,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Roger Williams,R,house,TX,25,HEALTH_SOCIAL,4,1,1,0,3,0,3
Roger Williams,R,house,TX,25,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Roger Williams,R,house,TX,25,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Roger Williams,R,house,TX,25,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ron Estes,R,house,KS,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Ron Estes,R,house,KS,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ron Estes,R,house,KS,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ron Estes,R,house,KS,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ron Estes,R,house,KS,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ron Estes,R,house,KS,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ron Estes,R,house,KS,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ron Johnson,R,senate,WI,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Ron Johnson,R,senate,WI,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Ron Johnson,R,senate,WI,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Ron Johnson,R,senate,WI,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Ron Wyden,D,senate,OR,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Ron Wyden,D,senate,OR,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Ron Wyden,D,senate,OR,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Ron Wyden,D,senate,OR,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Ronny Jackson,R,house,TX,13,ECONOMY_TAXES,9,7,7,2,0,0,8
Ronny Jackson,R,house,TX,13,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Ronny Jackson,R,house,TX,13,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ronny Jackson,R,house,TX,13,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ronny Jackson,R,house,TX,13,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ronny Jackson,R,house,TX,13,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ronny Jackson,R,house,TX,13,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Rosa L. DeLauro,D,house,CT,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Rosa L. DeLauro,D,house,CT,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Rosa L. DeLauro,D,house,CT,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Rosa L. DeLauro,D,house,CT,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Rosa L. DeLauro,D,house,CT,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Rosa L. DeLauro,D,house,CT,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Rosa L. DeLauro,D,house,CT,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ruben Gallego,D,senate,AZ,Statewide,ECONOMY_TAXES,4,4,3,0,0,1,3
Ruben Gallego,D,senate,AZ,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Ruben Gallego,D,senate,AZ,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Ruben Gallego,D,senate,AZ,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,2,0,0,2,1
Rudy Yakym III,R,house,IN,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Rudy Yakym III,R,house,IN,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Rudy Yakym III,R,house,IN,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Rudy Yakym III,R,house,IN,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Rudy Yakym III,R,house,IN,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Rudy Yakym III,R,house,IN,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Rudy Yakym III,R,house,IN,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Russ Fulcher,R,house,ID,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Russ Fulcher,R,house,ID,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Russ Fulcher,R,house,ID,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Russ Fulcher,R,house,ID,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Russ Fulcher,R,house,ID,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Russ Fulcher,R,house,ID,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Russ Fulcher,R,house,ID,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Russell Fry,R,house,SC,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Russell Fry,R,house,SC,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Russell Fry,R,house,SC,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Russell Fry,R,house,SC,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Russell Fry,R,house,SC,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Russell Fry,R,house,SC,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Russell Fry,R,house,SC,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ryan K. Zinke,R,house,MT,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Ryan K. Zinke,R,house,MT,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ryan K. Zinke,R,house,MT,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ryan K. Zinke,R,house,MT,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ryan K. Zinke,R,house,MT,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ryan K. Zinke,R,house,MT,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ryan K. Zinke,R,house,MT,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Ryan Mackenzie,R,house,PA,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Ryan Mackenzie,R,house,PA,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ryan Mackenzie,R,house,PA,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ryan Mackenzie,R,house,PA,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ryan Mackenzie,R,house,PA,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ryan Mackenzie,R,house,PA,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ryan Mackenzie,R,house,PA,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Salud O. Carbajal,D,house,CA,24,ECONOMY_TAXES,9,7,7,2,0,0,8
Salud O. Carbajal,D,house,CA,24,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Salud O. Carbajal,D,house,CA,24,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Salud O. Carbajal,D,house,CA,24,HEALTH_SOCIAL,4,1,1,0,3,0,3
Salud O. Carbajal,D,house,CA,24,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Salud O. Carbajal,D,house,CA,24,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Salud O. Carbajal,D,house,CA,24,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sam Graves,R,house,MO,06,ECONOMY_TAXES,9,7,6,2,0,1,8
Sam Graves,R,house,MO,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sam Graves,R,house,MO,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Sam Graves,R,house,MO,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sam Graves,R,house,MO,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sam Graves,R,house,MO,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sam Graves,R,house,MO,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sam T. Liccardo,D,house,CA,16,ECONOMY_TAXES,9,7,7,2,0,0,8
Sam T. Liccardo,D,house,CA,16,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sam T. Liccardo,D,house,CA,16,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Sam T. Liccardo,D,house,CA,16,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sam T. Liccardo,D,house,CA,16,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sam T. Liccardo,D,house,CA,16,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sam T. Liccardo,D,house,CA,16,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sanford D. Bishop, Jr.,D,house,GA,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Sanford D. Bishop, Jr.,D,house,GA,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sanford D. Bishop, Jr.,D,house,GA,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Sanford D. Bishop, Jr.,D,house,GA,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sanford D. Bishop, Jr.,D,house,GA,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sanford D. Bishop, Jr.,D,house,GA,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sanford D. Bishop, Jr.,D,house,GA,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sara Jacobs,D,house,CA,51,ECONOMY_TAXES,9,7,7,2,0,0,8
Sara Jacobs,D,house,CA,51,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sara Jacobs,D,house,CA,51,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Sara Jacobs,D,house,CA,51,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sara Jacobs,D,house,CA,51,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sara Jacobs,D,house,CA,51,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sara Jacobs,D,house,CA,51,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sarah Elfreth,D,house,MD,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Sarah Elfreth,D,house,MD,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sarah Elfreth,D,house,MD,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Sarah Elfreth,D,house,MD,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sarah Elfreth,D,house,MD,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sarah Elfreth,D,house,MD,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sarah Elfreth,D,house,MD,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sarah McBride,D,house,DE,00,ECONOMY_TAXES,9,7,7,2,0,0,8
Sarah McBride,D,house,DE,00,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sarah McBride,D,house,DE,00,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Sarah McBride,D,house,DE,00,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sarah McBride,D,house,DE,00,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sarah McBride,D,house,DE,00,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sarah McBride,D,house,DE,00,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Scott DesJarlais,R,house,TN,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Scott DesJarlais,R,house,TN,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Scott DesJarlais,R,house,TN,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Scott DesJarlais,R,house,TN,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Scott DesJarlais,R,house,TN,04,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Scott DesJarlais,R,house,TN,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,1,7
Scott DesJarlais,R,house,TN,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Scott Fitzgerald,R,house,WI,05,ECONOMY_TAXES,9,7,6,2,0,1,8
Scott Fitzgerald,R,house,WI,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Scott Fitzgerald,R,house,WI,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Scott Fitzgerald,R,house,WI,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Scott Fitzgerald,R,house,WI,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Scott Fitzgerald,R,house,WI,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Scott Fitzgerald,R,house,WI,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Scott Franklin,R,house,FL,18,ECONOMY_TAXES,9,7,7,2,0,0,8
Scott Franklin,R,house,FL,18,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Scott Franklin,R,house,FL,18,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Scott Franklin,R,house,FL,18,HEALTH_SOCIAL,4,1,1,0,3,0,3
Scott Franklin,R,house,FL,18,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Scott Franklin,R,house,FL,18,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Scott Franklin,R,house,FL,18,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Scott H. Peters,D,house,CA,50,ECONOMY_TAXES,9,7,7,2,0,0,8
Scott H. Peters,D,house,CA,50,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Scott H. Peters,D,house,CA,50,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Scott H. Peters,D,house,CA,50,HEALTH_SOCIAL,4,1,1,0,3,0,3
Scott H. Peters,D,house,CA,50,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Scott H. Peters,D,house,CA,50,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Scott H. Peters,D,house,CA,50,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Scott Perry,R,house,PA,10,ECONOMY_TAXES,9,7,6,2,0,1,8
Scott Perry,R,house,PA,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Scott Perry,R,house,PA,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Scott Perry,R,house,PA,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
Scott Perry,R,house,PA,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Scott Perry,R,house,PA,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Scott Perry,R,house,PA,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Sean Casten,D,house,IL,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Sean Casten,D,house,IL,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sean Casten,D,house,IL,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Sean Casten,D,house,IL,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sean Casten,D,house,IL,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sean Casten,D,house,IL,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sean Casten,D,house,IL,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Seth Magaziner,D,house,RI,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Seth Magaziner,D,house,RI,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Seth Magaziner,D,house,RI,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Seth Magaziner,D,house,RI,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Seth Magaziner,D,house,RI,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Seth Magaziner,D,house,RI,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Seth Magaziner,D,house,RI,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Seth Moulton,D,house,MA,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Seth Moulton,D,house,MA,06,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Seth Moulton,D,house,MA,06,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Seth Moulton,D,house,MA,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Seth Moulton,D,house,MA,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Seth Moulton,D,house,MA,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Seth Moulton,D,house,MA,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sharice Davids,D,house,KS,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Sharice Davids,D,house,KS,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sharice Davids,D,house,KS,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Sharice Davids,D,house,KS,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sharice Davids,D,house,KS,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sharice Davids,D,house,KS,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sharice Davids,D,house,KS,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sheila Cherfilus-McCormick,D,house,FL,20,ECONOMY_TAXES,9,7,7,2,0,0,8
Sheila Cherfilus-McCormick,D,house,FL,20,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sheila Cherfilus-McCormick,D,house,FL,20,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Sheila Cherfilus-McCormick,D,house,FL,20,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sheila Cherfilus-McCormick,D,house,FL,20,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sheila Cherfilus-McCormick,D,house,FL,20,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,1,7
Sheila Cherfilus-McCormick,D,house,FL,20,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sheldon Whitehouse,D,senate,RI,Statewide,ECONOMY_TAXES,4,4,3,0,0,1,3
Sheldon Whitehouse,D,senate,RI,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Sheldon Whitehouse,D,senate,RI,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Sheldon Whitehouse,D,senate,RI,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Shelley Moore Capito,R,senate,WV,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Shelley Moore Capito,R,senate,WV,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Shelley Moore Capito,R,senate,WV,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Shelley Moore Capito,R,senate,WV,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Sheri Biggs,R,house,SC,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Sheri Biggs,R,house,SC,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sheri Biggs,R,house,SC,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Sheri Biggs,R,house,SC,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sheri Biggs,R,house,SC,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sheri Biggs,R,house,SC,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sheri Biggs,R,house,SC,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sherrill,D,house,NJ,00,ECONOMY_TAXES,8,6,4,2,0,4,7
Sherrill,D,house,NJ,00,EDUCATION_WORKFORCE,1,0,0,0,1,0,1
Sherrill,D,house,NJ,00,ENVIRONMENT_ENERGY,2,0,0,0,2,0,1
Sherrill,D,house,NJ,00,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sherrill,D,house,NJ,00,JUSTICE_PUBLIC_SAFETY,13,6,2,1,6,10,7
Sherrill,D,house,NJ,00,NATIONAL_SECURITY_FOREIGN,20,1,0,2,17,20,3
Shomari Figures,D,house,AL,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Shomari Figures,D,house,AL,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Shomari Figures,D,house,AL,02,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Shomari Figures,D,house,AL,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Shomari Figures,D,house,AL,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Shomari Figures,D,house,AL,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Shomari Figures,D,house,AL,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Shontel M. Brown,D,house,OH,11,ECONOMY_TAXES,9,7,7,2,0,0,8
Shontel M. Brown,D,house,OH,11,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Shontel M. Brown,D,house,OH,11,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Shontel M. Brown,D,house,OH,11,HEALTH_SOCIAL,4,1,1,0,3,0,3
Shontel M. Brown,D,house,OH,11,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Shontel M. Brown,D,house,OH,11,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Shontel M. Brown,D,house,OH,11,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Shri Thanedar,D,house,MI,13,ECONOMY_TAXES,9,7,7,2,0,0,8
Shri Thanedar,D,house,MI,13,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Shri Thanedar,D,house,MI,13,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Shri Thanedar,D,house,MI,13,HEALTH_SOCIAL,4,1,1,0,3,0,3
Shri Thanedar,D,house,MI,13,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Shri Thanedar,D,house,MI,13,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Shri Thanedar,D,house,MI,13,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Stacey E. Plaskett,D,house,VI,00,ECONOMY_TAXES,1,0,0,1,0,0,1
Stacey E. Plaskett,D,house,VI,00,NATIONAL_SECURITY_FOREIGN,17,0,0,0,17,0,1
Steny H. Hoyer,D,house,MD,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Steny H. Hoyer,D,house,MD,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Steny H. Hoyer,D,house,MD,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Steny H. Hoyer,D,house,MD,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Steny H. Hoyer,D,house,MD,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Steny H. Hoyer,D,house,MD,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Steny H. Hoyer,D,house,MD,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Stephanie I. Bice,R,house,OK,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Stephanie I. Bice,R,house,OK,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Stephanie I. Bice,R,house,OK,05,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Stephanie I. Bice,R,house,OK,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Stephanie I. Bice,R,house,OK,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Stephanie I. Bice,R,house,OK,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Stephanie I. Bice,R,house,OK,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Stephen F. Lynch,D,house,MA,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Stephen F. Lynch,D,house,MA,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Stephen F. Lynch,D,house,MA,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Stephen F. Lynch,D,house,MA,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Stephen F. Lynch,D,house,MA,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Stephen F. Lynch,D,house,MA,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Stephen F. Lynch,D,house,MA,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Steve Cohen,D,house,TN,09,ECONOMY_TAXES,9,7,7,2,0,0,8
Steve Cohen,D,house,TN,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Steve Cohen,D,house,TN,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Steve Cohen,D,house,TN,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Steve Cohen,D,house,TN,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Steve Cohen,D,house,TN,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Steve Cohen,D,house,TN,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Steve Daines,R,senate,MT,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Steve Daines,R,senate,MT,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Steve Daines,R,senate,MT,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Steve Daines,R,senate,MT,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Steve Scalise,R,house,LA,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Steve Scalise,R,house,LA,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Steve Scalise,R,house,LA,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Steve Scalise,R,house,LA,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Steve Scalise,R,house,LA,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Steve Scalise,R,house,LA,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Steve Scalise,R,house,LA,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Steve Womack,R,house,AR,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Steve Womack,R,house,AR,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Steve Womack,R,house,AR,03,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Steve Womack,R,house,AR,03,HEALTH_SOCIAL,4,1,0,0,3,2,3
Steve Womack,R,house,AR,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Steve Womack,R,house,AR,03,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,3,7
Steve Womack,R,house,AR,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Steven Horsford,D,house,NV,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Steven Horsford,D,house,NV,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Steven Horsford,D,house,NV,04,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Steven Horsford,D,house,NV,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Steven Horsford,D,house,NV,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Steven Horsford,D,house,NV,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Steven Horsford,D,house,NV,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Suhas Subramanyam,D,house,VA,10,ECONOMY_TAXES,9,7,7,2,0,0,8
Suhas Subramanyam,D,house,VA,10,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Suhas Subramanyam,D,house,VA,10,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Suhas Subramanyam,D,house,VA,10,HEALTH_SOCIAL,4,1,1,0,3,0,3
Suhas Subramanyam,D,house,VA,10,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Suhas Subramanyam,D,house,VA,10,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Suhas Subramanyam,D,house,VA,10,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Summer L. Lee,D,house,PA,12,ECONOMY_TAXES,9,7,7,2,0,0,8
Summer L. Lee,D,house,PA,12,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Summer L. Lee,D,house,PA,12,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Summer L. Lee,D,house,PA,12,HEALTH_SOCIAL,4,1,1,0,3,0,3
Summer L. Lee,D,house,PA,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Summer L. Lee,D,house,PA,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Summer L. Lee,D,house,PA,12,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Susan M. Collins,R,senate,ME,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Susan M. Collins,R,senate,ME,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Susan M. Collins,R,senate,ME,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Susan M. Collins,R,senate,ME,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Susie Lee,D,house,NV,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Susie Lee,D,house,NV,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Susie Lee,D,house,NV,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Susie Lee,D,house,NV,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Susie Lee,D,house,NV,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Susie Lee,D,house,NV,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Susie Lee,D,house,NV,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Suzan K. DelBene,D,house,WA,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Suzan K. DelBene,D,house,WA,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Suzan K. DelBene,D,house,WA,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Suzan K. DelBene,D,house,WA,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Suzan K. DelBene,D,house,WA,01,IMMIGRATION_BORDER,1,1,0,0,0,1,1
Suzan K. DelBene,D,house,WA,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Suzan K. DelBene,D,house,WA,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Suzanne Bonamici,D,house,OR,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Suzanne Bonamici,D,house,OR,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Suzanne Bonamici,D,house,OR,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Suzanne Bonamici,D,house,OR,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Suzanne Bonamici,D,house,OR,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Suzanne Bonamici,D,house,OR,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Suzanne Bonamici,D,house,OR,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sydney Kamlager-Dove,D,house,CA,37,ECONOMY_TAXES,9,7,6,2,0,1,8
Sydney Kamlager-Dove,D,house,CA,37,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sydney Kamlager-Dove,D,house,CA,37,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Sydney Kamlager-Dove,D,house,CA,37,HEALTH_SOCIAL,4,1,1,0,3,0,3
Sydney Kamlager-Dove,D,house,CA,37,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sydney Kamlager-Dove,D,house,CA,37,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sydney Kamlager-Dove,D,house,CA,37,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Sylvia R. Garcia,D,house,TX,29,ECONOMY_TAXES,9,7,7,2,0,0,8
Sylvia R. Garcia,D,house,TX,29,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Sylvia R. Garcia,D,house,TX,29,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Sylvia R. Garcia,D,house,TX,29,HEALTH_SOCIAL,4,1,1,0,3,2,3
Sylvia R. Garcia,D,house,TX,29,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Sylvia R. Garcia,D,house,TX,29,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Sylvia R. Garcia,D,house,TX,29,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tammy Baldwin,D,senate,WI,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Tammy Baldwin,D,senate,WI,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Tammy Baldwin,D,senate,WI,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Tammy Baldwin,D,senate,WI,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,2,0,0,0,1
Tammy Duckworth,D,senate,IL,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Tammy Duckworth,D,senate,IL,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Tammy Duckworth,D,senate,IL,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Tammy Duckworth,D,senate,IL,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Ted Budd,R,senate,NC,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Ted Budd,R,senate,NC,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,0,6,0,6,2
Ted Budd,R,senate,NC,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Ted Budd,R,senate,NC,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Ted Cruz,R,senate,TX,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Ted Cruz,R,senate,TX,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Ted Cruz,R,senate,TX,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Ted Cruz,R,senate,TX,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Ted Lieu,D,house,CA,36,ECONOMY_TAXES,9,7,7,2,0,0,8
Ted Lieu,D,house,CA,36,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Ted Lieu,D,house,CA,36,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Ted Lieu,D,house,CA,36,HEALTH_SOCIAL,4,1,1,0,3,0,3
Ted Lieu,D,house,CA,36,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Ted Lieu,D,house,CA,36,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Ted Lieu,D,house,CA,36,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Teresa Leger Fernandez,D,house,NM,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Teresa Leger Fernandez,D,house,NM,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Teresa Leger Fernandez,D,house,NM,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Teresa Leger Fernandez,D,house,NM,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Teresa Leger Fernandez,D,house,NM,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Teresa Leger Fernandez,D,house,NM,03,JUSTICE_PUBLIC_SAFETY,13,6,5,1,6,2,7
Teresa Leger Fernandez,D,house,NM,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Terri A. Sewell,D,house,AL,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Terri A. Sewell,D,house,AL,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Terri A. Sewell,D,house,AL,07,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Terri A. Sewell,D,house,AL,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Terri A. Sewell,D,house,AL,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Terri A. Sewell,D,house,AL,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Terri A. Sewell,D,house,AL,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Thom Tillis,R,senate,NC,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Thom Tillis,R,senate,NC,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Thom Tillis,R,senate,NC,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Thom Tillis,R,senate,NC,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Thomas H. Kean, Jr.,R,house,NJ,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Thomas H. Kean, Jr.,R,house,NJ,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Thomas H. Kean, Jr.,R,house,NJ,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Thomas H. Kean, Jr.,R,house,NJ,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Thomas H. Kean, Jr.,R,house,NJ,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Thomas H. Kean, Jr.,R,house,NJ,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Thomas H. Kean, Jr.,R,house,NJ,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Thomas Massie,R,house,KY,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Thomas Massie,R,house,KY,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Thomas Massie,R,house,KY,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Thomas Massie,R,house,KY,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Thomas Massie,R,house,KY,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Thomas Massie,R,house,KY,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Thomas Massie,R,house,KY,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Thomas P. Tiffany,R,house,WI,07,ECONOMY_TAXES,9,7,7,2,0,0,8
Thomas P. Tiffany,R,house,WI,07,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Thomas P. Tiffany,R,house,WI,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Thomas P. Tiffany,R,house,WI,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Thomas P. Tiffany,R,house,WI,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Thomas P. Tiffany,R,house,WI,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Thomas P. Tiffany,R,house,WI,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Thomas R. Suozzi,D,house,NY,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Thomas R. Suozzi,D,house,NY,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Thomas R. Suozzi,D,house,NY,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Thomas R. Suozzi,D,house,NY,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Thomas R. Suozzi,D,house,NY,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Thomas R. Suozzi,D,house,NY,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Thomas R. Suozzi,D,house,NY,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tim Burchett,R,house,TN,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Tim Burchett,R,house,TN,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Tim Burchett,R,house,TN,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Tim Burchett,R,house,TN,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Tim Burchett,R,house,TN,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Tim Burchett,R,house,TN,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Tim Burchett,R,house,TN,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tim Kaine,D,senate,VA,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Tim Kaine,D,senate,VA,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Tim Kaine,D,senate,VA,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Tim Kaine,D,senate,VA,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Tim Moore,R,house,NC,14,ECONOMY_TAXES,9,7,7,2,0,0,8
Tim Moore,R,house,NC,14,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Tim Moore,R,house,NC,14,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Tim Moore,R,house,NC,14,HEALTH_SOCIAL,4,1,1,0,3,0,3
Tim Moore,R,house,NC,14,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Tim Moore,R,house,NC,14,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Tim Moore,R,house,NC,14,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tim Scott,R,senate,SC,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Tim Scott,R,senate,SC,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Tim Scott,R,senate,SC,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Tim Scott,R,senate,SC,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Tim Sheehy,R,senate,MT,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Tim Sheehy,R,senate,MT,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Tim Sheehy,R,senate,MT,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Tim Sheehy,R,senate,MT,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Tim Walberg,R,house,MI,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Tim Walberg,R,house,MI,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Tim Walberg,R,house,MI,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Tim Walberg,R,house,MI,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Tim Walberg,R,house,MI,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Tim Walberg,R,house,MI,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Tim Walberg,R,house,MI,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Timothy M. Kennedy,D,house,NY,26,ECONOMY_TAXES,9,7,7,2,0,0,8
Timothy M. Kennedy,D,house,NY,26,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Timothy M. Kennedy,D,house,NY,26,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Timothy M. Kennedy,D,house,NY,26,HEALTH_SOCIAL,4,1,1,0,3,0,3
Timothy M. Kennedy,D,house,NY,26,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Timothy M. Kennedy,D,house,NY,26,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Timothy M. Kennedy,D,house,NY,26,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tina Smith,D,senate,MN,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Tina Smith,D,senate,MN,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Tina Smith,D,senate,MN,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Tina Smith,D,senate,MN,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Todd Young,R,senate,IN,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Todd Young,R,senate,IN,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Todd Young,R,senate,IN,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Todd Young,R,senate,IN,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Tom Barrett,R,house,MI,07,ECONOMY_TAXES,9,7,6,2,0,1,8
Tom Barrett,R,house,MI,07,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Tom Barrett,R,house,MI,07,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Tom Barrett,R,house,MI,07,HEALTH_SOCIAL,4,1,1,0,3,0,3
Tom Barrett,R,house,MI,07,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Tom Barrett,R,house,MI,07,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Tom Barrett,R,house,MI,07,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tom Cole,R,house,OK,04,ECONOMY_TAXES,9,7,7,2,0,0,8
Tom Cole,R,house,OK,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Tom Cole,R,house,OK,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Tom Cole,R,house,OK,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Tom Cole,R,house,OK,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Tom Cole,R,house,OK,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Tom Cole,R,house,OK,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tom Cotton,R,senate,AR,Statewide,ECONOMY_TAXES,4,4,3,0,0,1,3
Tom Cotton,R,senate,AR,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Tom Cotton,R,senate,AR,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Tom Cotton,R,senate,AR,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Tom Emmer,R,house,MN,06,ECONOMY_TAXES,9,7,7,2,0,0,8
Tom Emmer,R,house,MN,06,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Tom Emmer,R,house,MN,06,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Tom Emmer,R,house,MN,06,HEALTH_SOCIAL,4,1,1,0,3,0,3
Tom Emmer,R,house,MN,06,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Tom Emmer,R,house,MN,06,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Tom Emmer,R,house,MN,06,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tom McClintock,R,house,CA,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Tom McClintock,R,house,CA,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Tom McClintock,R,house,CA,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Tom McClintock,R,house,CA,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Tom McClintock,R,house,CA,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Tom McClintock,R,house,CA,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Tom McClintock,R,house,CA,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tommy Tuberville,R,senate,AL,Statewide,ECONOMY_TAXES,4,4,4,0,0,0,3
Tommy Tuberville,R,senate,AL,Statewide,INFRASTRUCTURE_TECH_TRANSPORT,7,1,1,6,0,0,2
Tommy Tuberville,R,senate,AL,Statewide,JUSTICE_PUBLIC_SAFETY,1,1,1,0,0,0,1
Tommy Tuberville,R,senate,AL,Statewide,NATIONAL_SECURITY_FOREIGN,4,4,4,0,0,0,1
Tony Gonzales,R,house,TX,23,ECONOMY_TAXES,9,7,7,2,0,0,8
Tony Gonzales,R,house,TX,23,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Tony Gonzales,R,house,TX,23,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Tony Gonzales,R,house,TX,23,HEALTH_SOCIAL,4,1,1,0,3,0,3
Tony Gonzales,R,house,TX,23,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Tony Gonzales,R,house,TX,23,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Tony Gonzales,R,house,TX,23,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tony Wied,R,house,WI,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Tony Wied,R,house,WI,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Tony Wied,R,house,WI,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Tony Wied,R,house,WI,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Tony Wied,R,house,WI,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Tony Wied,R,house,WI,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Tony Wied,R,house,WI,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Tracey Mann,R,house,KS,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Tracey Mann,R,house,KS,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Tracey Mann,R,house,KS,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Tracey Mann,R,house,KS,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Tracey Mann,R,house,KS,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Tracey Mann,R,house,KS,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Tracey Mann,R,house,KS,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Trent Kelly,R,house,MS,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Trent Kelly,R,house,MS,01,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Trent Kelly,R,house,MS,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Trent Kelly,R,house,MS,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Trent Kelly,R,house,MS,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Trent Kelly,R,house,MS,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Trent Kelly,R,house,MS,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Troy A. Carter,D,house,LA,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Troy A. Carter,D,house,LA,02,EDUCATION_WORKFORCE,6,3,3,0,3,1,5
Troy A. Carter,D,house,LA,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Troy A. Carter,D,house,LA,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Troy A. Carter,D,house,LA,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Troy A. Carter,D,house,LA,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Troy A. Carter,D,house,LA,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Troy Balderson,R,house,OH,12,ECONOMY_TAXES,9,7,6,2,0,1,8
Troy Balderson,R,house,OH,12,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Troy Balderson,R,house,OH,12,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Troy Balderson,R,house,OH,12,HEALTH_SOCIAL,4,1,1,0,3,0,3
Troy Balderson,R,house,OH,12,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Troy Balderson,R,house,OH,12,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Troy Balderson,R,house,OH,12,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Troy Downing,R,house,MT,02,ECONOMY_TAXES,9,7,7,2,0,0,8
Troy Downing,R,house,MT,02,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Troy Downing,R,house,MT,02,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Troy Downing,R,house,MT,02,HEALTH_SOCIAL,4,1,1,0,3,0,3
Troy Downing,R,house,MT,02,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Troy Downing,R,house,MT,02,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Troy Downing,R,house,MT,02,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Troy E. Nehls,R,house,TX,22,ECONOMY_TAXES,9,7,6,2,0,1,8
Troy E. Nehls,R,house,TX,22,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Troy E. Nehls,R,house,TX,22,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Troy E. Nehls,R,house,TX,22,HEALTH_SOCIAL,4,1,1,0,3,1,3
Troy E. Nehls,R,house,TX,22,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Troy E. Nehls,R,house,TX,22,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Troy E. Nehls,R,house,TX,22,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,2,5
Turner (TX),D,house,TX,00,ECONOMY_TAXES,1,1,1,0,0,0,1
Turner (TX),D,house,TX,00,ENVIRONMENT_ENERGY,2,0,0,0,2,0,1
Turner (TX),D,house,TX,00,JUSTICE_PUBLIC_SAFETY,2,1,1,1,0,0,2
Val T. Hoyle,D,house,OR,04,ECONOMY_TAXES,9,7,6,2,0,1,8
Val T. Hoyle,D,house,OR,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Val T. Hoyle,D,house,OR,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Val T. Hoyle,D,house,OR,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Val T. Hoyle,D,house,OR,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Val T. Hoyle,D,house,OR,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Val T. Hoyle,D,house,OR,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Valerie P. Foushee,D,house,NC,04,ECONOMY_TAXES,9,7,6,2,0,1,8
Valerie P. Foushee,D,house,NC,04,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Valerie P. Foushee,D,house,NC,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Valerie P. Foushee,D,house,NC,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
Valerie P. Foushee,D,house,NC,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Valerie P. Foushee,D,house,NC,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Valerie P. Foushee,D,house,NC,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Vern Buchanan,R,house,FL,16,ECONOMY_TAXES,9,7,5,2,0,2,8
Vern Buchanan,R,house,FL,16,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Vern Buchanan,R,house,FL,16,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Vern Buchanan,R,house,FL,16,HEALTH_SOCIAL,4,1,1,0,3,0,3
Vern Buchanan,R,house,FL,16,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Vern Buchanan,R,house,FL,16,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,3,7
Vern Buchanan,R,house,FL,16,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Veronica Escobar,D,house,TX,16,ECONOMY_TAXES,9,7,7,2,0,0,8
Veronica Escobar,D,house,TX,16,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Veronica Escobar,D,house,TX,16,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Veronica Escobar,D,house,TX,16,HEALTH_SOCIAL,4,1,1,0,3,0,3
Veronica Escobar,D,house,TX,16,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Veronica Escobar,D,house,TX,16,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Veronica Escobar,D,house,TX,16,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Vicente Gonzalez,D,house,TX,34,ECONOMY_TAXES,9,7,7,2,0,0,8
Vicente Gonzalez,D,house,TX,34,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Vicente Gonzalez,D,house,TX,34,ENVIRONMENT_ENERGY,3,1,1,0,2,1,2
Vicente Gonzalez,D,house,TX,34,HEALTH_SOCIAL,4,1,1,0,3,0,3
Vicente Gonzalez,D,house,TX,34,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Vicente Gonzalez,D,house,TX,34,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Vicente Gonzalez,D,house,TX,34,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Victoria Spartz,R,house,IN,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Victoria Spartz,R,house,IN,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Victoria Spartz,R,house,IN,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Victoria Spartz,R,house,IN,05,HEALTH_SOCIAL,4,1,1,0,3,1,3
Victoria Spartz,R,house,IN,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Victoria Spartz,R,house,IN,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Victoria Spartz,R,house,IN,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Vince Fong,R,house,CA,20,ECONOMY_TAXES,9,7,7,2,0,0,8
Vince Fong,R,house,CA,20,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Vince Fong,R,house,CA,20,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Vince Fong,R,house,CA,20,HEALTH_SOCIAL,4,1,1,0,3,0,3
Vince Fong,R,house,CA,20,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Vince Fong,R,house,CA,20,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Vince Fong,R,house,CA,20,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Virginia Foxx,R,house,NC,05,ECONOMY_TAXES,9,7,7,2,0,0,8
Virginia Foxx,R,house,NC,05,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Virginia Foxx,R,house,NC,05,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Virginia Foxx,R,house,NC,05,HEALTH_SOCIAL,4,1,1,0,3,0,3
Virginia Foxx,R,house,NC,05,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Virginia Foxx,R,house,NC,05,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Virginia Foxx,R,house,NC,05,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
W. Gregory Steube,R,house,FL,17,ECONOMY_TAXES,9,7,7,2,0,0,8
W. Gregory Steube,R,house,FL,17,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
W. Gregory Steube,R,house,FL,17,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
W. Gregory Steube,R,house,FL,17,HEALTH_SOCIAL,4,1,1,0,3,0,3
W. Gregory Steube,R,house,FL,17,IMMIGRATION_BORDER,1,1,1,0,0,0,1
W. Gregory Steube,R,house,FL,17,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
W. Gregory Steube,R,house,FL,17,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Warren Davidson,R,house,OH,08,ECONOMY_TAXES,9,7,7,2,0,0,8
Warren Davidson,R,house,OH,08,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Warren Davidson,R,house,OH,08,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Warren Davidson,R,house,OH,08,HEALTH_SOCIAL,4,1,1,0,3,0,3
Warren Davidson,R,house,OH,08,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Warren Davidson,R,house,OH,08,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Warren Davidson,R,house,OH,08,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Wesley Bell,D,house,MO,01,ECONOMY_TAXES,9,7,7,2,0,0,8
Wesley Bell,D,house,MO,01,EDUCATION_WORKFORCE,6,3,3,0,3,2,5
Wesley Bell,D,house,MO,01,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Wesley Bell,D,house,MO,01,HEALTH_SOCIAL,4,1,1,0,3,0,3
Wesley Bell,D,house,MO,01,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Wesley Bell,D,house,MO,01,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Wesley Bell,D,house,MO,01,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Wesley Hunt,R,house,TX,38,ECONOMY_TAXES,9,7,7,2,0,0,8
Wesley Hunt,R,house,TX,38,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Wesley Hunt,R,house,TX,38,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Wesley Hunt,R,house,TX,38,HEALTH_SOCIAL,4,1,0,0,3,1,3
Wesley Hunt,R,house,TX,38,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Wesley Hunt,R,house,TX,38,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Wesley Hunt,R,house,TX,38,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
William R. Keating,D,house,MA,09,ECONOMY_TAXES,9,7,7,2,0,0,8
William R. Keating,D,house,MA,09,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
William R. Keating,D,house,MA,09,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
William R. Keating,D,house,MA,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
William R. Keating,D,house,MA,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
William R. Keating,D,house,MA,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
William R. Keating,D,house,MA,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
William R. Timmons IV,R,house,SC,04,ECONOMY_TAXES,9,7,7,2,0,0,8
William R. Timmons IV,R,house,SC,04,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
William R. Timmons IV,R,house,SC,04,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
William R. Timmons IV,R,house,SC,04,HEALTH_SOCIAL,4,1,1,0,3,0,3
William R. Timmons IV,R,house,SC,04,IMMIGRATION_BORDER,1,1,1,0,0,0,1
William R. Timmons IV,R,house,SC,04,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
William R. Timmons IV,R,house,SC,04,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Yassamin Ansari,D,house,AZ,03,ECONOMY_TAXES,9,7,6,2,0,1,8
Yassamin Ansari,D,house,AZ,03,EDUCATION_WORKFORCE,6,3,2,0,3,1,5
Yassamin Ansari,D,house,AZ,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Yassamin Ansari,D,house,AZ,03,HEALTH_SOCIAL,4,1,1,0,3,0,3
Yassamin Ansari,D,house,AZ,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Yassamin Ansari,D,house,AZ,03,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Yassamin Ansari,D,house,AZ,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Young Kim,R,house,CA,40,ECONOMY_TAXES,9,7,7,2,0,0,8
Young Kim,R,house,CA,40,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Young Kim,R,house,CA,40,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Young Kim,R,house,CA,40,HEALTH_SOCIAL,4,1,1,0,3,0,3
Young Kim,R,house,CA,40,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Young Kim,R,house,CA,40,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Young Kim,R,house,CA,40,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Yvette D. Clarke,D,house,NY,09,ECONOMY_TAXES,9,7,6,2,0,1,8
Yvette D. Clarke,D,house,NY,09,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Yvette D. Clarke,D,house,NY,09,ENVIRONMENT_ENERGY,3,1,0,0,2,1,2
Yvette D. Clarke,D,house,NY,09,HEALTH_SOCIAL,4,1,1,0,3,0,3
Yvette D. Clarke,D,house,NY,09,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Yvette D. Clarke,D,house,NY,09,JUSTICE_PUBLIC_SAFETY,13,6,6,1,6,0,7
Yvette D. Clarke,D,house,NY,09,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
Zachary Nunn,R,house,IA,03,ECONOMY_TAXES,9,7,7,2,0,0,8
Zachary Nunn,R,house,IA,03,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Zachary Nunn,R,house,IA,03,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Zachary Nunn,R,house,IA,03,HEALTH_SOCIAL,4,1,1,0,3,2,3
Zachary Nunn,R,house,IA,03,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Zachary Nunn,R,house,IA,03,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,2,7
Zachary Nunn,R,house,IA,03,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,1,5
Zoe Lofgren,D,house,CA,18,ECONOMY_TAXES,9,7,7,2,0,0,8
Zoe Lofgren,D,house,CA,18,EDUCATION_WORKFORCE,6,3,3,0,3,0,5
Zoe Lofgren,D,house,CA,18,ENVIRONMENT_ENERGY,3,1,1,0,2,0,2
Zoe Lofgren,D,house,CA,18,HEALTH_SOCIAL,4,1,1,0,3,0,3
Zoe Lofgren,D,house,CA,18,IMMIGRATION_BORDER,1,1,1,0,0,0,1
Zoe Lofgren,D,house,CA,18,JUSTICE_PUBLIC_SAFETY,13,6,4,1,6,2,7
Zoe Lofgren,D,house,CA,18,NATIONAL_SECURITY_FOREIGN,22,2,2,3,17,0,5
```

## 2. Source-Grounding Readiness

Interpreted rows audited: 10,084.

| Field | Populated interpreted rows | Share | Readiness |
|---|---:|---:|---|
| source_url | 10,084/10,084 | 100.0% | strong |
| source_basis | 10,084/10,084 | 100.0% | strong |
| context_source_list (available vote-context source list) | 10,084/10,084 | 100.0% | strong |
| final_result | 10,084/10,084 | 100.0% | strong |
| vote_margin | 10,084/10,084 | 100.0% | strong |
| party_vote_totals | 10,084/10,084 | 100.0% | strong |
| member_voted_with_party_majority | 9,795/10,084 | 97.1% | strong |
| member_voted_with_winning_side | 9,707/10,084 | 96.3% | strong |
| what_happened | 3,027/10,084 | 30.0% | weak |
| why_it_mattered | 3,027/10,084 | 30.0% | weak |
| what_not_to_infer | 3,027/10,084 | 30.0% | weak |
| policy_effect | 10,084/10,084 | 100.0% | strong |
| issue_facet | 10,084/10,084 | 100.0% | strong |

Notes:
- `interpretation_source_list` is not currently a separate response/database field in the evidence rows audited. `context_source_list` is present for vote-context provenance, and `source_basis` is present for interpreted records.
- The weakest source-grounded public fields are `what_happened`, `why_it_mattered`, and `what_not_to_infer`, each populated on only 30.0% of interpreted rows. This explains why generic fallback cards still repeat older summary/policy-effect text outside the gold slices.
- Vote-context fields are strong overall: final result, margin, party totals, and context source list are complete for interpreted rows; member-party/outcome booleans are present on roughly 96-97%.

## 3. Overview Readiness

Current generic overview generation is structurally usable but not broadly public-ready.

- It now avoids wrong-domain labels for Justice/Public Safety and uses shared domain labels rather than raw domain codes.
- Sample rendered non-Economy overviews did not show `stored vote context`, `for-side`, `against-side`, `leans Nay`, or `plus other reviewed measures`.
- Economy & Taxes intentionally still uses `concrete fiscal questions`; that phrase is acceptable only in Economy & Taxes.
- Non-gold domains often fall back to raw `policy_effect` as concrete-question text. That is source-grounded, but it can be too long and too close to audit language.
- The PR #3 fix prevents raw limited-context facet strings from appearing in the overview caveat for non-Economy domains, but mapped measure labels are still sparse outside Economy and Justice.

## 4. Measure-Group Readiness

### Current Issue Facets by Domain

**Economy & Taxes**
- `abortion` (200 rows): unmapped
- `administrative_law_and_regulatory_procedures` (100 rows): unmapped
- `appropriations_amendment` (438 rows): mapped
- `budget_reconciliation_and_debt_limit` (866 rows): mapped
- `conference_instruction` (432 rows): mapped
- `congressional_oversight` (100 rows): unmapped
- `government_funding_and_shutdown` (433 rows): mapped
- `military_construction_and_va_appropriations` (432 rows): mapped
- `small_business_loan_eligibility` (432 rows): mapped
- `small_business_regulation` (432 rows): mapped
- `temporary_government_funding` (432 rows): mapped

**Education & Workforce**
- `federal_employee_collective_bargaining` (433 rows): unmapped
- `floor_rule_for_multiple_bills` (864 rows): unmapped
- `house_censure_and_committee_assignment` (432 rows): unmapped
- `school_foreign_funding_and_contract_restrictions` (432 rows): unmapped
- `school_foreign_influence_parent_notifications` (433 rows): unmapped

**Environment & Energy**
- `floor_rule_for_energy_and_budget_measures` (866 rows): unmapped
- `natural_gas_pipeline_and_lng_review_coordination` (433 rows): unmapped

**Health & Social Services**
- `floor_rule_for_multiple_bills` (866 rows): unmapped
- `health_insurance_premiums` (433 rows): unmapped
- `medicaid_payment_rules_for_minor_health_procedures` (433 rows): unmapped

**Immigration & Border Policy**
- `dc_immigration_information_sharing` (432 rows): unmapped

**Infrastructure, Tech & Transportation**
- `floor_procedure_on_hydrogen_vehicle_rule` (600 rows): unmapped
- `hydrogen_vehicle_safety_standards` (100 rows): unmapped

**Justice & Public Safety**
- `administrative_law_and_regulatory_procedures` (532 rows): unmapped
- `dc_police_pursuit_policy` (432 rows): mapped
- `dc_policing_reform_repeal` (433 rows): mapped
- `federal_law_enforcement_equipment` (433 rows): mapped
- `fentanyl_scheduling_and_penalties` (865 rows): mapped
- `house_of_representatives` (2,593 rows): unmapped
- `law_enforcement_safety_reporting` (433 rows): mapped

**National Security & Foreign Policy**
- `Defense authorization` (432 rows): unmapped
- `Defense authorization amendment` (7,429 rows): unmapped
- `House floor procedure` (861 rows): unmapped
- `Motion to commit` (433 rows): unmapped
- `Veterans cemetery administration` (433 rows): unmapped
- `foreign_military_sales` (400 rows): unmapped

### Facets Needing Cleanup

- Economy & Taxes / `abortion` (200 rows): needs voter-facing label.
- Economy & Taxes / `administrative_law_and_regulatory_procedures` (100 rows): raw snake_case.
- Economy & Taxes / `congressional_oversight` (100 rows): raw snake_case.
- Education & Workforce / `federal_employee_collective_bargaining` (433 rows): raw snake_case.
- Education & Workforce / `floor_rule_for_multiple_bills` (864 rows): raw snake_case, procedural/vague.
- Education & Workforce / `house_censure_and_committee_assignment` (432 rows): raw snake_case.
- Education & Workforce / `school_foreign_funding_and_contract_restrictions` (432 rows): raw snake_case, long.
- Education & Workforce / `school_foreign_influence_parent_notifications` (433 rows): raw snake_case.
- Environment & Energy / `floor_rule_for_energy_and_budget_measures` (866 rows): raw snake_case, procedural/vague.
- Environment & Energy / `natural_gas_pipeline_and_lng_review_coordination` (433 rows): raw snake_case, long.
- Health & Social Services / `floor_rule_for_multiple_bills` (866 rows): raw snake_case, procedural/vague.
- Health & Social Services / `health_insurance_premiums` (433 rows): raw snake_case.
- Health & Social Services / `medicaid_payment_rules_for_minor_health_procedures` (433 rows): raw snake_case, long.
- Immigration & Border Policy / `dc_immigration_information_sharing` (432 rows): raw snake_case.
- Infrastructure, Tech & Transportation / `floor_procedure_on_hydrogen_vehicle_rule` (600 rows): raw snake_case, procedural/vague.
- Infrastructure, Tech & Transportation / `hydrogen_vehicle_safety_standards` (100 rows): raw snake_case.
- Justice & Public Safety / `administrative_law_and_regulatory_procedures` (532 rows): raw snake_case.
- Justice & Public Safety / `house_of_representatives` (2,593 rows): raw snake_case, procedural/vague.
- National Security & Foreign Policy / `Defense authorization` (432 rows): needs voter-facing label.
- National Security & Foreign Policy / `Defense authorization amendment` (7,429 rows): needs voter-facing label.
- National Security & Foreign Policy / `House floor procedure` (861 rows): procedural/vague.
- National Security & Foreign Policy / `Motion to commit` (433 rows): needs voter-facing label.
- National Security & Foreign Policy / `Veterans cemetery administration` (433 rows): needs voter-facing label.
- National Security & Foreign Policy / `foreign_military_sales` (400 rows): raw snake_case.

## 5. Card-Summary Readiness

- Rows with custom Valerie/Economy roll-specific card summaries or limited-row summaries: 9.
- Rows using generic fallback summary behavior: 26,754.
- No broad curated Justice roll-number system exists; Justice polish is facet-based in the generic helper for two facets only.

### Five Strong Generic Examples

- Valerie P. Foushee / Justice & Public Safety / Roll 130: Nay. The House passed a bill directing GSA to create a process for federal law-enforcement officers to buy retired agency-issued firearms. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.
- Valerie P. Foushee / Justice & Public Safety / Roll 32: Yea. The packet identifies an amendment vote, but the cached bill summary describes the underlying bill rather than the exact amendment change. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.
- Valerie P. Foushee / Education & Workforce / Roll 308: Nay. This was a previous-question vote tied to a floor rule for multiple education and small-business bills, not a final vote on any single policy. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.
- Valerie P. Foushee / Health & Social Services / Roll 344: Nay. This was a floor-rule vote for considering multiple bills, not a final vote on the health, education, or environmental policies named in the rule. This row remains visible but is not counted in the summarized vote pattern because the available source text does not explain the practical policy effect.
- Valerie P. Foushee / Justice & Public Safety / Roll 33: Nay. The House passed the HALT Fentanyl Act, which would permanently place fentanyl-related substances as a class into Schedule I and apply fentanyl-analogue penalty thresholds, while creating or revising research-registration paths. Foushee voted against passing the bill, matching most Democrats. The bill passed the House.

### Five Weak Generic Examples

- Justice & Public Safety / law_enforcement_safety_reporting: still falls back to a long generic summary that repeats the bill title, what happened, why it mattered, and policy effect before the vote-context sentence.
- Justice & Public Safety / dc_police_pursuit_policy: generic summary is accurate but dense, with repeated D.C. pursuit-rule details and no compact facet-specific sentence yet.
- National Security & Foreign Policy / Defense authorization amendment: 7,429 rows are insufficient-evidence; card text is procedural/limited rather than a useful public read.
- National Security & Foreign Policy / House floor procedure: raw facet label and procedural wording are likely too audit-heavy for default scale.
- Economy & Taxes / non-Foushee rows on the gold-slice rolls: generic summaries are good enough mechanically but lack the exact curated clarity approved for Valerie.

Common failure modes:
- Repetition between `what_happened`, `why_it_mattered`, and `policy_effect`.
- Vague or procedural facet labels such as `house_of_representatives`, `Defense authorization amendment`, and floor-rule labels.
- Missing compact action templates for many interpreted non-gold facets.
- Long card summaries when older `plain_english_summary` and `policy_effect` are both surfaced.
- Generic fallback is mechanically safer than before, but still lacks the polished voter-facing cadence of the gold slice.

## 6. UI Scaling Risk

- 10+ row sections: 868.
- 20+ row sections: 430.
- 5+ measure-group/facet sections: 1,724.
- Sections with 5+ limited/ambiguous rows: 968.
- Sections with repeated roll calls for the same bill/description: 2,600.

Progressive disclosure helps, but it is not enough for broad scale. Before broad rollout, high-volume sections likely need grouped measure cards or bill-level grouping above individual roll calls. National Security & Foreign Policy is the clearest risk: many slices have 20+ rows and are dominated by defense-authorization amendments or floor procedure.

## 7. Recommended Scaling Plan

### Safe to Scale Now

- Additional House Economy & Taxes slices using the existing mapped Economy facets, provided the overview is framed as a slice-level read and not a full ideology score.
- Justice/Public Safety slices with the already mapped facets, where counted interpreted rows are at least 3 and limited rows remain caveated.

### Needs Facet-Label Cleanup First

- Education & Workforce, Health & Social Services, Environment & Energy, Infrastructure/Tech/Transportation, Immigration/Border, and National Security/Foreign Policy. Each has unmapped or procedural facets that would currently read too raw in measure groups.

### Needs Source Enrichment First

- National Security & Foreign Policy defense authorization amendment slices: high volume, low interpreted share, and many insufficient-evidence rows.
- Infrastructure/Tech/Transportation floor-procedure rows and any sections where rules/procedure dominate the issue slice.

### Needs Generic Card-Summary Improvements First

- Justice/Public Safety remaining interpreted facets beyond fentanyl scheduling and federal law-enforcement equipment.
- Education/Workforce, Health/Social, Environment/Energy, and Immigration/Border interpreted facets that currently rely on older summary/policy-effect fallbacks.

### Should Remain Hidden/Limited Due to Insufficient Evidence

- Any official/domain slice with fewer than 3 counted interpreted Yes/No rows.
- Any 10+ row slice where 60% or more rows are ambiguous/insufficient unless the public UI strongly groups and caveats the evidence.

## 8. Recommended Next PRs

### PR 1: Facet Label Coverage Audit and Mapping

- Goal: add reviewed voter-facing labels for the highest-volume unmapped facets without changing interpretation coverage.
- Scope: `frontend/lib/issueOverview.mjs`, `frontend/lib/issueOverview.test.mjs`, docs review packet.
- Acceptance criteria: top unmapped facets no longer render raw snake_case/title-case audit labels; Economy and Justice approved copy remains unchanged.
- Risk level: low to medium.
- Change type: code + tests + docs.

### PR 2: Generic Card Summary Templates for Top Non-Gold Facets

- Goal: reduce repetition and dense fallback summaries for the most common interpreted non-gold facets.
- Scope: `frontend/lib/voteCardSummary.mjs`, tests, one review packet with rendered examples.
- Acceptance criteria: five selected high-volume facets have concise summaries with vote, practical action, vote meaning, and party/outcome context; no roll-number curated expansion.
- Risk level: medium.
- Change type: code + tests + docs.

### PR 3: Measure-Grouped Evidence Section Prototype

- Goal: determine whether high-volume sections need grouped measure cards above individual evidence rows.
- Scope: review-only prototype or behind-flag frontend component experiment; do not broad-rollout.
- Acceptance criteria: compare a 20+ row National Security slice and a 13-row Justice slice in text/screenshot packet; source links remain accessible; limited rows stay visible but grouped.
- Risk level: medium to high.
- Change type: review packet first; code only if explicitly approved.

## 9. Verification

Commands run:

```text
git checkout -b codex/interpretation-scale-readiness-audit
PYTHONPATH=backend python -  # read-only DB aggregate scripts shown in Codex tool calls
node helper via node_repl  # rendered overview/card examples from frontend helpers
node --test frontend/lib/issueOverview.test.mjs
Result: pass, 6 tests passing.
```

No production code was changed. No backend/frontend server was started. No broad interpretation rollout was performed.
