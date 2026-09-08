import { test, expect } from '@playwright/test';
import path from 'node:path';

const csv = path.resolve(process.cwd(), '../test.csv');

test.describe('KYC end-to-end pipeline', () => {
  test('upload -> prep -> schema -> analysis -> report', async ({ page }) => {
    test.setTimeout(180_000);

    await page.goto('/upload');
    await expect(page.getByRole('heading', { name: /Analyse KYC de données/i })).toBeVisible();

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(csv);

    // UploadStep should advance to schema only after upload + Prep succeed.
    await expect(page.getByText(/Détection du schéma|Schéma/i).first()).toBeVisible({ timeout: 60_000 });

    // The schema step exposes selects/comboboxes for the KYC mapping.
    const selects = page.locator('select');
    const count = await selects.count();
    expect(count).toBeGreaterThanOrEqual(8);

    for (let i = 0; i < count; i++) {
      const select = selects.nth(i);
      if (await select.isVisible()) {
        const options = await select.locator('option').evaluateAll((items) =>
          items.map((item) => ({ value: (item as HTMLOptionElement).value, text: item.textContent || '' }))
        );
        const usable = options.find((option) => option.value && !/sélection|select/i.test(option.text));
        if (usable) await select.selectOption(usable.value);
      }
    }

    const continueButton = page.getByRole('button', { name: /continuer|analyse/i });
    await expect(continueButton).toBeEnabled({ timeout: 10_000 });
    await continueButton.click();

    // Country validation + active-line detection + analysis can be backend-bound.
    await expect(page.getByText(/Analyse|analyse|complétée|Rapport/i).first()).toBeVisible({ timeout: 120_000 });

    // The report is the terminal state of the pipeline.
    await expect(page.getByText(/Analyse complétée avec succès/i)).toBeVisible({ timeout: 120_000 });
  });

  test('dashboard -> analysis detail', async ({ page }) => {
    test.setTimeout(60_000);
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    const details = page.getByRole('link').filter({ hasText: /Détails/i }).first();
    if (await details.count()) {
      await details.click();
      await expect(page).toHaveURL(/\/dashboard\/[^/]+$/);
      await expect(page.getByText(/Analyse complétée avec succès|Chargement du rapport/i).first()).toBeVisible({ timeout: 30_000 });
    }
  });
});
