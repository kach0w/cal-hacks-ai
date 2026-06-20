/**
 * Optional, SECONDARY Midjourney concept illustration. ALWAYS rendered with the
 * 'Illustrative concept - not a photo of this site' label. The honest primary 'after'
 * is the overlay on the real photo, not this.
 */
export default function ConceptToggle({ conceptUrl }: { conceptUrl: string | null }) {
  if (!conceptUrl) return null;
  return (
    <figure>
      <img src={conceptUrl} alt="concept illustration" className="rounded" />
      <figcaption className="text-xs text-amber-700">
        Illustrative concept — not a photo of this site.
      </figcaption>
    </figure>
  );
}
