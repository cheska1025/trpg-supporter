import { test, expect } from '@playwright/test';

test('characters page loads and can open', async ({ page }) => {
  await page.goto('/characters');
  await expect(page.getByRole('heading', { name: 'Characters' })).toBeVisible();
});
