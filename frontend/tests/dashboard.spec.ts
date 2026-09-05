import { test, expect } from '@playwright/test';

test.describe('Dashboard & Job Search', () => {
  const timestamp = Date.now();
  const testEmail = `dash_user_${timestamp}@example.com`;
  const testPassword = 'SecurePassword123!';

  test.beforeEach(async ({ page }) => {
    // Register a new user for each test to ensure a clean state
    await page.goto('/');
    await page.click('button:has-text("Sign up")');
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', testPassword);
    await page.click('button[type="submit"]');
    
    // Wait for navigation to /dashboard
    await page.waitForURL(/.*\/dashboard/, { timeout: 10000 });
    await page.waitForLoadState('networkidle');
    
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test('shows upload state for new user', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Upload your resume');
    await expect(page.locator('.dropzone')).toBeVisible();
  });

  test('can sign out', async ({ page }) => {
    await page.click('.sign-out-btn');
    // Should redirect back to / (auth page)
    await expect(page).toHaveURL(/.*\//);
  });
});
