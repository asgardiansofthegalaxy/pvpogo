import { expect, test, type ConsoleMessage, type Page } from "@playwright/test";

/**
 * Smoke gate. These assert the app boots, routes, and that the team builder's
 * core interaction works -- enough that an agent can tell whether a frontend
 * change broke something without a human opening a browser.
 */

/** Sprite images are fetched from a third-party host; a flaky CDN is not a bug in this app. */
const IGNORED_CONSOLE = [/raw\.githubusercontent\.com/, /favicon/, /ERR_INTERNET_DISCONNECTED/];

function collectConsoleErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (msg: ConsoleMessage) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (IGNORED_CONSOLE.some((pattern) => pattern.test(text))) return;
    errors.push(text);
  });
  page.on("pageerror", (err) => errors.push(String(err)));
  return errors;
}

test.describe("landing page", () => {
  test("renders the hero and the newsletter form", async ({ page }) => {
    const errors = collectConsoleErrors(page);
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "PvPogo", level: 1 })).toBeVisible();
    await expect(page.getByPlaceholder("Enter your email")).toBeVisible();
    await expect(page.getByRole("button", { name: "Subscribe" })).toBeVisible();

    expect(errors, `unexpected console errors:\n${errors.join("\n")}`).toEqual([]);
  });

  test("routes to the team builder", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("link", { name: "Build Your Team" }).click();

    await expect(page).toHaveURL(/\/team$/);
    await expect(page.getByRole("heading", { name: "Team Builder" })).toBeVisible();
  });
});

test.describe("team builder", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/team");
  });

  test("starts empty", async ({ page }) => {
    await expect(page.getByText("No Pokemon selected")).toBeVisible();
    await expect(page.getByText("0/6 Pokemon selected")).toBeVisible();
  });

  test("search filters the roster", async ({ page }) => {
    await page.getByPlaceholder("Search Pokemon...").fill("bulba");

    await expect(page.getByText("Bulbasaur", { exact: true })).toBeVisible();
    await expect(page.getByText("Charmander", { exact: true })).toHaveCount(0);
  });

  test("adds and removes a Pokemon", async ({ page }) => {
    const roster = page.getByPlaceholder("Search Pokemon...");
    await roster.fill("bulbasaur");
    await page.getByText("Bulbasaur", { exact: true }).click();

    await expect(page.getByText("1/6 Pokemon selected")).toBeVisible();
    await expect(page.getByText("No Pokemon selected")).toHaveCount(0);

    await page.getByRole("button", { name: "✕" }).click();

    await expect(page.getByText("0/6 Pokemon selected")).toBeVisible();
    await expect(page.getByText("No Pokemon selected")).toBeVisible();
  });

  test("caps the team at six", async ({ page }) => {
    const names = [
      "Bulbasaur", "Charmander", "Squirtle", "Pikachu",
      "Sandshrew", "Clefairy", "Vulpix",
    ];
    const search = page.getByPlaceholder("Search Pokemon...");

    for (const name of names) {
      await search.fill(name);
      await page.getByText(name, { exact: true }).first().click();
    }

    // Seven clicked, six allowed.
    await expect(page.getByText("6/6 Pokemon selected")).toBeVisible();
  });
});

test.describe("IP hygiene", () => {
  test("no publisher artwork is requested", async ({ page }) => {
    // The species mark is drawn by SpeciesAvatar, not fetched. If a sprite host
    // ever creeps back into the UI, this catches it at runtime rather than
    // relying on a source grep alone.
    const assetRequests: string[] = [];
    page.on("request", (req) => {
      const url = req.url();
      if (/pokeapi|pokemondb|serebii|assets\.pokemon\.com|projectpokemon/i.test(url)) {
        assetRequests.push(url);
      }
    });

    await page.goto("/team");
    await page.getByPlaceholder("Search Pokemon...").fill("bulbasaur");
    await page.getByText("Bulbasaur", { exact: true }).click();
    await page.waitForLoadState("networkidle");

    expect(assetRequests, `publisher asset requests: ${assetRequests.join(", ")}`).toEqual([]);
  });

  test("the affiliation disclaimer is visible on every page", async ({ page }) => {
    for (const route of ["/", "/team"]) {
      await page.goto(route);
      await expect(
        page.getByText(/Not affiliated with, endorsed by, or sponsored by/i)
      ).toBeVisible();
    }
  });
});
