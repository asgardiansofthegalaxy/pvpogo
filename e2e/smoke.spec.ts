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

  test("a fresh pick defaults to the moveset the matrix simulated", async ({
    page,
  }) => {
    await page.getByPlaceholder("Search Pokémon...").fill("azumarill");
    await page.getByRole("button", { name: /Add Azumarill/ }).click();

    const team = page.getByRole("region", { name: "Your team" });
    const slot = team.getByRole("listitem").filter({ hasText: "Azumarill" }).first();

    // The dataset lists Rock Smash first and Play Rough second; the ratings
    // shown underneath were computed on Bubble / Hydro Pump + Ice Beam, so
    // that is what the slot has to start with.
    await expect(slot.getByRole("button", { name: "Fast move" })).toHaveText(
      /Bubble/
    );
    await expect(slot.getByRole("button", { name: "Charged moves" })).toHaveText(
      /Hydro Pump.*Ice Beam/
    );

    // Which means the panel has nothing to disclaim about a fresh pick.
    await expect(slot.getByText(/not the moves you picked/)).toHaveCount(0);

    // And it does have something to disclaim as soon as the build differs,
    // which is what keeps the assertion above from passing vacuously.
    await slot.getByRole("button", { name: "Charged moves" }).click();
    await page.getByRole("option", { name: /Play Rough/ }).click();
    await page.keyboard.press("Escape");
    await expect(slot.getByText(/not the moves you picked/)).toHaveCount(1);
  });

  test("finds the best IV spread for the league", async ({ page }) => {
    await page.getByPlaceholder("Search Pokémon...").fill("registeel");
    await page.getByRole("button", { name: /Add Registeel/ }).click();

    const team = page.getByRole("region", { name: "Your team" });
    const slot = team.getByRole("listitem").filter({ hasText: "Registeel" }).first();
    const optimise = slot.getByRole("button", {
      name: /Set Registeel to the best IVs/,
    });

    // The default 0/15/15 is a good spread but not the best one under 1500.
    await expect(slot).toContainText(/Rank #\d+ of 4,096/);
    await expect(slot).not.toContainText("Rank #1 of 4,096");

    await optimise.click();

    // Rank 1 by construction, and the button retires rather than sitting there
    // as a no-op.
    await expect(slot).toContainText("Rank #1 of 4,096");
    await expect(optimise).toBeDisabled();

    // Under a CP cap the best spread is a lower attack IV levelled higher, so
    // the optimiser has to actually move the boxes, not just relabel itself.
    const defIv = slot.getByRole("spinbutton").nth(1);
    await expect(defIv).not.toHaveValue("15");

    // And the ratings underneath were simulated at the spread it just left, so
    // the panel has to say they no longer describe this Pokemon.
    await expect(slot.getByText(/not your spread/)).toBeVisible();
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

  test("shows what the whole team has no answer to", async ({ page }) => {
    const coverage = page.getByRole("region", { name: "Team coverage" });

    // Nothing to analyse yet, so it says what it will do rather than showing
    // an empty panel.
    await expect(coverage).toContainText(/Pick a Pokémon/);

    const search = page.getByPlaceholder("Search Pokémon...");
    for (const name of ["Azumarill", "Registeel", "Medicham"]) {
      await search.fill(name);
      await page.getByRole("button", { name: new RegExp(`Add ${name}`) }).click();
    }

    // A recognisable Great League core answers most of the meta; the count is
    // asserted as a range because the meta is derived, not curated, and moves
    // when the matrix is rebuilt.
    await expect(coverage).toContainText(/of 100 meta picks answered/);
    const answered = Number(
      (await coverage.innerText()).match(/(\d+)\s+of 100 meta picks answered/)?.[1]
    );
    expect(answered).toBeGreaterThan(80);
    expect(answered).toBeLessThan(100);

    // The gaps are the point: each names the meta pick and the team's best
    // rating against it, which must be a losing one.
    const gaps = coverage.getByRole("listitem");
    expect(await gaps.count()).toBeGreaterThan(0);
    const ratings = await gaps.locator("span.tabular-nums").allInnerTexts();
    for (const rating of ratings) expect(Number(rating)).toBeLessThan(500);
  });

  test("the full matrix is fetched only once there is a team", async ({ page }) => {
    const rowRequests: string[] = [];
    page.on("request", (req) => {
      if (/matchups\.\w+\.rows\.json/.test(req.url())) rowRequests.push(req.url());
    });

    // Browsing the roster must not pull the larger half of the data.
    await page.getByPlaceholder("Search Pokémon...").fill("azumarill");
    await expect(page.getByRole("button", { name: /Add Azumarill/ })).toBeVisible();
    expect(rowRequests).toEqual([]);

    await page.getByRole("button", { name: /Add Azumarill/ }).click();
    await expect
      .poll(() => rowRequests.length)
      .toBeGreaterThan(0);
    expect(rowRequests[0]).toContain("matchups.great.rows.json");
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
