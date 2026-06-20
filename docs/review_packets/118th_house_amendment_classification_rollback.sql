-- Rollback for 118th House amendment classifications.
-- Scope: exact preflight-approved roll_call_ids only.
BEGIN;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1899;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1900;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1901;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1902;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1904;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1905;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1907;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1908;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1911;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1912;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1950;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1951;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1952;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1953;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1955;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1956;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"JUSTICE_PUBLIC_SAFETY": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1958;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 1998;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2010;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2011;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2012;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2075;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2082;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2084;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2086;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2087;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2091;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2095;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2140;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2141;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2142;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2143;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2144;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2145;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2146;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2147;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2148;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2149;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2150;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2151;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2152;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2153;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2155;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2156;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2157;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2158;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2159;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2161;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2162;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2163;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2164;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2165;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2166;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2167;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2168;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2169;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2170;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2171;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2172;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2173;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2174;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2175;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2176;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2178;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2179;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2180;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2181;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2182;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2183;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2184;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2185;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2186;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2187;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2190;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2191;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2193;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2196;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2200;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2202;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2203;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2204;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2205;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2206;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2207;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2208;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2209;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2210;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2211;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2212;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2213;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2214;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2215;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2216;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2217;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2218;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2219;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2220;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2221;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2222;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2223;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2224;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2225;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2226;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2227;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2228;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2229;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2230;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2252;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2260;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2265;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2266;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2268;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2303;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2313;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2326;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2332;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2336;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2337;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2343;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2386;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2387;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2388;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2389;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2390;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2391;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2393;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2394;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2397;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2403;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2404;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2405;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2406;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2407;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2408;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2409;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2411;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2421;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2579;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2650;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2653;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2655;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"IMMIGRATION_BORDER": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2720;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"INFRASTRUCTURE_TECH_TRANSPORT": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2729;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"INFRASTRUCTURE_TECH_TRANSPORT": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2730;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"INFRASTRUCTURE_TECH_TRANSPORT": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2731;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2733;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2734;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2735;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"ECONOMY_TAXES": {"keyword_match": 2}, "NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2749;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"ECONOMY_TAXES": {"keyword_match": 2}, "NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2750;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2759;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2760;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2761;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2762;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2763;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2765;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2767;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2768;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2769;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2770;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2771;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2772;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2773;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2774;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2775;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2776;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2777;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2778;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2779;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2780;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2781;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2782;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2783;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2791;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2794;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2795;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2796;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2797;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2798;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2799;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2800;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2801;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2802;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2803;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2804;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2805;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2806;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2808;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2809;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2810;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2811;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2812;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2813;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2814;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2815;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2816;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2817;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2818;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2819;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2820;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2822;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2823;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2824;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2825;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2826;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2827;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2828;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2829;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2830;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2831;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2832;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2833;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{"NATIONAL_SECURITY_FOREIGN": {"keyword_match": 2}}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2835;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2873;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2874;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2875;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2876;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2878;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2881;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2882;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2883;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2884;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2889;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2892;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2893;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2902;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2912;

UPDATE vote_classifications
SET
    is_eligible = FALSE,
    eligibility_reason = 'low_classification_confidence',
    primary_domain = NULL,
    score_breakdown = '{}'::jsonb,
    classification_version = 'v1',
    updated_at = NOW()
WHERE roll_call_id = 2915;

COMMIT;
