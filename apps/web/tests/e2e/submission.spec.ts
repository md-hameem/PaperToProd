import { test, expect } from '@playwright/test';

test.describe('Job Submission Flow', () => {
  test('User can submit a job via arXiv ID and view progress', async ({ page }) => {
    // 1. Login (assuming mock auth or bypassing via cookie in a real test)
    await page.goto('/login');
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    // 2. Dashboard submission
    await expect(page).toHaveURL('/dashboard');
    await page.fill('input[placeholder*="arXiv ID"]', '2103.00020');
    await page.click('button:has-text("Submit")');

    // 3. Monitor Progress
    await expect(page).toHaveURL(/\/jobs\/\d+/);

    // Check if the progress steps appear (Planner -> Scaffolder -> Coder)
    await expect(page.locator('text=Planner')).toBeVisible();

    // In a full E2E, we might wait for completion, but it takes 15 minutes.
    // So we just verify the initial WebSocket updates arrive.
    await expect(page.locator('text=Generating scaffold')).toBeVisible({ timeout: 10000 });
  });
});
