import { expect, test } from '@playwright/test';

test('loads demo candidates and updates selected detail', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'Molecule Atlas' })).toBeVisible();
  await expect(page.getByText('Demo Candidate Set')).toBeVisible();
  await expect(page.getByRole('cell', { name: 'Aspirin' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Aspirin' })).toBeVisible();

  await page.getByRole('cell', { name: 'Caffeine' }).click();

  await expect(page.getByRole('heading', { name: 'Caffeine' })).toBeVisible();
  await expect(page.getByLabel('Caffeine detail')).toContainText('Nearest Neighbors');
});

test('keeps invalid SMILES visible and non-fatal', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('cell', { name: 'Invalid Demo' })).toBeVisible();
  await page.getByRole('cell', { name: 'Invalid Demo' }).click();

  await expect(page.getByRole('heading', { name: 'Invalid Demo' })).toBeVisible();
  await expect(page.getByText('Invalid SMILES: not_a_smiles')).toBeVisible();
  await expect(page.getByText('Descriptors are unavailable for invalid molecules.')).toBeVisible();
});

test('valid-only filter hides invalid candidates', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('cell', { name: 'Invalid Demo' })).toBeVisible();
  await page.getByLabel('Valid only').check();

  await expect(page.getByRole('cell', { name: 'Invalid Demo' })).toHaveCount(0);
  await expect(page.getByRole('cell', { name: 'Aspirin' })).toBeVisible();
});

test('opens 3D conformer view for a valid molecule', async ({ page }) => {
  await page.goto('/');

  await page.getByRole('button', { name: '3D conformer' }).click();

  await expect(page.getByText('Generated conformer. Not a docked binding pose.')).toBeVisible();
  await expect(page.getByLabel('3D conformer viewer')).toBeVisible();
});

test('renders the chemical-space section', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'Chemical Space' })).toBeVisible();
  await expect(page.getByText('Morgan fingerprints · PCA')).toBeVisible();
});
