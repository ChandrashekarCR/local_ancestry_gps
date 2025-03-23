merged.fam - the HGDP populations analyzed. notice that the last 135 are the refrence regional popualtions.
merged.bim - the map file, you'll need it to know which chromosome is being analyzed.
LocalAncestry.zip - The gene pool split per 500 SNPs windows. Use merged.bim to know, which segment you analyze, note that those windows would overlap chromosomes, which is wrong.
You can either throw those regions away or assign the ancestry from those windows to both start/end chromosomes, which is probably better.
HGDP.xlsx - Annotation for HGDP individuals.
HGDP coordinates.xlsx - cooridnates per HGDP individuals (you don't really need it).

Note, LocalAncestry has data for the first 3-4 chromosomes. I think this would be enough here.

Best,
Eran

