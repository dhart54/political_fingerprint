# Federal Contact Metadata Workflow

This workflow expands current-official contact metadata without turning the contact layer into a persuasion or outreach automation system.

## Source Priority

Use official federal sources first:

1. Senate contact XML
   - URL: `https://www.senate.gov/general/contact_information/senators_cfm.xml`
   - Existing fetch helper: `python -m app.etl.fetch_sources senate-members --contact-only --overwrite`
   - Expected fields: senator name, state, party, official website or contact URL when present, Washington phone, office information.
   - Use for: senator official website, contact path, phone, and source provenance.

2. House MemberData XML
   - URL: `https://clerk.house.gov/xml/lists/MemberData.xml`
   - Existing fetch helper: `python -m app.etl.fetch_sources house-members --overwrite`
   - Expected fields: member identity, state, district, party, Bioguide ID, official website, office and phone fields when present.
   - Use for: House identity matching, official website, phone, and source provenance.

3. Official member websites
   - Use only when the official XML source does not expose a durable contact-form URL.
   - Contact-form URLs should be reviewed before import, because member sites use inconsistent paths and form vendors.
   - Do not scrape message forms, submit forms, or infer constituent eligibility rules.

Avoid third-party directories for production imports unless they are only used as a review hint and the final stored source is still an official House, Senate, or member-office URL.

## Cost, Access, And Legal Review

Current source posture:

- Cost: no paid vendor is required for the official House and Senate directory files used by this workflow.
- Access: no API key is required for the House MemberData XML or Senate contact XML files.
- Freshness: the files should be treated as current official directory snapshots, not historical records.
- Source availability:
  - Senate.gov publishes an XML sources page that lists the current senators contact list and current senators information as XML-available resources.
  - The Senate public contact guidance also tells users they can download the senators contact list XML and open it in a spreadsheet.
  - XML.house.gov publishes House Member Data XML resources, including a schema, user guide, and sample.
- License/legal posture:
  - The official pages confirm public XML availability, but they do not by themselves grant permission to scrape, submit, or automate member-office contact forms.
  - Store the source URL, source type, and retrieval date for every imported record.
  - Before broad scheduled production imports, do one human review of each source page for any usage notices, robots/access guidance, or changed publication terms.
  - If a chamber or member site publishes stricter terms, the stricter source-specific rule controls this workflow.

Do not treat this workflow as permission to scrape, submit, or automate member-office web forms. It only supports storing official contact paths and metadata for user-directed contact.

## Stored Fields

The importer currently accepts:

- `bioguide_id`
- `official_website_url`
- `contact_form_url`
- `phone`
- `source_url`
- `source_type`
- `source_retrieved_at`

Allowed `source_type` values remain:

- `official_house_website`
- `official_senate_website`

If a source provides a phone number or official website but not a contact form, import the available official fields and leave `contact_form_url` empty. The frontend must show the missing contact path as unavailable rather than guessing.

## Update Cadence

Recommended cadence:

- Monthly during normal periods.
- Weekly after a new Congress is seated, special elections, appointments, resignations, or known office website transitions.
- Before staging or production demos that rely on a newly added ZIP path.

Store the retrieval date from the actual review/import date, not from a previous cached file.

## Review And Import Steps

1. Fetch current official source files into `backend/data_sources`.
2. Build or update a reviewed JSON seed in `docs/legislator_contacts/`.
   - Current reviewed seeds:
     - `nc_federal_contacts_seed.json`
     - `loaded_zip_federal_contacts_seed.json`
3. Verify each record is keyed by Bioguide ID and has at least one contact field.
4. Review source pages for changed publication or access caveats, especially before changing cadence from manual review to scheduled imports.
5. Run a dry-run parse:

```powershell
cd backend
python -m app.etl.legislator_contacts --input ..\docs\legislator_contacts\<seed>.json --dry-run
```

6. Import only after review:

```powershell
cd backend
python -m app.etl.legislator_contacts --input ..\docs\legislator_contacts\<seed>.json
```

7. Smoke-test representative contact endpoints for loaded and missing records.

## Failure Modes

- Official XML omits a contact form. Store the official website and phone only.
- Member websites change paths. Mark the retrieval date and update the reviewed seed.
- A Bioguide ID is missing from the local legislator table. The importer skips that row; update legislator ingestion before retrying.
- Source fields conflict. Prefer the chamber source for identity and phone, then use the member office site for contact-form URL after review.
- A contact URL leads to an external vendor form. Store it only if it is linked from the official member site or chamber contact source.

## Product Boundaries

Contact metadata is civic utility data. It must not affect:

- vote classification
- vote interpretation
- alignment labels
- issue evidence counts
- candidate evidence tiers
- race ranking or candidate comparison

The contact surface should continue to expose official paths and the evidence context the user selected. It should not generate message bodies, talking points, outreach campaigns, reminders, or newsletters until those needs are validated separately.
