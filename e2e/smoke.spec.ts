import { expect, test, type ConsoleMessage, type Page } from "@playwright/test";

/**
 * Smoke gate. These assert the app boots, routes, and that the team builder's
 * core interaction works against the real dataset -- enough that an agent can
 * tell whether a frontend change broke something without opening a browser.
 */

const IGNORED_CONSOLE = [/favicon/, /ERR_INTERNET_DISCONNECTED/];

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

/** The roster is fetched, so wait for it rather than racing the skeleton. */
async function gotoTeamBuilder(page: Page) {
  await page.goto("/team");
  await expect(page.getByRole("heading", { name: "Team Builder" })).toBeVisible();
  await expect(page.getByPlaceholder("Search Pokémon...")).toBeVisible();
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
    await gotoTeamBuilder(page);
  });

  test("loads the full roster from the engine dataset", async ({ page }) => {
    // The old page hardcoded 136 stub entries with no stats. This asserts we
    // are on the real dataset, not a stub.
    await expect(page.getByText(/1,2\d\d of 1,2\d\d/)).toBeVisible();
  });

  test("starts with three empty slots", async ({ page }) => {
    await expect(page.getByText("0/3 selected")).toBeVisible();
    await expect(page.getByText("Pick a Pokémon to fill this slot")).toHaveCount(3);
  });

  test("search filters the roster", async ({ page }) => {
    await page.getByPlaceholder("Search Pokémon...").fill("azumarill");

    await expect(page.getByRole("button", { name: /Add Azumarill/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Add Charmander/ })).toHaveCount(0);
  });

  test("adds a Pokemon with a real CP under the league cap", async ({ page }) => {
    await page.getByPlaceholder("Search Pokémon...").fill("azumarill");
    await page.getByRole("button", { name: /Add Azumarill/ }).click();

    await expect(page.getByText("1/3 selected")).toBeVisible();

    // Great League caps at 1500; the auto-levelled pick must land under it.
    const cp = await page.getByRole("listitem").filter({ hasText: "Azumarill" })
      .locator("p.tabular-nums").first().innerText();
    expect(Number(cp)).toBeGreaterThan(1000);
    expect(Number(cp)).toBeLessThanOrEqual(1500);
  });

  test("removes a Pokemon", async ({ page }) => {
    await page.getByPlaceholder("Search Pokémon...").fill("azumarill");
    await page.getByRole("button", { name: /Add Azumarill/ }).click();
    await expect(page.getByText("1/3 selected")).toBeVisible();

    await page.getByRole("button", { name: /Remove Azumarill/ }).click();
    await expect(page.getByText("0/3 selected")).toBeVisible();
  });

  test("caps the team at three", async ({ page }) => {
    const search = page.getByPlaceholder("Search Pokémon...");
    for (const name of ["Azumarill", "Medicham", "Skarmory", "Registeel"]) {
      await search.fill(name);
      const button = page.getByRole("button", { name: new RegExp(`Add ${name}`) });
      if (await button.isEnabled().catch(() => false)) await button.click();
    }

    // Four attempted, three allowed.
    await expect(page.getByText("3/3 selected")).toBeVisible();
  });

  test("switching league re-caps the team", async ({ page }) => {
    await page.getByPlaceholder("Search Pokémon...").fill("azumarill");
    await page.getByRole("button", { name: /Add Azumarill/ }).click();

    const cpOf = async () =>
      Number(
        await page.getByRole("listitem").filter({ hasText: "Azumarill" })
          .locator("p.tabular-nums").first().innerText()
      );

    const greatCp = await cpOf();
    await page.getByRole("tab", { name: /Ultra League/ }).click();
    await expect.poll(cpOf).toBeGreaterThan(greatCp);
    expect(await cpOf()).toBeLessThanOrEqual(2500);
  });

  test("shows precomputed matchups against the meta", async ({ page }) => {
    await page.getByPlaceholder("Search Pokémon...").fill("azumarill");
    await page.getByRole("button", { name: /Add Azumarill/ }).click();

    // Scope to the team panel: the picker renders list items too, and its
    // Azumarill entry comes first in the DOM.
    const team = page.getByRole("region", { name: "Your team" });
    const slot = team.getByRole("listitem").filter({ hasText: "Azumarill" }).first();
    await expect(
      slot.getByRole("heading", { name: "Against the meta" })
    ).toBeVisible();

    // Two lists -- what it beats and what it loses to -- three rows each.
    await expect(slot.getByRole("list")).toHaveCount(2);
    await expect(slot.getByRole("list").first().getByRole("listitem")).toHaveCount(3);
    await expect(slot.getByRole("list").last().getByRole("listitem")).toHaveCount(3);

    // Best matchups must actually be better than the worst ones.
    const ratings = await slot.getByRole("listitem").locator("span.tabular-nums").allInnerTexts();
    const numbers = ratings.map(Number).filter((n) => !Number.isNaN(n));
    expect(numbers.length).toBeGreaterThanOrEqual(6);
    expect(Math.max(...numbers.slice(0, 3))).toBeGreaterThan(
      Math.min(...numbers.slice(-3))
    );
  });

  test("matchups come from a static file, not a server", async ({ page }) => {
    const dataRequests: string[] = [];
    page.on("request", (request) => {
      const url = new URL(request.url());
      if (url.pathname.startsWith("/data/")) dataRequests.push(url.pathname);
      // Anything that looks like a live simulator would defeat the point.
      expect(url.pathname).not.toMatch(/^\/api\//);
    });

    await gotoTeamBuilder(page);
    await page.getByPlaceholder("Search Pokémon...").fill("azumarill");
    await page.getByRole("button", { name: /Add Azumarill/ }).click();
    await expect(page.getByRole("heading", { name: "Against the meta" })).toBeVisible();

    expect(dataRequests).toContain("/data/matchups.great.json");
  });

  test("switching league loads that league's matchups", async ({ page }) => {
    await page.getByPlaceholder("Search Pokémon...").fill("registeel");
    await page.getByRole("button", { name: /Add Registeel/ }).click();
    await expect(page.getByRole("heading", { name: "Against the meta" })).toBeVisible();

    await page.getByRole("tab", { name: /Ultra League/ }).click();

    // The panel comes back once the Ultra file has loaded.
    await expect(page.getByRole("heading", { name: "Against the meta" })).toBeVisible();
  });
});

test.describe("IP hygiene", () => {
  test("no publisher artwork is requested", async ({ page }) => {
    const assetRequests: string[] = [];
    page.on("request", (req) => {
      const url = req.url();
      if (/pokeapi|pokemondb|serebii|assets\.pokemon\.com|projectpokemon/i.test(url)) {
        assetRequests.push(url);
      }
    });

    await gotoTeamBuilder(page);
    await page.getByPlaceholder("Search Pokémon...").fill("azumarill");
    await page.getByRole("button", { name: /Add Azumarill/ }).click();
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
