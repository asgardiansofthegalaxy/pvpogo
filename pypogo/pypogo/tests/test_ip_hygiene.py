"""
Enforce the data policy in DISCLAIMER.md.

The project's position is that factual game data (base stats, typings, move
values) is fine to derive and distribute, while publisher *assets* -- artwork,
raw export files, logos -- are not. That distinction only holds if it is
actually enforced, so these are tests rather than a note in a README.
"""

import os
import re
import subprocess
from pathlib import Path
from unittest import TestCase

REPO_ROOT = Path(__file__).resolve().parents[3]

# Hosts that serve publisher artwork. Rendering these ships copyrighted sprites
# regardless of who is rehosting them.
ASSET_HOSTS = [
    "raw.githubusercontent.com/PokeAPI",
    "assets.pokemon.com",
    "pokemondb.net/sprites",
    "serebii.net/pokemon",
    "img.pokemondb.net",
    "projectpokemon.org/images",
]

# Filenames used by raw Game Master exports. Matched against the basename:
# an unanchored ".*" here would span the path separator and flag the derived
# files that live in the game_master/ directory.
RAW_EXPORT_PATTERN = re.compile(
    r"^(gm_latest|game_master_latest|game_master[^/]*)\.json$", re.IGNORECASE
)

SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".py", ".css", ".html", ".json"}
SKIP_DIRS = {
    "node_modules", ".git", ".next", ".venv", "venv", "__pycache__",
    "test-results", "playwright-report", ".pyenv",
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return [line for line in result.stdout.splitlines() if line]


def source_files():
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.suffix in SOURCE_SUFFIXES:
                yield path


class RawExportTests(TestCase):
    def test_no_raw_game_master_export_is_tracked(self):
        offenders = [f for f in tracked_files() if RAW_EXPORT_PATTERN.match(Path(f).name)]

        self.assertEqual(
            offenders,
            [],
            "Raw Game Master exports are the publisher's own files and must not be "
            f"committed. Untrack: {offenders}. See DISCLAIMER.md.",
        )

    def test_engine_runs_without_a_raw_export(self):
        # The derived dataset is what the engine reads; the raw export is a
        # build input only. If this ever fails, the raw file has crept back onto
        # the import path.
        from pypogo.game_master.game_master import (
            MOVES_FILE,
            POKEDEX_FILE,
            RAW_GAME_MASTER_FILE,
            GameMaster,
        )

        source = Path(GameMaster._read_moves.__code__.co_filename).read_text()
        init_body = source.split("def __init__(self)")[1].split("@staticmethod")[0]

        self.assertNotIn(
            RAW_GAME_MASTER_FILE,
            init_body,
            "GameMaster.__init__ must not read the raw export.",
        )
        self.assertIn(POKEDEX_FILE, source)
        self.assertIn(MOVES_FILE, source)


class PublisherAssetTests(TestCase):
    def test_no_source_file_references_a_publisher_asset_host(self):
        offenders = []
        for path in source_files():
            if path.name == Path(__file__).name:
                continue  # this file necessarily spells out the hosts it bans
            try:
                content = path.read_text(errors="ignore")
            except OSError:
                continue
            for host in ASSET_HOSTS:
                if host in content:
                    offenders.append(f"{path.relative_to(REPO_ROOT)} -> {host}")

        self.assertEqual(
            offenders,
            [],
            "Publisher artwork must not be rendered, even when rehosted by a third "
            f"party. Use SpeciesAvatar instead. Offenders: {offenders}",
        )

    def test_no_unexpected_image_assets_are_tracked(self):
        # Any new image is a potential piece of publisher artwork, so additions
        # are a deliberate decision rather than something that slips in.
        allowed = {"public/sunflower-bg.jpg", "public/vite.svg"}
        images = {
            f
            for f in tracked_files()
            if Path(f).suffix.lower()
            in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}
        }

        self.assertEqual(
            images - allowed,
            set(),
            "New image assets were added. Confirm they are not publisher artwork, "
            "then add them to the allowlist in this test.",
        )


class DisclaimerTests(TestCase):
    def test_disclaimer_exists_and_makes_the_key_statements(self):
        disclaimer = (REPO_ROOT / "DISCLAIMER.md").read_text().lower()

        for phrase in ["not affiliated", "trademark", "nominativ"]:
            self.assertIn(phrase, disclaimer, f"DISCLAIMER.md must state: {phrase}")

    def test_disclaimer_is_surfaced_in_the_ui(self):
        # A disclaimer nobody sees does not do the job it exists to do.
        layout = (REPO_ROOT / "app" / "layout.tsx").read_text().lower()

        self.assertIn(
            "not affiliated",
            layout,
            "The app must surface the affiliation disclaimer to users.",
        )
