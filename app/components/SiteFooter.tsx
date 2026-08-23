/**
 * Affiliation disclaimer.
 *
 * Rendered on every page. Nominative use of the trademarks this tool refers to
 * depends on not implying endorsement, so this notice is part of the product,
 * not boilerplate. Enforced by pypogo/pypogo/tests/test_ip_hygiene.py.
 */
export default function SiteFooter() {
  return (
    <footer className="w-full border-t border-white/10 bg-black/40 px-4 py-6 text-center">
      <p className="mx-auto max-w-3xl text-xs leading-relaxed text-gray-400">
        Unofficial fan-made tool. Not affiliated with, endorsed by, or sponsored
        by Nintendo, The Pokémon Company, Game Freak, Creatures Inc., or
        Niantic, Inc. Pokémon and related names are trademarks of their
        respective owners, used here only to identify the creatures and moves
        this tool analyses. No official artwork or game assets are distributed.
      </p>
    </footer>
  );
}
