// Prospective compatibility release, using public fixture responses only.
import fs from 'node:fs';
import path from 'node:path';
import {gunzipSync} from 'node:zlib';
import {expect, test} from '@playwright/test';
import {contentHash, findingIdentity} from '../lib/recordCard.mjs';

const candidate = JSON.parse(fs.readFileSync(path.resolve('../docs/review_packets/record_at_a_glance_v1/candidate.json'), 'utf8'));
const snapshots = {
  old: JSON.parse(gunzipSync(fs.readFileSync(path.resolve('..', candidate.source_snapshot)))),
  locator: JSON.parse(gunzipSync(fs.readFileSync(path.resolve('../docs/review_packets/education79_locator_v1/prepared/expected-public-after.json.gz')))),
};
const educationEntry = candidate.entries.find(e => e.issue_id === 'EDUCATION_WORKFORCE');
const member = 'leg_valerie_p_foushee';
const profile = {id: member, bioguide_id: 'F000477', name_display: 'Valerie P. Foushee', chamber: 'house', state: 'NC', district: '04', party: 'D'};
async function fixture(page, state, mutate = () => {}) {
  await page.route('http://localhost:8000/**', async route => {
    const url = new URL(route.request().url());
    if (url.pathname.endsWith('/profile')) return route.fulfill({json: profile});
    const scope = url.searchParams.get('scope') || 'all';
    const resource = url.pathname.endsWith('/editorial-presentations') ? 'editorial' : url.pathname.endsWith('/evidence') ? url.pathname.split('/')[4] : 'positions';
    const supplied = snapshots[state.value][`${member}:${scope}:${resource}`];
    if (!supplied) throw Error('Unexpected fixture interface: ' + url.pathname);
    const body = structuredClone(supplied.body);
    if (resource === 'editorial') mutate(body);
    await route.fulfill({status: supplied.status, json: body});
  });
}
const educationHash = (state, scope) => contentHash(snapshots[state][`${member}:${scope}:editorial`].body.presentations.find(p => p.issue_id === 'EDUCATION_WORKFORCE'));

for (const scope of ['119', 'all']) {
  const landing = `/?representative=${member}&scope=${scope}`;
  test(`${scope}: compatibility deployment, exact activation and registry rollback retain the card and actual-source journeys`, async ({page}) => {
    const state = {value: 'old'};
    await fixture(page, state);
    await page.emulateMedia({reducedMotion: 'reduce'});
    for (const version of ['old', 'locator', 'old']) {
      state.value = version;
      await page.goto(landing);
      await expect(page.getByTestId('record-card-entry')).toHaveCount(6);
      const source = await educationHash(version, scope);
      const link = page.locator('#' + educationEntry.id);
      expect(new URL(await link.getAttribute('href'), 'http://localhost').searchParams.get('source')).toBe(source);
      for (const entry of candidate.entries) await expect(page.getByTestId('record-card').getByText(entry.explanation, {exact: true})).toBeVisible();
      await link.click();
      await expect(page.getByTestId('card-finding-detail')).toBeVisible();
      await expect(page).toHaveURL(new RegExp('source=' + source));
      const votes = page.getByRole('link', {name: `See 2 House votes: ${educationEntry.headline}`});
      const receiptUrl = new URL(await votes.getAttribute('href'), 'http://localhost');
      expect(receiptUrl.searchParams.get('source')).toBe(source);
      expect(receiptUrl.searchParams.get('view')).toBe('receipts');
      await votes.focus(); await votes.press('Enter');
      await expect(page.locator('[data-canonical-action-id]')).toHaveCount(2);
      for (const action of educationEntry.action_ids) await expect(page.locator(`[data-canonical-action-id="${action}"]`)).toBeVisible();
      await page.reload(); await expect(page.locator('[data-canonical-action-id]')).toHaveCount(2);
      await page.goBack(); await expect(page.getByTestId('card-finding-detail')).toBeVisible();
      await page.goForward(); await expect(page.locator('[data-canonical-action-id]')).toHaveCount(2);
      await page.getByRole('link', {name: 'Return to record at a glance'}).click();
      await expect(page.getByTestId('record-card-entry')).toHaveCount(6);
    }
  });
  test(`${scope}: stale deep links retain the exact-current-source guard and full issue fallback`, async ({page}) => {
    const state = {value: 'locator'};
    await fixture(page, state);
    const oldHash = await educationHash('old', scope);
    await page.goto(`${landing}&issue=EDUCATION_WORKFORCE&finding=${encodeURIComponent(educationEntry.finding_id)}&source=${oldHash}#finding-detail`);
    await expect(page.getByText(/This finding link does not match/)).toBeVisible();
    await expect(page.getByTestId('card-finding-detail')).toHaveCount(0);
    await expect(page.getByTestId('reviewed-analysis')).toBeVisible();
    const evidenceKey = `${member}:${scope}:EDUCATION_WORKFORCE`;
    const recordedActions = snapshots.locator[evidenceKey].body.evidence.length;
    expect(recordedActions).toBe(snapshots.old[evidenceKey].body.evidence.length);
    await expect(page.locator('#vote-record')).toContainText(`${recordedActions} recorded actions`);
  });
  for (const mutation of ['omitted finding', 'provenance']) test(`${scope}: ${mutation} mutation withholds the card without inventing no-summary`, async ({page}) => {
    await fixture(page, {value: 'locator'}, body => {
      const p = body.presentations.find(p => p.issue_id === 'EDUCATION_WORKFORCE');
      if (mutation === 'provenance') p.provenance.test_change = 'unknown';
      else p.repeated_patterns.find(f => findingIdentity(f) !== educationEntry.finding_id).public_title += ' altered';
    });
    await page.goto(landing);
    await expect(page.getByTestId('record-card-entry')).toHaveCount(0);
    await expect(page.getByText(/The reviewed source has changed/)).toBeVisible();
    await expect(page.getByText(/No reviewed findings are available/)).toHaveCount(0);
  });
}
