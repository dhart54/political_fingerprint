"""Source-bound editorial definitions for the detached M3A-R1 V2 candidate batch.

The entries contain no party, benchmark, episode, synthesis, or public-conclusion
information.  Locators refer only to the governed M2 operative representations.
"""

from __future__ import annotations


def _d(
    meaning: str | None,
    provisions: tuple[tuple[str, str], ...],
    limits: tuple[tuple[str, str], ...] = (),
    *,
    confidence: str = "high",
    official: str | None = None,
) -> dict[str, object]:
    return {
        "meaning": meaning,
        "provisions": provisions,
        "limits": limits,
        "confidence": confidence,
        "official": official,
    }


ACTION_DEFINITIONS: dict[str, dict[str, object]] = {
    "house:119:1:6": _d(
        "The House choice was whether to pass H.R. 29, requiring federal detention and DHS detainers for certain inadmissible noncitizens connected to burglary, theft, larceny, or shoplifting offenses. It also would give State attorneys general standing to seek expedited injunctive relief over specified federal detention, release, parole, and visa actions.",
        (
            (
                "Require detention and DHS detainers for covered noncitizens connected to specified theft offenses.",
                "section 2",
            ),
            (
                "Create State attorney-general enforcement actions concerning specified immigration detention, release, parole, and visa duties.",
                "section 3",
            ),
        ),
        (
            (
                "State enforcement standing uses a claimed-harm threshold that includes financial harm over $100.",
                "section 3",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:23": _d(
        "The House choice was whether to pass the Senate version of the Laken Riley Act, requiring federal detention and DHS detainers for certain inadmissible noncitizens connected to burglary, theft, larceny, or shoplifting offenses. It also would give State attorneys general standing to seek expedited injunctive relief over specified federal detention, release, parole, and visa actions.",
        (
            (
                "Require detention and DHS detainers for covered noncitizens connected to specified theft offenses.",
                "section 2",
            ),
            (
                "Create State attorney-general enforcement actions concerning specified immigration detention, release, parole, and visa duties.",
                "section 3",
            ),
        ),
        (
            (
                "State enforcement standing uses a claimed-harm threshold that includes financial harm over $100.",
                "section 3",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:27": _d(
        "The House choice was whether to pass H.R. 21, requiring practitioners to provide a child born alive after an abortion or attempted abortion the same care as another child at the same gestational age, ensure immediate hospital admission when needed, and report known violations. The bill also would create criminal penalties and civil remedies while barring prosecution of the woman on whom the abortion was performed.",
        (
            (
                "Require equivalent professional care for a child born alive after an abortion or attempted abortion.",
                "section 3(a)",
            ),
            (
                "Require immediate hospital admission and mandatory reporting in specified circumstances.",
                "section 3(a)",
            ),
            (
                "Create criminal penalties and a civil action for violations.",
                "section 3(a)",
            ),
        ),
        (
            (
                "The woman on whom the abortion was performed may not be prosecuted under the new offense.",
                "section 3(a), bar to prosecution",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:32": _d(
        "The House choice was whether to amend H.R. 27 so its classwide fentanyl scheduling and related amendments would take effect only after the Health and Human Services Secretary and Attorney General jointly certified in the Federal Register that the Act would reduce overdose deaths.",
        (
            (
                "Condition the Act's effective operation on a joint overdose-reduction certification.",
                "governed Congressional Record pages 24-25",
            ),
        ),
        (
            (
                "The amendment addressed when the parent bill would take effect; it did not itself replace the parent bill's scheduling framework.",
                "governed Congressional Record pages 24-25",
            ),
        ),
        official="Trahan amendment requiring a joint overdose-reduction certification before H.R. 27 would take effect.",
    ),
    "house:119:1:33": _d(
        "The House choice was whether to pass H.R. 27, placing fentanyl-related substances in schedule I as a class, applying specified trafficking penalties, and establishing registration pathways and procedures for research involving schedule I substances.",
        (
            (
                "Place fentanyl-related substances in schedule I as a class.",
                "section 2",
            ),
            (
                "Create alternative and expedited registration procedures for specified schedule I research.",
                "section 3",
            ),
            (
                "Apply specified Controlled Substances Act penalties to fentanyl-related substances.",
                "section 6",
            ),
            (
                "Require implementing rules and address applicability.",
                "sections 5 and 7",
            ),
        ),
        (
            (
                "The class definition excludes substances specifically exempted or listed in another schedule.",
                "section 2",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:42": _d(
        "The House choice was whether to pass H.R. 35, creating a federal offense for intentionally fleeing specified pursuing officers by motor vehicle within 100 miles of the border, with penalties escalating when serious injury or death results. The bill also would impose specified immigration consequences and require annual Justice and Homeland Security reporting on enforcement of the offense.",
        (
            (
                "Create a federal offense for intentional motor-vehicle flight from specified pursuing officers within 100 miles of the border.",
                "section 2",
            ),
            (
                "Set a maximum two-year term generally, five-to-20 years for serious bodily injury, and 10 years to life when death results.",
                "section 2(b)",
            ),
            (
                "Make covered conduct a basis for inadmissibility, deportability, and ineligibility for immigration relief.",
                "section 3",
            ),
            (
                "Require annual reporting on charges, apprehensions, sought penalties, and imposed penalties.",
                "section 4",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:68": _d(
        "The House choice was whether to pass H.R. 1156, establishing a 10-year limitations period for specified criminal prosecutions and civil enforcement actions involving fraud in three pandemic unemployment programs. It also would rescind $5 million in unobligated administrative funding.",
        (
            (
                "Create a 10-year limitations period for covered pandemic unemployment fraud actions.",
                "section 2",
            ),
            (
                "Apply the period to Pandemic Unemployment Assistance, Federal Pandemic Unemployment Compensation, Mixed Earner Unemployment Compensation, and Pandemic Emergency Unemployment Compensation.",
                "section 2",
            ),
            ("Rescind $5 million in unobligated administrative balances.", "section 3"),
        ),
        (
            (
                "The extension does not revive an action whose prior limitations period expired before enactment.",
                "section 2 exceptions",
            ),
        ),
    ),
    "house:119:1:98": _d(
        "The House choice was whether to pass H.R. 1526, generally limiting federal district-court injunctions to the parties and represented nonparties in the case. A challenge brought by two or more States in different circuits would instead go to a randomly selected three-judge panel that could issue broader relief under specified considerations.",
        (
            (
                "Limit district-court injunctive relief to parties and represented nonparties in the case.",
                "section 2(a), new 28 U.S.C. 1370(a)",
            ),
            (
                "Create a three-judge-panel process for executive-action challenges brought by multiple States in different circuits.",
                "section 2(a), new 28 U.S.C. 1370(b)",
            ),
        ),
        (
            (
                "The three-judge panel may grant relief otherwise barred after considering justice, nonparty harm, and separation of powers.",
                "section 2(a), new 28 U.S.C. 1370(b)-(c)",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:128": _d(
        "The House choice was whether to pass H.R. 2243, expanding where qualified current and retired law-enforcement officers may carry concealed firearms, including specified school zones, publicly accessible transport property, National Park System units, and lower-security federal public facilities. It also would revise retired-officer qualification periods and documentation.",
        (
            (
                "Conform school-zone rules to LEOSA concealed-carry authority.",
                "section 2",
            ),
            (
                "Expand LEOSA preemption for specified National Park, transportation, and public-access property.",
                "section 3",
            ),
            (
                "Revise retired-officer firearm qualification standards and documentation.",
                "section 3",
            ),
            (
                "Permit qualified officers to carry in Facility Security Level I or II civilian public-access federal facilities.",
                "section 4",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:130": _d(
        "The House choice was whether to pass H.R. 2255, requiring a program that lets eligible current or retired federal law-enforcement officers buy qualifying surplus firearms issued to them. Purchases would be limited to a six-month window, officers in good standing, and salvage-value pricing.",
        (
            (
                "Require GSA to establish the retired-service-firearm purchase program within one year.",
                "section 2(a)",
            ),
        ),
        (
            (
                "A purchase must occur within six months after retirement of the firearm and the officer must be in good standing.",
                "section 2(b)",
            ),
            (
                "The firearm is sold at salvage value and specified machineguns are excluded.",
                "section 2(c)-(d)",
            ),
        ),
    ),
    "house:119:1:131": _d(
        "The House choice was whether to pass H.R. 2240, requiring the Attorney General to develop reports on violent attacks against officers and the systems used to collect attack data, on aggression against officers, and on officer mental-health and wellness programs and resources.",
        (
            (
                "Report on attacks against officers and development of the underlying reporting system and data.",
                "section 3",
            ),
            ("Report on aggression against law-enforcement officers.", "section 4"),
            (
                "Report on officer mental-health and wellness needs, programs, and resources.",
                "section 5",
            ),
        ),
    ),
    "house:119:1:162": _d(
        "The House choice was whether to pass H.R. 2096, restoring collective bargaining over discipline for D.C. law-enforcement officers and restoring the prior limitations rules for disciplinary claims against Metropolitan Police Department members and civilian employees.",
        (
            (
                "Restore collective bargaining over D.C. law-enforcement discipline.",
                "section 2(a)",
            ),
            (
                "Repeal the 2022 subtitle that changed limitations rules for disciplinary claims and revive the prior law.",
                "section 2(b)",
            ),
        ),
    ),
    "house:119:1:166": _d(
        "The House choice was whether to pass S. 331, permanently placing fentanyl-related substances in schedule I as a class and applying specified trafficking penalties. The bill also would establish alternative and expedited research-registration procedures, technical corrections, and implementing rules.",
        (
            (
                "Permanently place fentanyl-related substances in schedule I as a class.",
                "section 2",
            ),
            (
                "Create alternative and expedited registration pathways for schedule I research.",
                "section 3",
            ),
            ("Require implementing rules and technical corrections.", "sections 4-5"),
            (
                "Apply specified Controlled Substances Act and import-export penalties.",
                "section 6",
            ),
        ),
        (
            (
                "The class definition excludes substances specifically exempted or listed in another schedule.",
                "section 2",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:270": _d(
        "The House choice was whether to pass H.R. 4922, limiting D.C. youth-offender status to people under 18, removing authority to impose a sentence below a mandatory minimum under that statute, and requiring a monthly, downloadable public juvenile-crime statistics website. The website would use specified arrest and case measures while excluding personally identifiable information.",
        (
            (
                "Limit D.C. youth-offender status to people under 18 and make conforming changes.",
                "section 2(a)",
            ),
            (
                "Remove authority for a sentence below a mandatory-minimum term under the Youth Rehabilitation Act.",
                "section 2(b)",
            ),
            (
                "Require a monthly, archived, machine-readable public juvenile-crime statistics website.",
                "section 3",
            ),
        ),
        (
            (
                "The public website may not disclose a juvenile's personally identifiable information.",
                "section 3(a), new D.C. Code 16-2340a(e)",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:271": _d(
        "The House choice was whether to pass H.R. 5140, lowering from 16 to 14 the age at which specified D.C. minors may be excluded from Family Court jurisdiction and lowering related transfer thresholds to 14 for covered criminal proceedings.",
        (
            (
                "Lower the specified Family Court exclusion age from 16 to 14.",
                "section 1(a)",
            ),
            (
                "Lower specified transfer-to-criminal-proceeding ages to 14.",
                "section 1(b)",
            ),
        ),
        (
            (
                "The changes apply to offenses committed on or after enactment.",
                "section 1(c)",
            ),
        ),
    ),
    "house:119:1:274": _d(
        "The House choice was whether to pass H.R. 5125, terminating the D.C. Judicial Nomination Commission and removing its nomination-list role, while shifting specified chief-judge designation and judicial nomination functions to the President.",
        (
            ("Terminate the D.C. Judicial Nomination Commission.", "section 2(a)"),
            (
                "Remove the Commission's candidate-list role and assign specified chief-judge designation and nomination functions to the President.",
                "section 2(b)-(d)",
            ),
        ),
        (
            (
                "The changes apply to appointments made on or after enactment.",
                "section 2(e)",
            ),
        ),
    ),
    "house:119:1:275": _d(
        "The House choice was whether to pass H.R. 5143, replacing D.C. pursuit restrictions with authority for an officer to pursue a fleeing motor-vehicle suspect unless the pursuit presents an unacceptable risk, would be futile, or another means would be more effective or faster. It also would require a Justice Department evaluation and report on public pursuit-alert technology.",
        (
            (
                "Replace existing D.C. vehicular-pursuit restrictions with broader pursuit authority.",
                "section 2(a)",
            ),
            (
                "Require a Justice Department evaluation and report on PursuitAlert or similar technology.",
                "section 2(b)",
            ),
        ),
        (
            (
                "Pursuit remains limited when it poses unacceptable third-party harm, would be futile, or another means would be more effective or expeditious.",
                "section 2(a)",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:286": _d(
        "The House choice was whether to pass H.R. 1608 as amended, requiring Homeland Security to assess emerging vehicular-terrorism threats and countermeasures, including risks involving connected and autonomous vehicles, higher-risk locations, and protective technologies. DHS would report to Congress within 180 days and brief the committees after submission.",
        (
            (
                "Require a DHS assessment of current and emerging vehicular-terrorism threats.",
                "section 3(a)",
            ),
            (
                "Cover higher-risk locations, protective infrastructure, technology, coordination, and response measures.",
                "section 3(a)(2)",
            ),
            ("Require a congressional report and subsequent briefing.", "section 3"),
        ),
        confidence="medium",
    ),
    "house:119:1:289": _d(
        "The House choice was whether to pass H.R. 4405, requiring the Attorney General within 30 days to release searchable, downloadable unclassified Justice Department records concerning Jeffrey Epstein and related people, entities, agreements, investigations, detention, and death. It would limit withholding to specified privacy, victim-safety, investigative, graphic-content, and classified-information grounds and require a follow-up report to Congress.",
        (
            (
                "Require release of specified unclassified DOJ and FBI Epstein-related records within 30 days.",
                "section 2(a)",
            ),
            (
                "Bar withholding based only on embarrassment, reputational harm, or political sensitivity.",
                "section 2(b)",
            ),
            (
                "Require a congressional report on releases, withholdings, redactions, and named officials.",
                "section 3",
            ),
        ),
        (
            (
                "Permit tailored withholding or redaction for victim privacy, child sexual-abuse material, temporary active-investigation needs, graphic images, and properly classified information.",
                "section 2(c)",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:298": _d(
        "The House choice was whether to pass H.R. 5214, requiring pretrial and post-conviction detention for defined D.C. crimes of violence or dangerous crimes and secured cash bail for a separate group of public-safety or public-order offenses. It also would revise covered-offense definitions and apply to charges filed at least 30 days after enactment.",
        (
            (
                "Require pretrial and post-conviction detention for defined crimes of violence or dangerous crimes.",
                "section 2",
            ),
            (
                "Require secured appearance bonds for defined public-safety or public-order crimes.",
                "section 3",
            ),
            ("Revise definitions and related release procedures.", "sections 2-3"),
        ),
        (
            (
                "The changes apply to people charged on or after 30 days following enactment.",
                "section 4",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:299": _d(
        "The House choice was whether to pass H.R. 5107, repealing most of D.C.'s 2022 Comprehensive Policing and Justice Reform Amendment Act and reviving prior law, while retaining subtitles S and A of title I of that Act.",
        (
            (
                "Repeal most of D.C.'s 2022 policing reform law and restore or revive prior law.",
                "section 2(a)",
            ),
        ),
        (
            (
                "Retain subtitles S and A of title I rather than repealing the entire 2022 Act.",
                "section 2(b)",
            ),
        ),
    ),
    "house:119:1:340": _d(
        "The House choice was whether to pass H.R. 4371, requiring consultation, criminal-record collection, and gang-related screening before specified placements of unaccompanied children, and secure-facility placement for certain children age 12 or older who are flight risks or dangers. It also would bar release on recognizance, restrict sponsors by immigration status and household criminal history, require sponsor-household information sharing, and allow specified immediate-implementation exemptions.",
        (
            (
                "Require interagency consultation, foreign criminal-record requests, and gang-related screening before placement.",
                "sections 2-3",
            ),
            (
                "Require secure placement for specified children age 12 or older who are flight risks or dangers.",
                "section 3, secure-facility provision",
            ),
            (
                "Prohibit release on the child's own recognizance.",
                "section 3, placement generally",
            ),
            (
                "Restrict sponsors and household members by status and criminal history and require household information sharing.",
                "section 3, sponsor provisions",
            ),
        ),
        (
            (
                "The placement rules apply to pending and future release and custody determinations.",
                "section 6",
            ),
            (
                "Officials may bypass specified Paperwork Reduction Act or Administrative Procedure Act steps when they determine compliance would impede immediate implementation.",
                "section 5",
            ),
        ),
        confidence="medium",
    ),
    "house:119:1:351": _d(
        "The House choice was whether to pass H.R. 3492, creating federal offenses for specified genital or bodily procedures, administration of puberty-blocking or cross-sex hormones, and facilitation or transport for female genital mutilation involving minors, with maximum prison terms of 10 years. The bill would bar prosecution of the minor and preserve specified medical, intersex-condition, injury-treatment, imminent-health, and precocious-puberty exceptions while excluding mental or emotional distress alone from its health exception.",
        (
            (
                "Create offenses covering defined genital or bodily procedures and chemical castration involving minors.",
                "section 2, new 18 U.S.C. 116(a)-(b)",
            ),
            (
                "Cover facilitation, consent, or transport for female genital mutilation of a minor.",
                "section 2, new 18 U.S.C. 116(c)",
            ),
            (
                "Set fines and maximum 10-year imprisonment for the covered offenses.",
                "section 2, new 18 U.S.C. 116(a)-(c)",
            ),
            (
                "Define covered procedures, medications, minors, and jurisdictional connections.",
                "section 2, new 18 U.S.C. 116(d), (h)",
            ),
        ),
        (
            (
                "The minor who undergoes a covered procedure may not be prosecuted under the section.",
                "section 2, new 18 U.S.C. 116(f)",
            ),
            (
                "Specified medical, intersex-condition, prior-injury, imminent-physical-health, and precocious-puberty exceptions remain.",
                "section 2, new 18 U.S.C. 116(g)",
            ),
            (
                "Mental, behavioral, or emotional distress or disorder alone does not satisfy the minor-health exception.",
                "section 2, new 18 U.S.C. 116(g)(1)(B)",
            ),
        ),
        confidence="medium",
    ),
    "house:119:2:155": _d(
        "The House choice was whether to pass S. 4465, whose operative body would extend two Title VII FISA sunset references from April 30, 2026, to June 12, 2026, effective on the earlier of enactment or April 29, 2026. The action is kept ambiguous because the governed XML's Dublin Core title identifies the 110th Congress while its structured fields and governed action identify the 119th Congress and S. 4465.",
        (
            (
                "Extend two Title VII repeal-date references from April 30, 2026, to June 12, 2026.",
                "section 1(a)",
            ),
        ),
        (
            (
                "Take effect on the earlier of enactment or April 29, 2026.",
                "section 1(b)",
            ),
        ),
        confidence="low",
    ),
    "house:119:2:157": _d(
        "The House choice was whether to pass H.R. 2853 as amended, expanding specified federal theft, stolen-goods, forfeiture, and money-laundering rules for organized retail and supply-chain crime and aggregated conduct. It also would establish a Homeland Security coordination center for federal, State, local, and private-sector investigations and information sharing.",
        (
            (
                "Expand specified forfeiture, laundering, interstate-shipment, and stolen-goods provisions.",
                "section 3",
            ),
            (
                "Apply an aggregate $5,000 threshold over 12 months to specified transported or received stolen goods.",
                "section 3",
            ),
            (
                "Establish an Organized Retail and Supply Chain Crime Coordination Center.",
                "section 4",
            ),
            (
                "Require federal, State, local, and private-sector coordination and secure information sharing.",
                "section 4",
            ),
        ),
        confidence="medium",
    ),
    "house:119:2:169": _d(
        "The House choice was whether to pass H.R. 6260, extending the existing federal offense for false statements and overvaluation in insurance business to include posting monetary bail, criminal bail bonds, and federal immigration bail bonds.",
        (
            (
                "Add monetary bail, criminal bail bonds, and federal immigration bail bonds to the covered insurance-business transaction provision.",
                "section 2",
            ),
        ),
    ),
    "house:119:2:171": _d(
        "The House choice was whether to pass H.R. 5625, requiring the Attorney General within one year and annually thereafter to publish a list of States and local governments that allow personal-recognizance or unsecured-bond release for offenses the Attorney General determines threaten public safety or order.",
        (
            (
                "Require annual publication of jurisdictions permitting cashless pretrial release for covered offenses.",
                "section 2(a)",
            ),
        ),
        (
            (
                "The Attorney General defines the covered public-safety or public-order offenses, with violent, sexual, disorder, property-destruction, and flight examples.",
                "section 2(b)",
            ),
        ),
    ),
    "house:119:2:218": _d(
        "The House choice was whether to pass H.R. 8312, establishing Treasury fraud-prevention and payment-integrity data functions, a permanent Inspector General for Fraud, Accountability, and Recovery, and expanded fraud-related data-sharing authority. It also would transfer the Pandemic Response Accountability Committee's assets and obligations to the new office at the end of 2028.",
        (
            (
                "Establish Treasury fraud-prevention, Do Not Pay, and voluntary governmentwide data-analysis functions.",
                "section 2",
            ),
            (
                "Create a permanent Inspector General for Fraud, Accountability, and Recovery.",
                "section 3",
            ),
            (
                "Authorize specified interagency and private-entity data-sharing agreements and legislative recommendations.",
                "section 4",
            ),
            (
                "Terminate the pandemic committee and transfer its assets and obligations at the end of 2028.",
                "section 5",
            ),
        ),
        (
            (
                "The Fiscal Service data-analysis function excludes investigative and law-enforcement functions and is bounded by applicable privacy and security law.",
                "section 2",
            ),
        ),
        confidence="medium",
    ),
    "house:119:2:221": _d(
        "The House choice was whether to pass H.R. 9238, extending two Title VII FISA sunset references from June 12, 2026, to July 2, 2026. The extension would take effect on the earlier of enactment or June 11, 2026.",
        (
            (
                "Extend two Title VII repeal-date references from June 12, 2026, to July 2, 2026.",
                "section 1(a)",
            ),
        ),
        (
            (
                "Take effect on the earlier of enactment or June 11, 2026.",
                "section 1(b)",
            ),
        ),
    ),
    "house:119:2:227": _d(
        "The House choice was whether to pass H.R. 2478 as amended, allowing participating open-end investment companies and transfer agents to delay specified-adult account redemptions when they reasonably believe financial exploitation has occurred, is occurring, or was attempted. The bill sets contact, notice, review, recordkeeping, duration, and government-extension rules and requires SEC recommendations.",
        (
            (
                "Allow an elective trusted-contact and financial-exploitation protection regime for direct-at-fund accounts.",
                "section 2(a), new subsection (h)",
            ),
            (
                "Permit a 15-business-day redemption delay, with a possible 10-business-day internal extension and further government extension.",
                "section 2(a), new subsection (i)",
            ),
            (
                "Require internal review, notices, procedures, disclosures, and retained records.",
                "section 2(a), new subsection (i)",
            ),
            ("Require SEC regulatory and legislative recommendations.", "section 2(b)"),
        ),
        (
            (
                "Notice to a trusted contact is not required when the firm reasonably believes that contact is involved in exploitation.",
                "section 2(a), new subsection (i)(2)(D)",
            ),
        ),
        confidence="medium",
    ),
    "house:119:2:234": _d(
        "The House choice was whether to pass H.R. 3106, requiring Homeland Security to conduct a terrorism-response exercise involving extreme cold and cascading critical-infrastructure failures, with federal, State, Tribal, local, private-sector, and community coordination. DHS would submit an after-action report within 60 days after the exercise.",
        (
            (
                "Conduct a terrorism exercise involving extreme cold and cascading critical-infrastructure effects.",
                "section 2(a)-(b)",
            ),
            (
                "Coordinate federal, State, local, Tribal, territorial, private-sector, and community participants.",
                "section 2(b)",
            ),
            ("Submit a protected after-action report within 60 days.", "section 2(c)"),
        ),
    ),
    "house:119:2:240": _d(
        "The House choice was whether to pass H.R. 1181, barring payment-card networks and covered processors from requiring or assigning merchant category codes that specifically identify firearms retailers. The Attorney General would investigate complaints and could seek an injunction after notice and a cure period, while the bill would preempt related State and local code rules subject to specified transaction-integrity exceptions.",
        (
            (
                "Prohibit required or assigned merchant codes that specifically distinguish firearms retailers.",
                "section 2(a)",
            ),
            (
                "Create Attorney General complaint, investigation, notice, cure, and injunction procedures.",
                "section 2(b)",
            ),
            (
                "Preempt State and local laws regulating the covered merchant codes.",
                "section 2(c)",
            ),
            ("Require annual congressional reporting on enforcement.", "section 2(d)"),
        ),
        (
            ("The bill creates no private right of action.", "section 2(b)(4)(B)"),
            (
                "The preemption rule preserves compliance with laws on disputes, fraud, illegal or suspicious activity, data breaches, and cyber risks.",
                "section 2(c)(2)",
            ),
        ),
        confidence="medium",
    ),
    "house:119:2:259": _d(
        "The House choice was whether to add a Defense Secretary certification regime for domestic energy infrastructure tied to military readiness, fuel supply, or logistics, limiting State and local interference and creating operator enforcement rights and federal-court procedures. The amendment would establish heightened preliminary-relief standards while preserving specified federal safety, environmental, property, criminal, and operational boundaries.",
        (
            (
                "Authorize Defense certification of qualifying domestic energy infrastructure tied to military needs.",
                "governed Rules report pages 51-58",
            ),
            (
                "Limit specified State and local actions that halt, condition, restrict, or substantially delay certified infrastructure.",
                "governed Rules report pages 51-57",
            ),
            (
                "Create operator causes of action, venue rules, intervention rights, and preliminary-relief standards.",
                "governed Rules report pages 54-57",
            ),
        ),
        (
            (
                "Preserve specified federal environmental, pipeline-safety, occupational-safety, property, criminal, and operational authorities.",
                "governed Rules report page 57",
            ),
        ),
        confidence="medium",
        official="Amendment establishing protections and federal judicial procedures for Defense-certified domestic energy infrastructure.",
    ),
    "house:119:2:265": _d(
        "The House choice was whether to create a process allowing assigned service members and Defense civilian employees to request permission from designated commanders to carry personal firearms at specified Defense facilities, with denial limited to objective individualized reasons. The process would be due by December 31, 2027, and would repeal the prior FY2016 provision.",
        (
            (
                "Authorize assigned military and Defense civilian personnel to carry when permitted by a designated commander.",
                "governed Rules report page 75",
            ),
            (
                "Create a presumption of approval with denial limited to objective, clearly described, individualized reasons.",
                "governed Rules report page 75",
            ),
            (
                "Require implementation by December 31, 2027, and repeal the prior FY2016 provision.",
                "governed Rules report page 75",
            ),
        ),
        (
            (
                "Commander permission remains required, and the rule does not limit broader Defense authority to permit additional people.",
                "governed Rules report page 75",
            ),
        ),
        official="Amendment codifying and revising the process for certain Defense personnel to carry firearms at Defense facilities.",
    ),
    "house:119:2:273": _d(
        "The House choice was whether to add the Military Chaplains Modernization Act to H.R. 8800, codifying duties for Army, Navy, and Air Force chaplaincies; protecting chaplains from compelled actions contrary to their faith or endorsing organization; protecting religious exercise and confidential communications; and applying specified enforcement consequences through military law.",
        (
            (
                "Codify duties and advisory responsibilities for the service chaplaincies.",
                "governed Rules report pages 87-97",
            ),
            (
                "Protect chaplains against compelled contrary rites, speech, or tasks and against retaliation or discrimination.",
                "governed Rules report pages 89-97",
            ),
            (
                "Protect religious exercise and confidential, sacramental, and privileged communications.",
                "governed Rules report pages 89-97",
            ),
            (
                "Make specified violations enforceable under the Uniform Code of Military Justice and revise related statutes.",
                "governed Rules report pages 90-98",
            ),
        ),
        confidence="medium",
        official="Military Chaplains Modernization Act of 2026 amendment to H.R. 8800.",
    ),
    "house:119:2:275": _d(
        "The House choice was whether to bar federal funds from purchasing, installing, operating, maintaining, or contracting for automated speed-enforcement camera systems on military installations and require existing systems to be removed within 180 days. The amendment would preserve commander authority to enforce speed limits by other means and cameras used primarily for security, access control, force protection, or criminal investigations.",
        (
            (
                "Bar federal funds for automated speed-enforcement cameras on military installations.",
                "governed Rules report page 117",
            ),
            (
                "Require existing covered systems to be decommissioned and removed within 180 days.",
                "governed Rules report page 117",
            ),
        ),
        (
            (
                "Preserve other speed-enforcement methods and cameras primarily used for security, access control, force protection, or criminal investigation.",
                "governed Rules report page 117",
            ),
        ),
        official="Amendment prohibiting automated speed-enforcement cameras on military installations.",
    ),
    "house:119:2:278": _d(
        None,
        (),
        (
            (
                "The governed Rules report supplies floor structure but not the complete final House-passed package after amendments.",
                "governed Rules report pages 1-3",
            ),
        ),
        confidence="low",
        official="Final passage of H.R. 8800, the National Defense Authorization Act for Fiscal Year 2027, as amended.",
    ),
}


TARGETED_INITIAL_OMISSIONS: dict[str, tuple[str, ...]] = {
    "house:119:1:42": ("p4",),
    "house:119:1:131": ("p2", "p3"),
    "house:119:1:166": ("p2",),
    "house:119:1:275": ("l1",),
    "house:119:1:299": ("l1",),
    "house:119:1:340": ("p2", "p4"),
    "house:119:1:351": ("p3", "l2", "l3"),
}


COMPLEXITY_REASONS: dict[str, str] = {
    "house:119:1:351": "highest-complexity passage bill by governed operative-text byte count",
    "house:119:1:340": "complex passage bill with placement, screening, secure-facility, sponsor, and implementation mechanisms",
    "house:119:1:166": "Senate-origin S. 331 and multi-mechanism scheduling, enforcement, and research framework",
    "house:119:1:298": "complex passage bill with detention, bail, definitions, and applicability mechanisms",
    "house:119:2:157": "highest-complexity suspension passage as amended by governed operative-text byte count",
    "house:119:2:273": "highest-complexity amendment by governed operative-text byte count",
}
