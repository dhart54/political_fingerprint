-- Rollback for 118th Congress Evidence Expansion classifications.
-- Scope: exact roll_call_ids selected by evidence_118_expansion dry-run.
BEGIN;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1756;

UPDATE vote_classifications
SET
    is_eligible = TRUE,
    eligibility_reason = 'policy_vote',
    primary_domain = 'ECONOMY_TAXES'::issue_domain,
    score_breakdown = '{"ECONOMY_TAXES": {"keyword_match": 4}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1757;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1763;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1768;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1829;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"HEALTH_SOCIAL": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1830;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1831;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1832;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1847;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1848;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1849;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1852;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1856;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1865;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1868;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1875;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1877;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1881;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1897;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1898;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1913;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1914;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1916;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1925;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1926;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1933;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1940;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1941;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1942;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"ECONOMY_TAXES": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1943;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1954;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1959;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1961;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1964;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1966;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1984;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2009;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"EDUCATION_WORKFORCE": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2018;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2022;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2024;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2026;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2027;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2028;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2059;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2060;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2070;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2071;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"EDUCATION_WORKFORCE": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2072;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2096;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2115;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2117;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2124;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2127;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2132;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2139;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2231;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2232;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2233;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2234;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2235;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2236;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2237;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2238;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2239;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2244;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2246;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2251;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2283;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2284;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2285;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2286;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2301;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2324;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2325;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2331;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2345;

UPDATE vote_classifications
SET
    is_eligible = TRUE,
    eligibility_reason = 'policy_vote',
    primary_domain = 'EDUCATION_WORKFORCE'::issue_domain,
    score_breakdown = '{"HEALTH_SOCIAL": {"keyword_match": 2}, "EDUCATION_WORKFORCE": {"keyword_match": 4}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2369;

UPDATE vote_classifications
SET
    is_eligible = TRUE,
    eligibility_reason = 'policy_vote',
    primary_domain = 'EDUCATION_WORKFORCE'::issue_domain,
    score_breakdown = '{"HEALTH_SOCIAL": {"keyword_match": 2}, "EDUCATION_WORKFORCE": {"keyword_match": 4}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2370;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2381;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2399;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2400;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2410;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2412;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2413;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2418;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2428;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2436;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"HEALTH_SOCIAL": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2441;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2444;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2488;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2515;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2516;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2519;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2522;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2523;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2534;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2545;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"HEALTH_SOCIAL": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2546;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2550;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2559;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2561;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2564;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2573;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2591;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2593;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2594;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2597;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2598;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2599;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2600;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2601;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2602;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"ECONOMY_TAXES": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2603;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2611;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2625;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2626;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2627;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2628;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2629;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2632;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2633;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2636;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2638;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2644;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2645;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2646;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2647;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2649;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2660;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2662;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2667;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2672;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2673;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2682;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2689;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2690;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2691;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2707;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2709;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2713;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2721;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2722;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2723;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2724;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2725;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"INFRASTRUCTURE_TECH_TRANSPORT": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2732;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2736;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2756;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2757;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2758;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2784;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2785;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2787;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2836;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2837;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2838;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2839;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2840;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2841;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2857;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2858;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2860;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2897;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2898;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2906;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2916;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2917;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2918;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2919;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2927;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2934;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2935;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2938;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"INFRASTRUCTURE_TECH_TRANSPORT": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2939;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2942;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2949;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2951;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2954;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2957;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2958;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2962;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2965;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2966;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2979;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"ECONOMY_TAXES": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2981;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2982;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'procedural_vote',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3014;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3025;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3033;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3038;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3039;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3040;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3043;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3048;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3054;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3070;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3076;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 3103;

COMMIT;
