# Neuronte

A neural net that is its own font. A character goes in, as ASCII or as
UTF-8. The net writes that character's pixels into a buffer the caller
owns. No font file, glyph table or bitmap atlas is consulted. The
weights are the font.

This is version 0.1.6. [CHANGES.md](CHANGES.md) lists what is new since
0.1.1.

Version-1 distance models accept any integer hidden width from 1 to
1024, including widths 1, 2, 4, 6 and 12. The native loops use the declared width without
padding to a larger model. Older readers requiring multiples of eight reject
the newly supported widths. Colour-model widths retain their multiple-of-eight
requirement. `make test-widths` checks narrow distance models and their packing.

Games, the OS and `soft-raster` link the library and pass in the buffer.
The same buffer can be shown in a Kilix terminal or in a GUI window. The
library does not open the window or take the terminal.

Status: public, at github.com/itsmygithubacct/neuronte. The library ships
terminal bundles, per-size desktop faces, a scalable desktop face, and separate
colour nets. Scalars a file was not trained on get a mark of their own, not a
letter. Desktop adapters fall back for unsupported strings and styles.

| Weights | Use | Characters | Hidden width | Parameters | File |
|---|---|---|---:|---:|---:|
| `neuronte-split-v5` | the font to use | 1,176, over six nets and a router; [recipe and validation](weights/neuronte-split-v5.md) | 48, 128, 192 and 256 | 392,716 | 1,573,128 bytes |
| `neuronte-split-v6` | RC9 Braille: split-v5 with its Braille net replaced by the tiled `neuronte-braille-v1`; the video player's full-mode bundle; [recipe and validation](weights/neuronte-braille-v1.md) | 1,176, over six nets and a router | 6, 128, 192 and 256 | 384,232 | 1,539,388 bytes |
| `neuronte-split-v7` | split-v6 with the ASCII character groups added: tiled Braille and `neuronte-ascii-groups-v1`; not a default; [recipe and checks](weights/neuronte-split-v7.md) | 1,176, over ten nets and a router | 6, 64, 128, 192 and 256 | 441,068 | 1,768,128 bytes |
| `neuronte-split-v7-symbol-v1` | split-v7 with the symbol character groups added: tiled Braille, `neuronte-ascii-groups-v1` and `neuronte-symbol-v1`; not a default; [recipe and checks](weights/neuronte-split-v7-symbol-v1.md) | 1,176, over fourteen nets and a router | 6, 32, 64, 128, 192 and 256 | 461,296 | 1,850,412 bytes |
| `neuronte-split-v8` | split-v7 with the symbol, pixel and accent character groups added: tiled Braille, `neuronte-ascii-groups-v1`, `neuronte-symbol-v1`, `neuronte-pixel-groups-v1` and `neuronte-accent-groups-v1`; the pixel and accent groups failed their declared strict gates and were chosen by visual review; not a default; [recipe, checks and speed](weights/neuronte-split-v8.md) | 1,176, over twenty-one nets and a router | 6, 32, 64, 128, 192 and 256 | 699,511 | 2,805,688 bytes |
| `neuronte-split-v9` | split-v8 with 165 terminal characters added on fourteen group nets: 113 symbols (✓ ✗, arrows, ± ≤ ≥ ≠, € £ ¥ ₽ ₴, super- and subscripts, maths and keyboard signs) in `neuronte-tsymbol-v1`, 20 Greek letters with tonos in `neuronte-tgreek-v1`, 32 Cyrillic letters beyond Russian in `neuronte-tcyrillic-v1`; every group failed its declared gates and was chosen by visual review; not a default; [recipe, checks and speed](weights/neuronte-split-v9.md) | 1,341, over thirty-five nets and a router | 6, 32, 64, 128, 192 and 256 | 898,437 | 3,607,088 bytes |
| `neuronte-term-latin-v1` | 596 letters with marks that split-v9 was not trained on, alone in a standalone bundle to open beside split-v9: Vietnamese, Latin letters with one or two marks above or a mark below, polytonic Greek, Cyrillic with breve, diaeresis or macron; 71 of its 74 group nets failed their declared gates and were shipped by the owner's choice after review; not a default; [recipe, checks and speed](weights/neuronte-term-latin-v1.md) | 596, over 74 group nets, a table and a blank net | 64 and 96 | 1,065,306 in the group nets | 4,280,128 bytes |
| `neuronte-term-mathalpha-v1` | 179 styled letters and digits of Mathematical Alphanumeric Symbols that split-v9 was not trained on: the sans-serif, monospace and double-struck alphabets and digits; alone in a standalone bundle to open beside split-v9; every group net passed the common gates (gates-v2.3) with both seeds; not a default; [recipe, checks and speed](weights/neuronte-term-mathalpha-v1.md) | 179, over 17 group nets, a table and a blank net | 64 | 241,689 in the group nets | 971,056 bytes |
| `neuronte-term-syllabics-v1` | 168 Canadian syllabics made by rule: the vowels and the p, t, k, c, m and n series with their long and w forms and finals; the other 236 syllabics of the list were not drawn; alone in a standalone bundle to open beside split-v9; every group net passed the common gates (gates-v2.3) with both seeds; not a default; [recipe, checks and speed](weights/neuronte-term-syllabics-v1.md) | 168, over 15 group nets, a table and a blank net | 64 | 213,255 in the group nets | 856,824 bytes |
| `neuronte-term-scripts-v1` | 48 characters of the Lisu alphabet: Latin capitals, fifteen of them turned, and its marks; Ogham, Old Italic and parts of Tifinagh and Armenian are drawn in the font file and held back by the owner's word; alone in a standalone bundle to open beside split-v9; every group net passed the common gates (gates-v2.3) with both seeds; not a default; [recipe, checks and speed](weights/neuronte-term-scripts-v1.md) | 48, over 6 group nets, a table and a blank net | 64 | 85,302 in the group nets | 343,188 bytes |
| `neuronte-term-math-v1` | 465 arrows and mathematical operators that split-v9 was not trained on: the rest of Arrows and Mathematical Operators, long and supplemental arrows, mathematical brackets and the large and supplemental operators DejaVu Sans Mono covers, alone in a standalone bundle to open beside split-v9; 23 of its 47 group nets failed their declared gates and were shipped by the owner's choice after review; not a default; [recipe, checks and speed](weights/neuronte-term-math-v1.md) | 465, over 47 group nets, a table and a blank net | 64 | 667,823 in the group nets | 2,686,120 bytes |
| `neuronte-term-symbol-v1` | 480 punctuation marks, superscripts and subscripts, currency signs, letterlike symbols, number forms, technical symbols, enclosed digits and geometric shapes that split-v9 was not trained on, alone in a standalone bundle to open beside split-v9; 28 of its 48 group nets failed their declared gates and were shipped by the owner's choice after review; not a default; [recipe, checks and speed](weights/neuronte-term-symbol-v1.md) | 480, over 48 group nets, a table and a blank net | 64 | 682,032 in the group nets | 2,743,740 bytes |
| `neuronte-term-dingbat-v1` | 323 Miscellaneous Symbols and Dingbats that split-v9 was not trained on: weather, planets and zodiac, chess, cards and dice, music, stars, crosses, hands, pencils, scissors, circled digits and arrows, alone in a standalone bundle to open beside split-v9; 24 of its 35 group nets failed their declared gates and were shipped by the owner's choice after review; not a default; [recipe, checks and speed](weights/neuronte-term-dingbat-v1.md) | 323, over 35 group nets, a table and a blank net | 64 | 497,315 in the group nets | 2,000,188 bytes |
| `neuronte-term-blocks-v1` | 310 characters of four blocks made by rule, alone in a standalone bundle to open beside split-v9: the 64 Yijing hexagrams, the 87 Tai Xuan Jing figures, 100 domino tiles and 59 playing cards (dominoes and cards drawn to fill one cell); five tiled nets and one group net, each passing the common gates with both seeds as amended while it trained (gates-v2.3; three of the six pass only under the last amendment); not a default; [recipe, checks and speed](weights/neuronte-term-blocks-v1.md) | 310, over five tiled nets (16 tile nets), one group net, a table and a blank net | 32, 64 and 128 | 211,353 in the 17 nets | 849,696 bytes |
| `neuronte-term-letters-v1` | 812 more letters of Latin, Greek and Cyrillic that neither split-v9 nor term-latin-v1 was trained on, alone in a standalone bundle to open beside them: the rest of Latin Extended-B, IPA and phonetic letters, small capitals, modifier letters and tone bars, Latin Extended-C and -D, Coptic and old Greek letters, the rest of Cyrillic; every group net in it passed the shared gates with both seeds; one half failed again and its 4 characters (U+1DB4 to U+1DB7) are left out; not a default; [recipe, checks and speed](weights/neuronte-term-letters-v1.md) | 812, over 103 group nets, a table and a blank net | 64 | 1,464,351 in the group nets | 5,882,132 bytes |
| `neuronte-term-rest-v1` | 197 characters that split-v9 was not trained on, alone in a standalone bundle to open beside split-v9: the Hebrew letters and their pointed and wide presentation forms, Hebrew punctuation, Lao letters and the vowel signs that stand alone, the Thai baht sign, and the faces, animal faces and moon phases of Emoticons and Miscellaneous Symbols and Pictographs in one colour, one cell each; every group net passed gates v2.3 with both seeds (one group as two halves); the Lao letters are drawn from memory and unchecked by a reader of Lao; not a default; [recipe, checks and speed](weights/neuronte-term-rest-v1.md) | 197, over 26 group nets, a table and a blank net | 64 | 369,642 in the group nets | 1,484,956 bytes |
| `neuronte-kilix-chrome-v1` | The 39 symbols the Kilix terminal prints on its own bars, alone in a standalone bundle: a ringing bell, title bar buttons, widget symbols, a battery at ten levels and seven weather symbols, most at private-use code points used only as numbers, each drawn for this project from what it means on the bar; every group net passed gates v2.3 with both seeds; not a default; [recipe and checks](weights/neuronte-kilix-chrome-v1.md) | 39, over 6 group nets, a table and a blank net | 64 | 85,302 in the group nets | 343,224 bytes |
| `neuronte-kilix-chrome-v2` | The same symbols and the sun and the cloud drawn again for the box of two cells that Kilix gives a symbol with a blank cell after it (40 of them; the ringing bell stays one cell), with pens of 1/9 of the box, in a standalone bundle of its own; a program asks for a box W×H as the cell W×2H and averages each pair of rows; every net in it passed gates v2.3 with both seeds, 4 of the 6 groups as trained and 2 after being halved once; not a default; [recipe and checks](weights/neuronte-kilix-chrome-v2.md) | 41, over 8 group nets, a table and a blank net | 64 | 113,736 in the group nets | 457,336 bytes |
| `neuronte-wide-forms-v1` | The 103 fullwidth forms (U+FF01..FF60, U+FFE0..FFE6), drawn for the box of two cells a terminal gives a wide character (East Asian Width W or F), with pens of 1/9 of the box, in a standalone bundle of its own; a program asks for a box W×H as the cell W×2H and averages each pair of rows; every net in it passed gates v2.3 with both seeds (10 of 11 groups as trained, 1 after being halved once); all 103 in; not a default; [recipe and checks](weights/neuronte-wide-forms-v1.md) | 103, over 12 group nets, a table and a blank net | 64 | 170,604 in the group nets | 685,308 bytes |
| `neuronte-wide-symbols-v1` | Wide signs below U+1F300, game tiles, enclosed and squared signs, emoticons, transport and map symbols, large coloured shapes (colour twins drawn alike, by the owner's choice), drawn for the box of two cells a terminal gives a wide character (East Asian Width W or F), with pens of 1/9 of the box, in a standalone bundle of its own; a program asks for a box W×H as the cell W×2H and averages each pair of rows; **29 of its 73 nets FAILED gates v2.3** and are in by the owner's word (the failed halves within 25% of their limits, marked on the card); the other 44 passed with both seeds; 42 of the 324 drawn are left out, their nets having missed by more than 25%; not a default; [recipe and checks](weights/neuronte-wide-symbols-v1.md) | 282, over 73 group nets, a table and a blank net | 64 | 1,037,841 in the group nets | 4,166,204 bytes |
| `neuronte-wide-pictographs-v1` | The first half of the wide characters of Miscellaneous Symbols and Pictographs, U+1F300..1F448 (colour twins drawn alike; the second half is `neuronte-wide-pictographs2-v1`: one bundle holds at most 127 group nets), drawn for the box of two cells a terminal gives a wide character (East Asian Width W or F), with pens of 1/9 of the box, in a standalone bundle of its own; a program asks for a box W×H as the cell W×2H and averages each pair of rows; **27 of its 78 nets FAILED gates v2.3** and are in by the owner's word (the failed halves within 25% of their limits, marked on the card); the other 51 passed with both seeds; 6 of the 279 drawn are left out, their nets having missed by more than 25%; not a default; [recipe and checks](weights/neuronte-wide-pictographs-v1.md) | 273, over 78 group nets, a table and a blank net | 64 | 1,108,926 in the group nets | 4,451,088 bytes |
| `neuronte-wide-pictographs2-v1` | The second half of the wide characters of Miscellaneous Symbols and Pictographs, U+1F449..1F5FF (colour twins drawn alike; split from `neuronte-wide-pictographs-v1` because one bundle holds at most 127 group nets), drawn for the box of two cells a terminal gives a wide character (East Asian Width W or F), with pens of 1/9 of the box, in a standalone bundle of its own; a program asks for a box W×H as the cell W×2H and averages each pair of rows; **16 of its 68 nets FAILED gates v2.3** and are in by the owner's word (the failed halves within 25% of their limits, marked on the card); the other 52 passed with both seeds; 14 of the 280 drawn are left out, their nets having missed by more than 25%; not a default; [recipe and checks](weights/neuronte-wide-pictographs2-v1.md) | 266, over 68 group nets, a table and a blank net | 64 | 966,756 in the group nets | 3,880,504 bytes |
| `neuronte-wide-supplement-v1` | The wide characters of Supplemental Symbols and Pictographs and Symbols and Pictographs Extended-A (colour twins drawn alike), drawn for the box of two cells a terminal gives a wide character (East Asian Width W or F), with pens of 1/9 of the box, in a standalone bundle of its own; a program asks for a box W×H as the cell W×2H and averages each pair of rows; **23 of its 91 nets FAILED gates v2.3** and are in by the owner's word (the failed halves within 25% of their limits, marked on the card); the other 68 passed with both seeds; 12 of the 349 drawn are left out, their nets having missed by more than 25%; not a default; [recipe and checks](weights/neuronte-wide-supplement-v1.md) | 337, over 91 group nets, a table and a blank net | 64 | 1,293,747 in the group nets | 5,192,780 bytes |
| `neuronte-split-v4` | the default before Greek and Russian, kept; most measurements below were made on it | 1,061, over six nets and a router | 48, 128 and 192 | 329,356 | 1,319,616 bytes |
| `neuronte-full-v3` | explicit RC9 monolithic font; [quality and baseline comparison](weights/neuronte-full-v3.md) | 878, including the Greek and Russian additions | 384 | 331,009 | 1,324,240 bytes |
| `neuronte-full-v2` | the baseline `split` is measured against | 763 of them in one net, all but the sextants and octants | 320 | 234,881 | 939,728 bytes |
| `neuronte-ascii-v0` | the original ASCII expert | the 95 printable ASCII characters | 128 | 44,801 | 179,408 bytes |
| `neuronte-ascii-groups-v1` | ASCII character groups; [recipe and validation](weights/neuronte-ascii-next.md) | the 95 printable ASCII characters | 4×64 | 56,836 | 228,252 bytes |
| `neuronte-ascii-spatial-v1` | compact ASCII spatial halves; [recipe and validation](weights/neuronte-ascii-next.md) | the 95 printable ASCII characters | 2×64 | 28,418 | 114,172 bytes |
| `neuronte-pixel-groups-v1` | pixel character groups, seed 1; failed the declared strict geometry gates; [recipe, validation and exceptions](weights/neuronte-pixel-groups-v1.md) | the 327 block, sextant and octant characters | 4×64 | 56,836 | 228,372 bytes |
| `neuronte-accent-groups-v1` | accent script groups, seed 0; failed the declared strict gates; [recipe, validation and exceptions](weights/neuronte-accent-groups-v1.md) | the 318 accented Latin, spacing-mark, Greek and Russian characters | 192, 128 and 128 | 181,379 | 726,336 bytes |
| `neuronte-ui1-v0`, `neuronte-ui2-v0`, `neuronte-ui3-v0`, `neuronte-ui4-v0`, `neuronte-ui5-v0`, `neuronte-ui6-v0`, `neuronte-ui7-v0` | the desktop face at an em of 1, 2, 3, 4, 5, 6 and 7 pixels | printable ASCII and the ellipsis, 96, with their advances | 96 | 27,457 | 110,864 bytes each |
| `neuronte-ui8-v0`, `neuronte-ui9-v0`, `neuronte-ui10-v0`, `neuronte-ui11-v0` | the desktop face: proportional binary text at an em of 8, 9, 10 and 11 pixels | printable ASCII and the ellipsis, 96, with their advances | 96 | 27,457 | 110,864 bytes each |
| `neuronte-ui12-v0`, `neuronte-ui14-v0` | the desktop face at an em of 12 pixels and of 14 | printable ASCII and the ellipsis, 96, with their advances | 128 | 44,801 | 180,240 bytes each |
| `neuronte-ui13-v0`, `neuronte-ui15-v0` | the desktop face at an em of 13 pixels and of 15 | printable ASCII and the ellipsis, 96, with their advances | 128 | 44,801 | 180,240 bytes each |
| `neuronte-ui16-v0`, `neuronte-ui18-v0`, `neuronte-ui22-v0`, `neuronte-ui26-v0` | the desktop face at an em of 16, 18, 22 and 26 pixels | printable ASCII and the ellipsis, 96, with their advances | 192 | 91,777 | 368,144 bytes each |
| `neuronte-ui23-v0`, `neuronte-ui25-v0` | the desktop face at an em of 23 pixels and of 25 | printable ASCII and the ellipsis, 96, with their advances | 192 | 91,777 | 368,144 bytes each |
| `neuronte-ui17-v0` | the desktop face at an em of 17 pixels | printable ASCII and the ellipsis, 96, with their advances | 256 | 155,137 | 621,584 bytes |
| `neuronte-ui19-v0`, `neuronte-ui20-v0`, `neuronte-ui21-v0` | the desktop face at an em of 19, 20 and 21 pixels | printable ASCII and the ellipsis, 96, with their advances | 160 | 66,241 | 266,000 bytes each |
| `neuronte-ui1-v1`, `neuronte-ui2-v1`, `neuronte-ui3-v1`, `neuronte-ui4-v1`, `neuronte-ui5-v1`, `neuronte-ui6-v1`, `neuronte-ui7-v1`, `neuronte-ui8-v1`, `neuronte-ui9-v1`, `neuronte-ui10-v1`, `neuronte-ui11-v1`, `neuronte-ui12-v1`, `neuronte-ui13-v1`, `neuronte-ui14-v1`, `neuronte-ui15-v1`, `neuronte-ui19-v1`, `neuronte-ui20-v1`, `neuronte-ui21-v1`, `neuronte-ui3-italic-v1`, `neuronte-ui4-italic-v1`, `neuronte-ui5-italic-v1`, `neuronte-ui6-italic-v1`, `neuronte-ui7-italic-v1`, `neuronte-ui8-italic-v1`, `neuronte-ui9-italic-v1`, `neuronte-ui10-italic-v1`, `neuronte-ui11-italic-v1`, `neuronte-ui12-italic-v1`, `neuronte-ui14-italic-v1`, `neuronte-ui15-italic-v1` | the same faces as their v0, every character exactly the same pixels, drawn 4 to 30 times faster: each a drawing file of one bundle of 32 or 96 small nets, each drawing only the em rows of its own characters (one such net at 1 and 2 px); v0 is unchanged and still the default; [recipe and speed](weights/neuronte-ui-v1-small.md) | printable ASCII and the ellipsis, 96, with their advances | 16 per net (20 for ui12, ui12-italic, ui15 and ui19; 24 for ui21) | 2,017 to 257,376 | 9,788 to 1,119,068 bytes |
| `neuronte-ui24-v0`, `neuronte-ui27-v0`, `neuronte-ui28-v0`, `neuronte-ui29-v0`, `neuronte-ui30-v0` | the desktop face at an em of 24, 27, 28, 29 and 30 pixels | printable ASCII and the ellipsis, 96, with their advances | 384 | 331,009 | 1,325,072 bytes each |
| `neuronte-ui31-v0`, `neuronte-ui33-v0`, `neuronte-ui34-v0`, `neuronte-ui35-v0`, `neuronte-ui36-v0`, `neuronte-ui37-v0`, `neuronte-ui38-v0`, `neuronte-ui39-v0`, `neuronte-ui43-v0` | the desktop face at an em of 31, 33, 34, 35, 36, 37, 38, 39 and 43 pixels | printable ASCII and the ellipsis, 96, with their advances | 512 | 572,417 | 2,290,704 bytes each |
| `neuronte-ui33-v1`, `neuronte-ui34-v1`, `neuronte-ui35-v1`, `neuronte-ui36-v1`, `neuronte-ui37-v1`, `neuronte-ui38-v1`, `neuronte-ui39-v1`, `neuronte-ui43-v1` | the same faces as their v0, every character exactly the same pixels, drawn 32 to 48 times faster: each a drawing file of one bundle of 32 (16 for ui33, ui36 and ui37) small nets, each drawing only the em rows of its own characters (`weights/neuronte-ui-v1-h512.md`) | printable ASCII and the ellipsis, 96, with their advances | 48 (64 for ui33, ui36 and ui37) per net | 227,344 to 291,872 | 925,032 to 1,197,928 bytes |
| `neuronte-ui32-v0` | the desktop face at an em of 32 pixels | printable ASCII and the ellipsis, 96, with their advances | 768 | 1,251,841 | 5,008,400 bytes |
| `neuronte-ui10-italic-v0`, `neuronte-ui11-italic-v0` | the italic of that face at 10 and 11 pixels | printable ASCII and the ellipsis, 96, with their advances | 96 | 27,457 | 110,864 bytes each |
| `neuronte-ui12-italic-v0`, `neuronte-ui14-italic-v0` | the italic at 12 and 14 pixels | printable ASCII and the ellipsis, 96, with their advances | 128 | 44,801 | 180,240 bytes each |
| `neuronte-ui16-italic-v0`, `neuronte-ui18-italic-v0`, `neuronte-ui20-italic-v0` | the italic at 16, 18 and 20 pixels | printable ASCII and the ellipsis, 96, with their advances | 192 | 91,777 | 368,144 bytes each |
| `neuronte-ui22-italic-v0`, `neuronte-ui26-italic-v0` | the italic at 22 and 26 pixels | printable ASCII and the ellipsis, 96, with their advances | 256 | 155,137 | 621,584 bytes each |
| `neuronte-ui24-italic-v0`, `neuronte-ui30-italic-v0` | the italic at 24 and 30 pixels | printable ASCII and the ellipsis, 96, with their advances | 384 | 331,009 | 1,325,072 bytes each |
| `neuronte-ui-large-v0` | the desktop face at every em from 33 pixels up, drawn blended | printable ASCII and the ellipsis, 96, with their advances | 384 | 331,009 | 1,325,072 bytes |
| `neuronte-ui-scaled-v0` | the desktop face at every em from 17 to 32 pixels from one file, chosen by the owner in place of the hand faces there (1 to 16 px stay hand faces): the ui-large strokes scaled to the em by a bundle of 16 small nets, its stems snapped to whole pixels by a letter edge table, which a library older than the table refuses; a different face from the hand-drawn ones, not a copy of them; italic by the library's draw-time italic with the advances in `neuronte-ui-scaled-italic-advances-v0`; `neuronte-ui-scaled-latin1-v0` adds the Latin-1 letters; no default changes; [recipe, quality and speed](weights/neuronte-ui-scaled-v0.md) | printable ASCII and the ellipsis, 96, with advances fitted to the hand faces from 17 to 32 px | 96 | 439,312 | 1,774,948 bytes |
| `neuronte-ui-large-v1` | the same face as `neuronte-ui-large-v0` from 33 px up, with its advances, from a bundle of 4 nets 192 wide: whole-face first use about 12 times faster; negative under its declared overlap gate (32 px, and the minimum at 48 and 96 px) and shipped by the owner's decision; `neuronte-ui-large-latin1-v1` adds the Latin-1 letters; v0 is unchanged and still the default; [gate, speed and recipe](weights/neuronte-ui-large-v1.md) | printable ASCII and the ellipsis, 96, with their advances | 192 | 367,108 | 1,473,000 bytes |
| `neuronte-ui-scaled-latin1-v0`, `neuronte-ui-large-latin1-v1` | `neuronte-ui-scaled-v0` and `neuronte-ui-large-v1` with the 58 Latin-1 letters ui-large composes from its letters and `font/marks.txt`, drawn by two more nets 192 wide (`neuronte-ui-latin1-v0-gG.json`); the ASCII letters draw byte for byte as in the ASCII-only files; italic advances in `neuronte-ui-scaled-latin1-italic-advances-v0`; [Latin-1](weights/neuronte-ui-scaled-v0.md#latin-1-neuronte-ui-scaled-latin1-v0) | printable ASCII, the ellipsis and the Latin-1 letters, 154, with their advances | 96 and 192; 192 | 622,866; 550,662 | 2,512,896; 2,209,684 bytes |
| `neuronte-ui24-v1`, `neuronte-ui24-italic-v1`, `neuronte-ui27-v1`, `neuronte-ui28-v1`, `neuronte-ui28-italic-v1`, `neuronte-ui29-v1`, `neuronte-ui29-italic-v1`, `neuronte-ui30-v1`, `neuronte-ui30-italic-v1` | the same faces as their v0, every character exactly the same pixels, drawn 12 to 30 times faster: each a drawing file of one bundle of 16 (8 for ui30-italic) small nets, each drawing only the em rows of its own characters (`weights/neuronte-ui-v1.md`) | printable ASCII and the ellipsis, 96, with their advances | 48 (64 for ui28-italic and ui30, 96 for ui30-italic) per net | 145,936 to 227,344 | 599,400 to 925,032 bytes |
| `neuronte-flame-v0` | the Kilix flame, for the Start button at 16 px and the desktop icon at 32: a colour net, version 3, of three layers | one mark, at U+100000; the printable ASCII and U+FFFD draw nothing | 64 | 16,914 | 68,124 bytes |
| `neuronte-flame-v1` | the flame of `neuronte-flame-v0`, narrower and faster, drawn the same way; see its card | one mark, at U+100000; the printable ASCII and U+FFFD draw nothing | 56 | 14,226 | 57,372 bytes |
| `neuronte-icon-v1` | the icons in colour, a version 3 file by itself, not in the bundle | 167: the 133 in `font/icons.txt` and 34 powerline and progress glyphs, up to 6 layers each | 256 | 159,492 | 650,216 bytes |
| `neuronte-icon-v2` | the icons of `neuronte-icon-v1` as a version 2 bundle of four version 3 nets, each for a contiguous run of the icons, about four times faster; see its card | the same 167, up to 3 layers each | 96 | 120,904 | 496,184 bytes |
| `neuronte-pointer-v1` | the NW mouse pointer of `neuronte-pointer-v0`, narrower and faster, with the same sizes (16x32 and 32x64) and hotspots; see its card | one mark, at U+100001; other scalars are not guaranteed blank | 48 | 10,380 | 41,984 bytes |
| `neuronte-ui28-italic-v0` | the italic at 28 pixels, trained for 40,000 steps: at the default 20,000 no width from 384 to 768 had both seeds exact | printable ASCII and the ellipsis, 96, with their advances | 384 | 331,009 | 1,325,072 bytes |
| `neuronte-ui32-italic-v0` | the italic at 32 pixels, trained for 40,000 steps; both seeds exact at width 512 | printable ASCII and the ellipsis, 96, with their advances | 512 | 572,417 | 2,290,704 bytes |
| `neuronte-ui13-italic-v1` | narrower v1 of the desktop face at 13 px italic, trained 40,000 steps, both seeds exact; v0 is unchanged and still the default; [recipe and speed](weights/neuronte-ui-v1-192-256.md) | printable ASCII and the ellipsis, 96, with their advances | 96 | 27,457 | 110,864 bytes |
| `neuronte-ui16-italic-v1`, `neuronte-ui18-v1` | narrower v1 of the desktop faces at 16 px italic and 18 px, trained 80,000 steps, both seeds exact; v0 is unchanged and still the default; [recipe and speed](weights/neuronte-ui-v1-192-256.md) | printable ASCII and the ellipsis, 96, with their advances | 96 | 27,457 | 110,864 bytes each |
| `neuronte-ui16-v1`, `neuronte-ui19-italic-v1` | narrower v1 of the desktop faces at 16 px and 19 px italic, trained 40,000 steps, both seeds exact; v0 is unchanged and still the default; [recipe and speed](weights/neuronte-ui-v1-192-256.md) | printable ASCII and the ellipsis, 96, with their advances | 128 | 44,801 | 180,240 bytes each |
| `neuronte-ui17-v1`, `neuronte-ui17-italic-v1`, `neuronte-ui18-italic-v1`, `neuronte-ui20-italic-v1`, `neuronte-ui21-italic-v1`, `neuronte-ui22-v1`, `neuronte-ui23-v1`, `neuronte-ui26-v1` | narrower v1 of the desktop faces at 17 px, 17 px italic, 18 px italic, 20 px italic, 21 px italic, 22 px, 23 px and 26 px, trained 80,000 steps, both seeds exact; v0 is unchanged and still the default; [recipe and speed](weights/neuronte-ui-v1-192-256.md) | printable ASCII and the ellipsis, 96, with their advances | 128 | 44,801 | 180,240 bytes each |
| `neuronte-ui23-italic-v1`, `neuronte-ui25-v1` | narrower v1 of the desktop faces at 23 px italic and 25 px, trained 40,000 steps, both seeds exact; v0 is unchanged and still the default; [recipe and speed](weights/neuronte-ui-v1-192-256.md) | printable ASCII and the ellipsis, 96, with their advances | 160 | 66,241 | 266,000 bytes each |
| `neuronte-ui22-italic-v1`, `neuronte-ui25-italic-v1`, `neuronte-ui26-italic-v1` | narrower v1 of the desktop faces at 22 px italic, 25 px italic and 26 px italic, trained 80,000 steps, both seeds exact; v0 is unchanged and still the default; [recipe and speed](weights/neuronte-ui-v1-192-256.md) | printable ASCII and the ellipsis, 96, with their advances | 160 | 66,241 | 266,000 bytes each |
| `neuronte-ui32-v1`, `neuronte-ui27-italic-v1`, `neuronte-ui31-v1` | faster v1 of the desktop faces at 32 px, 27 px italic and 31 px: one bundle of 8 nets, one per group of 12 characters, trained 40,000 steps, both seeds exact; v0 is unchanged and still the default; [recipe and speed](weights/neuronte-ui-wide-v1.md) | printable ASCII and the ellipsis, 96, with their advances | 8 × 96 | 219,656 | 881,256 bytes each |
| `neuronte-ui31-italic-v1`, `neuronte-ui32-italic-v1` | faster v1 of the desktop faces at 31 px italic and 32 px italic: one bundle of 8 nets, one per group of 12 characters, trained 40,000 steps, both seeds exact; v0 is unchanged and still the default; [recipe and speed](weights/neuronte-ui-wide-v1.md) | printable ASCII and the ellipsis, 96, with their advances | 8 × 128 | 358,408 | 1,436,264 bytes each |

`neuronte-split-v5.nrt` is the default: 1,176 labelled scalars, including
49 Greek and 66 Russian letters, in a 1,573,128-byte bundle. It differs from
split-v4 only in its accent net and gate; every character the other five nets
draw comes out pixel for pixel the same. Its accent-v2 expert passes
both-seed script gates and root visual review. Latin mean IoU at 16 px
changes from .984936529 to .984822170, and individual letters regress at
every size; the per-glyph changes are retained. An accented, Greek or
Russian cell costs about 1.6 times what it did, because that net is 256 wide.
split-v4 and the full-v2 baseline are kept and still checked by `make test`.
See [the recipe and validation](weights/neuronte-split-v5.md).

`neuronte-split-v6.nrt` is split-v5 with one part replaced: its Braille net
is `neuronte-braille-v1`, a version 6 tiled net in which one net 6 wide
draws all eight dots, 637 parameters in place of 9,121. The other five nets,
the gate and the ranges are byte for byte split-v5's, so every other
character comes out the same. All 256 patterns are exact at 8 x 16, 16 x 32
and 48 x 96, and uncached Braille coverage is 4.5 to 21 times faster than
split-v5's on two x86 hosts and 11 to 40 times on an ARM board, least at
25 x 49. Its antialiasing is not better everywhere: mean coverage error is
higher at 48 x 96. The video player's full mode draws with split-v6; its
learned helpers are bound to split-v5, which stays. See
[the recipe and validation](weights/neuronte-braille-v1.md).

`neuronte-split-v7.nrt` is split-v6 with the four ASCII character-group
nets of `neuronte-ascii-groups-v1` added by `train/known_bundle.py`. split-v6's
members, unknown-character routing and non-ASCII pixels are unchanged, and
its ASCII pixels are the qualified group nets'. Measured as a whole bundle on
two x86 CPUs, it draws uncached ASCII about 2.2 times as fast as split-v6 and
Braille as fast, and takes 0.1 to 0.3 ms longer to open. It is not a default
yet. See [its recipe, checks and speed](weights/neuronte-split-v7.md).

`neuronte-split-v7-symbol-v1.nrt` is split-v7 with the four width-32 symbol
group nets of `neuronte-symbol-v1` added the same way. split-v7's members,
routing and every non-symbol pixel are unchanged; the 49 symbols draw exactly
as in `neuronte-split-v5-symbol-v1`, whose uncached symbol coverage measured
5–6× faster than split-v5 on two x86-64 hosts. It is not a default. See
[its recipe and checks](weights/neuronte-split-v7-symbol-v1.md).

`neuronte-split-v8.nrt` is split-v7 with three more sets of group nets added
the same way, one `train/known_bundle.py` step each: the symbol groups of
`neuronte-symbol-v1`, the pixel groups of `neuronte-pixel-groups-v1` and the
accent script groups of `neuronte-accent-groups-v1`. split-v7's ten members,
unknown-character routing, ASCII and Braille are unchanged; each replaced
character draws exactly as in the bundle it was reviewed in. The symbol groups
passed their gates. The pixel and accent groups failed their declared strict
gates at some sizes and were chosen after a visual review of the regressions,
which their cards list. Measured as a whole bundle on two x86 CPUs, it draws
uncached symbols about 5.5 times as fast as split-v7, pixel characters 2.1
times and accent characters 1.95 times; ASCII and Braille cost the same, and
it takes about 1 ms longer to open. It is not a default. Rebuild it with
`make pack-split-v8`; see [its recipe, checks and speed](weights/neuronte-split-v8.md).

`neuronte-split-v9.nrt` is split-v8 with 165 characters that terminals print
often and no earlier bundle was trained on: check and cross marks, arrows,
shapes, comparison and currency signs, super- and subscripts, fractions,
punctuation, maths and keyboard symbols, Greek letters with tonos, and the
Cyrillic letters of Ukrainian, Belarusian, Serbian, Macedonian and
Bulgarian. split-v8 sent them through its gate to nets that had never seen
them, so ✓ came out as a small arrow. Each now has a table row to a net trained
on it (`train/known_bundle.py`'s `add_known`); split-v8's members, rows and
gate are kept, so its 1,176 characters and every untrained character draw
exactly as before. Every group failed its declared gates, mostly on mean
error at 8×16, binary IoU and identity in the smallest cells, and was chosen
after a side-by-side review; the card lists the failures and the small-cell
limits. On two x86 CPUs it draws the added characters about 4.6 times as fast
as split-v8, and takes about 0.5 to 0.9 ms longer to open. It is not a
default; to use it, load it instead of split-v8 or split-v5, and nothing else
changes. Rebuild it with `make pack-split-v9`; see
[its recipe, checks and speed](weights/neuronte-split-v9.md).

`neuronte-term-latin-v1.nrt` is a bundle of its own for 596 letters with marks that
split-v9 has the letter for but was never trained on: the Vietnamese
letters, Latin letters with one or two marks above or a mark below,
polytonic Greek, and Cyrillic letters with a breve, diaeresis or macron.
Each is composed from a letter split-v9 already draws and one to three marks
of `font/marks.txt`; `font/term-latin.txt` lists them. It holds no copy of
split-v9. A program opens both files and draws a character with this one
when `neuronte_untrained()` says it was trained on it, and with split-v9
otherwise; a scalar outside its list draws blank through it and is reported
untrained (`train/standalone_bundle.py`). 3 of its 74 group nets passed
the gates declared before training; the others failed, about half the
misses on binary overlap and most of the rest on the one-sample rules,
also on the one declared retry at width 96, and were shipped at width 64 by the owner's choice after a side-by-side review. On a rented AMD EPYC 7B13 it draws these characters
about 3.1 times as fast as split-v9's fallback does. It is not a default.
Rebuild it with `make pack-term-latin-v1`; see
[its recipe, checks and speed](weights/neuronte-term-latin-v1.md).

`neuronte-term-mathalpha-v1.nrt` is a bundle of its own for 179 characters no earlier bundle was
trained on: the sans-serif, monospace and double-struck letters and digits of Mathematical Alphanumeric Symbols. Monospace is this face's own ASCII strokes, sans-serif the same but for six characters, and the double-struck ones are drawn by hand; `font/term-scripts.txt` lists them. It holds no
copy of split-v9 and is opened beside it, as `neuronte-term-latin-v1.nrt` is.
The common gates of the coverage phases judged it automatically: every group net passed the common gates (gates-v2.3) with both seeds. On an Intel Core i7-6820HQ and an Intel Core i7-10700F it draws these characters about 2.6 times as fast as split-v9's fallback does.
It is not a default. Rebuild it with `make pack-term-mathalpha-v1`; see
[its recipe, checks and speed](weights/neuronte-term-mathalpha-v1.md).

`neuronte-term-syllabics-v1.nrt` is a bundle of its own for 168 characters no earlier bundle was
trained on: Canadian syllabics: the vowels and the p, t, k, c, m and n series, each a shape turned four ways with dots for a long vowel and for w, and their finals, made by `train/term_scripts.py`. The other 236 syllabics DejaVu Sans Mono has were not drawn (their shapes were not known well enough) and stay untrained; `font/term-scripts.txt` lists them. It holds no
copy of split-v9 and is opened beside it, as `neuronte-term-latin-v1.nrt` is.
The common gates of the coverage phases judged it automatically: every group net passed the common gates (gates-v2.3) with both seeds. On an Intel Core i7-6820HQ and an Intel Core i7-10700F it draws these characters about 2.4 times as fast as split-v9's fallback does.
It is not a default. Rebuild it with `make pack-term-syllabics-v1`; see
[its recipe, checks and speed](weights/neuronte-term-syllabics-v1.md).

`neuronte-term-scripts-v1.nrt` is a bundle of its own for 48 characters no earlier bundle was
trained on: the Lisu (Fraser) alphabet: Latin capitals of this face, fifteen of them turned half round, and eight marks. Ogham, Old Italic and parts of Tifinagh and Armenian (102 characters) are drawn in `font/term-scripts.txt` and held back by the owner's word; Georgian was not drawn; `font/term-scripts.txt` lists them. It holds no
copy of split-v9 and is opened beside it, as `neuronte-term-latin-v1.nrt` is.
The common gates of the coverage phases judged it automatically: every group net passed the common gates (gates-v2.3) with both seeds. On an Intel Core i7-6820HQ and an Intel Core i7-10700F it draws these characters about 2.5 times as fast as split-v9's fallback does.
It is not a default. Rebuild it with `make pack-term-scripts-v1`; see
[its recipe, checks and speed](weights/neuronte-term-scripts-v1.md).

`neuronte-term-math-v1.nrt`, `neuronte-term-symbol-v1.nrt` and
`neuronte-term-dingbat-v1.nrt` are three more bundles of that kind, for the
symbols DejaVu Sans Mono covers and split-v9 was not trained on: 465 arrows
and mathematical operators; 480 punctuation marks, superscripts and
subscripts, currency signs, letterlike symbols, number forms, technical
symbols and geometric shapes; and 323 Miscellaneous Symbols and Dingbats.
DejaVu gave only the list of code points. Every character is drawn in the
project's own strokes (`font/term-math.txt`, `font/term-sym.txt`,
`font/term-ding.txt`) or made from them by `train/term_glyphs.py`: turned,
mirrored, negated, stacked, filled or enclosed. The 21 characters of these
blocks that Unicode makes two cells wide are left out. Each bundle holds no
copy of split-v9 and is used beside it in the same way, and no character is in
two bundles. Of their 47, 48 and 35 group nets, 24, 20 and 11 passed the gates
declared before training. The others failed, every one on the amount of error
and none on which character is drawn, and are in the bundles at width 64 by
the owner's choice after seeing the nets beside their teachers; the one
declared retry at width 96 was run for the first bundle, where it rescued none
of 23 groups, and not for the other two. On an Intel i7-6820HQ and an
i7-10700F each draws its characters about 2.7 times as fast as split-v9's
fallback does (2.69 to 2.76 over the three bundles and both hosts). None is a
default. Rebuild them with `make pack-term-math-v1`, `make
pack-term-symbol-v1` and `make pack-term-dingbat-v1`; see the recipe, checks
and speed of [term-math-v1](weights/neuronte-term-math-v1.md),
[term-symbol-v1](weights/neuronte-term-symbol-v1.md) and
[term-dingbat-v1](weights/neuronte-term-dingbat-v1.md).

`neuronte-term-blocks-v1.nrt` is a bundle of its own for 310 characters of four
blocks whose every character is put together from a few parts by a rule: the 64
Yijing hexagrams, the Tai Xuan Jing monogram, digrams and tetragrams, the
domino tiles lying and standing, and the playing cards. `train/term_blocks.py`
makes each drawing from `font/term-blocks.txt`; no font was read. Dominoes and
cards are drawn to fill one cell, so they are narrower than Unicode shows them.
Five of its six members are tiled nets: the cell is cut into the block's own
grid (six rows for a hexagram, four for a tetragram, two halves for a tile or a
card) and each piece is drawn by its own small net from the character's own
scalar (`train/tile_expert.py`, `train/tile_member.py`). It holds no copy of
split-v9 and is used beside it as term-latin-v1 is. Every member passed the
common gates with both seeds as the owner amended them while it trained; three
of the six pass only because of the last amendment. Uncached, it draws these
characters 2.2 times as fast as split-v9's fallback does on both benchmark
hosts (240 against 490 µs a character at 8×16 on an Intel Core i7-6820HQ, 180
against 378 on an Intel Core i7-10700F); a warm draw at 48×96 is about one
eighth slower. It is not a default. Rebuild it with `make pack-term-blocks-v1`;
see [its recipe, checks and speed](weights/neuronte-term-blocks-v1.md).

`neuronte-term-letters-v1.nrt` is a bundle of its own for 812 more letters of the scripts
Neuronte already draws, none of them in split-v9 or term-latin-v1: the rest
of Latin Extended-B, the IPA and phonetic letters, small capitals, modifier
letters and tone bars, Latin Extended-C and -D, the Coptic and old Greek
letters, and the rest of Cyrillic. `font/term-letters.txt` holds a line for
each and `train/term_letters.py` makes the drawing, most of them from a
letter drawn before, turned, mirrored, made small, raised, or given a hook,
bar or tail; no font file was opened to make one. It holds no copy of
split-v9. A program opens the files side by side and draws a character with
the one whose `neuronte_untrained()` says it was trained on it, and with
split-v9 otherwise. Every one of its 103 group nets passed the project's
shared gates with both seeds; 2 of the 102 groups trained failed them and
were cut in two and trained once more, as declared before training; one half failed again and its 4 characters (U+1DB4 to U+1DB7) are left out.
On an Intel Core i7-6820HQ and an Intel Core i7-10700F it draws these characters about 4.2 times as fast as split-v9's fallback does. It is not a default.
Rebuild it with `make pack-term-letters-v1`; see
[its recipe, checks and speed](weights/neuronte-term-letters-v1.md).

`neuronte-term-rest-v1.nrt` is a bundle of its own for 197 characters no
earlier bundle was trained on: the Hebrew letters, the presentation forms
that are one letter's picture (a letter with a dagesh or another point, the
wide letters), Hebrew punctuation, the Lao letters and the Lao vowel signs
that stand alone, the Thai baht sign, and the faces, cat faces, animal
faces and eight moon phases of Emoticons and Miscellaneous Symbols and
Pictographs, each in one colour and one cell. `font/term-rest.txt` holds
the drawings and `train/term_rest.py` makes the pointed and wide letters,
the faces and the moons from parts. No font was read: the Lao letters are
drawn from memory of their general shape and should be checked by a reader
of Lao; the ten Lao digits and the Lao ellipsis are not drawn. Right-to-left
order is the terminal's work. It holds no copy of split-v9 and is used
beside it as `neuronte-term-latin-v1` is. All 26 of its group nets passed
gates v2.3 with both seeds, one group as two halves; the gates were amended
after the first scores, when a perfect drawing was shown to fail some of
their rules, and the card says how. On an Intel Core i7-6820HQ and an Intel
Core i7-10700F it draws these characters about 2.7 times as fast as
split-v9's fallback does. It is not a default and does not change the
colour emoji net. Rebuild it with `make pack-term-rest-v1`; see
[its recipe, checks and speed](weights/neuronte-term-rest-v1.md).

`neuronte-kilix-chrome-v1.nrt` holds the 39 symbols the Kilix terminal
prints on its own bars: the ringing bell of a pane's title bar, the title
bar's split arrows and its maximise, restore and close buttons, the symbols
of the top bar's widgets, a battery at ten levels with a problem mark and
an unknown mark, and seven weather symbols. Kilix prints most of them at
private-use code points; those are used only as numbers, and each symbol is
this project's own drawing from what it means on the bar
(`font/kilix-chrome.txt`, `train/kilix_chrome.py`). A program opens it
before the terminal bundles and draws a symbol with it when
`neuronte_untrained()` is 0; every other scalar, U+10FFFD among them, is
reported untrained. All six of its group nets passed gates v2.3 with both
seeds. Rebuild it with `make pack-kilix-chrome-v1`; see
[its recipe and checks](weights/neuronte-kilix-chrome-v1.md).

`neuronte-kilix-chrome-v2.nrt` draws the same code points, and the sun and
the cloud, for the box of two cells Kilix gives a symbol that has a blank
cell after it: 41 symbols, all but the ringing bell twice a cell wide, on a
grid of 18 by 18 with pens of 2 (`font/kilix-chrome-2.txt`,
`train/kilix_chrome2.py`). A program asks for a box W×H as the cell W×2H and
averages each pair of rows; asked as W×H, level edges come out wrong by half
a pixel. It shares its code points with v1 on purpose, so its list is
`neuronte-kilix-chrome-v2.symbols.txt` and not a `.list.txt`, and
`tests/check_kilix_chrome_v2.py` holds it to that list. Every net in it
passed gates v2.3 with both seeds, 4 of the 6 groups as trained and 2 after
being halved once. v1 stays for a symbol in one cell. Rebuild it with `make
pack-kilix-chrome-v2`; see [its recipe and
checks](weights/neuronte-kilix-chrome-v2.md).

The five `neuronte-wide-*-v1.nrt` bundles draw wide characters, those a
terminal gives two cells, for that box, the way `neuronte-kilix-chrome-v2`
does: forms, symbols, pictographs (two files, `neuronte-wide-pictographs-v1`
and `neuronte-wide-pictographs2-v1`, because one bundle holds at most 127
group nets) and supplement, 1,261 of the 1,335 drawn (`train/wide.py` and
its parts, from each character's Unicode name and the charts' words; no
font was opened). A program asks for a box W×H as the cell W×2H and
averages each pair of rows. Each list is a `NAME.symbols.txt`, not a
`.list.txt`, because some of these code points are also one-cell
characters of a terminal bundle; `tests/check_wide.py` holds each table to
its list and no character in two of the five. Gates v2.3, kind symbols,
both seeds: a failing group was halved once. Of the 120 halves that failed
again, the owner looked at each and shipped the 95 whose lower-error seed
misses by at most 25%; they are **marked FAILED** on the cards and in the
validation records. The other 25 are left out, so 74 drawn characters stay
untrained (listed on the cards). Characters Unicode tells apart only by
colour are drawn alike, by the owner's choice. Rebuild them with
`make pack-wide`.

RC9 also ships the separate `neuronte-emoji-v0.nrt` colour bundle: 300 original
single-scalar emoji, 600 left/right half labels, three experts, and up to six
layers with dark/light palettes. The 7,011,412-byte bundle is used through the
half APIs below; it does not add shaping or replace the default terminal font.
Both seeds pass the stated C gates, and the complete source/two-seed sheets
were reviewed at 16 and 32 px per cell. The [emoji recipe and quality report](weights/neuronte-emoji-v0.md)
record the calibration, exact sampling policy and lower overlap at some other
sizes. Joined sequences, flags and skin-tone sequences are outside this set.

The [v1 small desktop faces](weights/neuronte-ui-v1-small.md), 1 to 15 px and 19 to 21 px, and the
italics 3 to 12, 14 and 15 px, are new files beside their v0, with the same advances. Both seeds draw
all 96 glyphs, regular and bold, exactly as the drawings at the native em. They draw a whole face 4
to 30 times faster, the cost a desktop pays when it builds its letter cells; opening a 96-net file
takes 0.6 to 1.3 ms longer than its v0, and with the opening counted a face still builds 3 to 29
times faster. The installer and Kilix 95 still load v0.

`neuronte-emoji-v1.nrt` draws the same 300 emoji, with the same labels,
palettes and half API, from twelve 192-wide experts over a
difficulty-balanced partition (`font/emoji-partition-balanced-12.json`) in
place of three 512-wide ones. It is 4,785,292 bytes. Both seeds pass v0's
unchanged gates, and on two x86 CPUs it draws uncached emoji about five times
as fast as v0 on the same library build. It trades a little overlap at 12 and
32 px for 16 px, as v0's calibrated expert does. It is not a default. See
[its recipe, gates and speed](weights/neuronte-emoji-v1.md).

`neuronte-weather-colour-v1.nrt` draws nine weather symbols in colour for a
status bar: sun, sun with small cloud, sun behind cloud, cloud, fog, sun
behind rain cloud, cloud with rain, cloud with snow, and thunder cloud with
rain (`weights/neuronte-weather-colour-v1.symbols.txt`). Each is two cells,
drawn through the same half API and palette as the emoji, from one 192-wide
net behind a table of its nine scalars; every other scalar is untrained in
it. The drawings are the project's own (`train/weather.py`). It is 396,956
bytes. Both seeds pass the gates emoji-v1 was held to. It is not a default.
See [its drawings, gates and sizes](weights/neuronte-weather-colour-v1.md).

The [17 additional desktop italic faces](weights/neuronte-italic-v0.md) complete
native sizes 3–32 while preserving the 13 earlier faces. Both matching seeds
reproduce all 96 source glyphs and their regular/bold masks and advances exactly
at each native size. Tiny grids reuse some shapes; exact reproduction does not
imply distinct or readable letters at every size. Sizes 1/2 and scalable italic
remain explicit consumer fallback.

Narrower [v1 desktop faces](weights/neuronte-ui-v1-192-256.md) exist for the sizes whose v0 nets
are 192 or 256 wide. Each is a new file beside its v0, with the same advances, and both seeds
reproduce all 96 glyphs exactly at the native em. They draw a whole face faster, which is the
cost a desktop pays when it builds its letter cells. The installer and Kilix 95 still load v0.

Faster [v1 desktop faces](weights/neuronte-ui-wide-v1.md) exist for ui32, ui27 italic, ui31, ui31 italic
and ui32 italic, among the widest v0 nets. Each is a new file beside its v0 with the same advances:
one bundle of 8 small nets, each drawing 12 of the 96 characters. Both seeds reproduce all 96 glyphs
exactly at the native em, and a whole face draws 6 to 18 times faster uncached, the cost a desktop pays
when it builds its letter cells. The installer and Kilix 95 still load v0.

`neuronte-split` draws each character with one small net picked for it.
It draws ASCII, symbols, blocks and the mosaics four to seven times
faster than `neuronte-full`, Braille about sixteen times faster, and box
drawing and accented letters about twice as fast, as well or better. `neuronte-full` draws every character with one
net, which has to be as wide as its hardest characters need, and is kept
to show what the split gains. See
[Split nets and the router](#split-nets-and-the-router).

Both are for terminals and TUIs. Their characters beyond ASCII were
picked from what Kilix terminals actually showed, and the mosaics from
what terminal picture viewers emit:

- **Box drawing**, U+2500..U+257F: all 128. Light, heavy, double, dashed,
  arcs, diagonals and half lines. Lines run to the cell edges, so
  neighbouring cells join.
- **Block elements**, U+2580..U+259F: all 32. The shades ░▒▓ are squares
  a quarter of a cell wide, on a lattice that tiles across cells, at 25,
  50 and 75 percent ink.
- **Braille**, U+2800..U+28FF: all 256, with dots on a lattice of half a
  cell width, so Braille graphics keep one pitch across cells.
- **Sextants and octants**, in `neuronte-split` only: the 60 sextants
  U+1FB00..U+1FB3B, a 2 × 3 lattice; the 230 octants U+1CD00..U+1CDE5, a
  2 × 4 lattice, new in Unicode 16; and the 8 characters that Unicode
  encodes the other octant patterns as, such as U+1FB82 and U+1CEA0. With
  space, the quadrants and the other block elements, every one of the 256
  octant patterns has a character. Each sub-cell is exactly its share of
  the cell, so a picture made of them has no seams.
- **Symbols**: `… · ⋅ • — – ‘ ’ “ ” › ❯ × ° ½ © ≡ ≈ ※ ⁙ ⸬ ◆ ◈ ● ◉ ◯ ◐ ◑
  ▲ ▼ ▾ ▸ ⏵ ⎿ ← → ↑ ↓ ↗ ⇣ ✔ ☐ ☒ ✻ ✢ ✶ ✽ ✳` and U+00A0, drawn blank.
- **Accented letters**, 203: the letters of Latin-1, U+00C0..U+00FF, all
  of Latin Extended-A, U+0100..U+017F, ÷, and the spacing marks `¨ ¯ ´ ¸
  ˆ ˇ ˘ ˙ ˚ ˛ ˜ ˝`.

A letter with a mark is made from the ASCII letter and a mark, by the
Unicode decomposition: é is e and U+0301. The marks are drawn once, in
`font/marks.txt`. A capital under a mark is shortened to make room, as
is the ascender of ĥ and ĺ; i and j lose their dot; ď ľ ť Ľ take their
caron as a comma beside the stem, and ķ ļ ņ ŗ Ģ Ķ Ļ Ņ Ŗ their cedilla as
a comma below, as fonts commonly draw them. The 29 letters that are not
a letter and a mark, such as ß æ œ ð þ ø ł đ ħ ŋ ĳ, are drawn in
`font/letters.txt`.

## Layout

| Path | What it is |
|---|---|
| `font/strokes.txt` | The ASCII face: each character as pen strokes on a 10 × 20 grid. Written for this project |
| `font/symbols.txt` | The symbols of the full set, in the same form |
| `font/marks.txt` | The diacritic marks, keyed by their combining code points |
| `font/term-latin.txt` | The code points of `neuronte-term-latin-v1`, by training set: letters with one to three marks, composed by `train/glyphs.py` from letters drawn before and `font/marks.txt` |
| `font/term-scripts.txt` | The drawings and code points of `neuronte-term-mathalpha-v1`, `neuronte-term-syllabics-v1` and `neuronte-term-scripts-v1`, by training set, read by `train/term_scripts.py`: drawn characters, characters made by rule from the ASCII strokes or from a few shapes, and drawings held back from training |
| `font/term-math.txt`, `font/term-sym.txt`, `font/term-ding.txt` | The symbols of `neuronte-term-math-v1`, `neuronte-term-symbol-v1` and `neuronte-term-dingbat-v1` that are drawn by hand, in the same form; `train/term_glyphs.py` makes the rest of each family from them. Written for this project; no font was read |
| `font/term-math-partition.json`, `font/term-sym-partition.json`, `font/term-ding-partition.json` | Their training groups: families of about the same ink edge, 12, 10 or 8 characters to a group net, as `tools/term-partition.py` makes them from the drawings |
| `font/term-blocks.txt` | The code points of `neuronte-term-blocks-v1`, by training set, with the hexagram table, the Tai Xuan Jing digrams and the card suits; `train/term_blocks.py` makes the drawings from it by rule |
| `font/term-letters.txt` | The drawings of `neuronte-term-letters-v1`, a line for each character and the training sets: letters made by `train/term_letters.py` from strokes and letters drawn before |
| `font/term-rest.txt` | The drawings of `neuronte-term-rest-v1`, by training set: Hebrew letters and punctuation, Lao letters, the baht sign, and the lists of pointed and wide Hebrew letters, faces and moons that `train/term_rest.py` makes from parts. Written for this project; a `# note` line marks each drawing whose shape is not sure |
| `font/kilix-chrome.txt` | The drawings of `neuronte-kilix-chrome-v1`, by training set, each with a `# note` line saying what the symbol means on the Kilix bar; `train/kilix_chrome.py` makes the batteries and six weather symbols. Written for this project |
| `font/kilix-chrome-2.txt` | The drawings of `neuronte-kilix-chrome-v2` for a box of two cells, on a grid of 18 by 18 units, by training set, each with a `# note` line; `train/kilix_chrome2.py` puts them in the net's cell, turns strokes into outlines so they are as thick lying as standing, and makes the batteries and eight weather symbols. Written for this project |
| `font/letters.txt` | The Latin letters beyond ASCII that are not a letter plus a mark, and the Greek and Russian Cyrillic letters. The 49 Greek and 66 Russian Cyrillic letters are trained in RC9 accent-v2 and explicit split-v5 |
| `font/ui-1.txt` to `font/ui-128.txt` | A proportional face for binary desktop text, printable ASCII and the ellipsis, drawn as pixels for every em from 1 to 128 except 44, each character with its advance in pixels. Stems are one pixel wide through 16, two from 17 through 26, and three from 27. Written for this project. `train/train.py --set ui10` and so on train one net each, and score it pixel by pixel at its size. `train/pack.py --advances` packs a file's advances, bold one pixel more. The nets so far are `neuronte-ui1-v0` through `neuronte-ui39-v0`, one for every em, and `neuronte-ui43-v0`. `font/ui-EM-italic.txt` is that face sheared on the grid so the top sits to the right of the bottom, trained as `uiEMi`. The packed `neuronte-uiEM-italic-v0` nets now cover every integer em from 3 through 32; [paired validation and small-grid limits](weights/neuronte-italic-v0.md) accompany the additional 17 faces |
| `font/ui-large.txt`, `font/ui-large-advances.txt` | The same face above 32 pixels: the first-pass strokes the pixel faces were fitted to, drawn once for every em with a pen 3/32 em wide, the 32 px drawing's three-pixel stem, and blended. The advances are the 32 px drawing's in em, bold 0.2 design units (0.02 em) more. `train/train.py --set uilarge` trains the net and scores it by overlap at 32, 48, 64 and 96 pixels. The net is `neuronte-ui-large-v0` |
| `font/ui-scaled-advances.txt`, `font/ui-scaled-italic-advances.txt` | The advances of `neuronte-ui-scaled-v0` and of its italic: per character and weight, the step in hundredths of an em with the least summed pixel error against the hand faces (`font/ui-EM.txt`, `font/ui-EM-italic.txt`) from 17 to 32 px, by `train/fit_advances.py 17 32`. One table cannot match whole-pixel advances that do not grow in step with the em, so some are a pixel or two off; the card lists them per em |
| `font/ui-scaled-latin1-advances.txt`, `font/ui-scaled-latin1-italic-advances.txt`, `font/ui-large-latin1-advances.txt` | The same tables with the Latin-1 letters that ui-large composes, each at its base letter's advance (`train/fit_advances.py --extend`) |
| `font/icons.txt` | The icons, as colour layers back to front, each naming a palette entry. Powerline and progress are made in `train/glyphs.py` and are not listed in the file. Trained in `neuronte-icon-v1` |
| `font/palette.txt` | The palette for colour glyphs: entry 0 is the cell's foreground, 1 is clear, the rest have a dark-theme and a light-theme colour |
| `font/flame.txt`, `font/flame-palette.txt` | The Kilix flame, three colour layers in the syntax of `font/icons.txt`, with its own palette of the desktop's red, yellow and white. Drawn in the middle square of the cell. `font/flame.md` says how it was drawn and trained. The net is `neuronte-flame-v0` |
| `font/code-masks.txt` | The 43 parity masks that turn a scalar into the net's 64 character inputs |
| `font/octants.txt` | Which cells each octant U+1CD00..U+1CDE5 fills. Made by `train/mosaics.py` from Unicode 16's `UnicodeData.txt`, whose version and sha256 it records |
| `train/strokes.py` | Reads the stroke files |
| `train/glyphs.py` | The character sets. Makes box drawing and blocks from their Unicode names, Braille from the dot bits, sextants and octants from the cells they fill, accented letters from a letter and a mark, powerline and progress as one foreground layer, and the target the net learns. `python3 train/glyphs.py` checks the sets |
| `train/mosaics.py` | Makes `font/octants.txt`, and checks the sextants and the octant patterns encoded elsewhere against the same Unicode data |
| `train/train.py` | Trains a net on one set. Needs torch, and wants a GPU |
| `train/colour.py` | Trains a colour net, on `font/icons.txt` or another drawing and palette named with `--drawing` and `--palette`, with `--blank` scalars trained to draw nothing. `--shard I/N`, `--group I/N` or `--partition FILE --part I` trains one expert's share of the scalars. Needs torch, and wants a GPU. The default collection includes drawn icons and generated powerline/progress glyphs |
| `train/calibrate_colour.py` | Applies a recorded uniform distance offset to a separate colour weight file, preserving the original training artifact |
| `train/snap.py` | The straight edges of a colour glyph, measured from the drawings when the weights are packed, and the warp that snaps them |
| `train/gate.py` | Trains the router's gate for a bundle of nets. Needs torch; a CPU is enough |
| `train/pack.py` | Packs weights JSON into the binary file the C library loads: a distance net, a colour net, a bundle, an advance table, or a drawing file. A pixel face such as `font/ui-10.txt` packs as an advance table, bold one pixel more. Documents the layouts |
| `weights/` | The trained weights as JSON, the packed files, the scores and `SHA256SUMS`. `neuronte-draw-v2`, `neuronte-symbol-v0`, `neuronte-accent-v1`, `neuronte-pixel-v1`, `neuronte-braille-v0` and `neuronte-gate-v3` are the parts of `neuronte-split-v4`, with `neuronte-ascii-v0`. `neuronte-full-v2` is here so that `make test` and `make bench` run from a clone. `neuronte-ui1-v0` through `neuronte-ui39-v0`, one for every em, and `neuronte-ui43-v0` are the desktop face, each a drawing file of one net and its advances. `neuronte-uiEM-italic-v0` covers every integer native italic size 3–32. `neuronte-braille-v1` is the tiled Braille part of `neuronte-split-v6`. The `-v1` faces at 24 to 30 px draw the same pixels as their `-v0`, each as a drawing file of one bundle of small nets with seed 1's nets kept beside seed 0's (`neuronte-ui-v1.md`). `neuronte-ui-large-v0` is the scalable upright face from 33 px; `neuronte-flame-v0`, `neuronte-icon-v1`, `neuronte-emoji-v0` and `neuronte-emoji-v1` are separate colour files |
| `include/neuronte.h`, `src/` | The C library |
| `include/neuronte_cells.h`, `src/cells.c` | Cells files: coverage drawn once and kept in a file every process maps |
| `tools/neuronte-render.c` | Draws lines of text into a PPM file |
| `tools/neuronte-bench.c` | Times a net per cell, or a full net against a bundle per class of character |
| `tests/` | UTF-8 cases, API and loader checks, a cross-check against numpy, and a check of the packed advance table against the library |
| `demo/neuronte-demo.c` | Shows the font in a Kilix terminal through `kitty-framebuffer`, with typing |
| `demo/neuronte-compare.c` | Two weight files side by side, on examples that show where they differ |
| `demo/neuronte-showcase.c` | Every class of character the bundle draws, and pictures through octant cells at three levels |
| `demo/common.c` | What the two demos share: text, typing, snapshots and the terminal |

## Build and test

```sh
make          # build/libneuronte.a, build/libneuronte.so and the tools
make test     # needs python3 with numpy
make bench
./build/neuronte-render weights/neuronte-split-v5.nrt 16 out.ppm 'Hello, café. Привет, αβγ.' '╭──╮ ⣿⣶⣤⣀ ░▒▓ ✔'
```

The library is C11 with libm and nothing else. On x86-64 it builds its
inner loops twice, plain and AVX2, and picks one by CPU when it loads.
`CFLAGS=-DNEURONTE_NO_CLONES` builds the plain path only.

Desktop clients can read `font/ui-tops.json` for the first cell row of each
native UI bitmap (upright and italic use the same row). Its
`neuronte.ui-tops/v1` schema contains a `tops` object mapping decimal em sizes
to integer rows. The baseline within the bitmap remains in each drawing's
header. This generated table needs no Python training code at runtime.
After changing `UI_TOP` in `train/glyphs.py`, run `make ui-metadata` and commit
the table with the change; `make test-ui-metadata` and `make test` check drift.

`neuronte_coverage_styled()` and `neuronte_draw_scalar_styled()` apply
explicit synthetic terminal bold and italic to a monochrome net. They
share style flags and geometry, keep the original cell boundary, and
leave colour artwork unchanged. They do not imply separately trained
terminal styles. `neuronte_draw_text_stroke()` and its matching width
call add a caller-selected horizontal stroke to a proportional face,
with precisely the same added pixel advance. A scalable bold caller can
use `max(1, (em + 16) / 32)` instead of a one-pixel strike at every size.
The existing APIs, trained weights and packed advances keep their behavior.

Two-cell colour drawings use the explicit `neuronte_coverage_half()`,
`neuronte_coverage_layers_half()` and `neuronte_draw_half()` calls. The
caller selects a model trained on left and right halves, and passes a
Unicode scalar plus half 0 or 1. The private right-half code is never
accepted as Unicode by the ordinary APIs. These calls do not adopt a
colour asset in an application, supply shaping, or assert that a loaded
model knows a scalar. See `include/neuronte.h` for exact contracts.

The `font/ui-EM-italic.txt` drawings and accepted weights cover every integer
3–32. At 1 and 2 pixels the grid cannot express a distinct slant, so no upright
drawing is relabelled as italic. `tools/make-italic.py` reproduces the new targets
without clipping ink or overwriting existing artwork. Unsupported sizes, text
or layout requests require an explicit fallback in a consumer.

`make test` includes the selected RC9 scripts, full-v3, italic and emoji
inventories. Use `make test-rc9-italics` or `make test-rc9-emoji` for the focused
asset checks; `make pack-rc9-italics` and `make pack-rc9-emoji` reproduce their
packed files. Video has its separate `make test-video` target, and the
optional in-process video decoder, which links FFmpeg's libraries, has
`make media` and `make test-media` (see `tools/neuronte-video.md`).

`make test` checks, for every weight file, that:

- the weights match `weights/SHA256SUMS`, and the pointer nets' files,
  which are not in that list, match `weights/neuronte-pointer-v0.sha256`
  and `weights/neuronte-pointer-v1.sha256`. That is the only check
  `make test` makes of `neuronte-pointer-v0`. `make test-colour-marks`
  runs the gates of `weights/neuronte-pointer-v1.md`,
  `weights/neuronte-flame-v1.md` and `weights/neuronte-icon-v2.md` on
  both seeds of each, checks their hash lists, and checks each against
  the float64 reference;
- UTF-8 decoding follows Unicode's maximal-subpart rule, so a bad byte
  becomes one U+FFFD and never swallows the next character;
- the loader refuses a short, long or damaged file, or one of a shape it
  does not know, and the same for bundles: overlapping or unsorted
  ranges, a range to a net that is not there, a damaged gate, and a net
  in the bundle that is itself bad;
- drawing clips at every edge and blends correctly, and the draw cache
  gives the same cell after it has turned over;
- a tiled (version 6) net draws exactly its definition. Each sample
  belongs to the tile that holds it, and each tile's net sees its own
  code (`tests/test_tiled.c`, with hand-built nets, at 14 sizes and
  every sampling). It agrees with a float64 numpy evaluation to 1e-4
  from 1×1 to 64×128, and bit for bit with a build that evaluates
  every sample where it is summed (`tests/check_tiled.py`). A whole-cell
  tiled wrapper is bit for bit the net it wraps. The loader refuses
  every truncation and 35 other malformed tiled files, and the packer
  refuses 21 malformed tiled JSON files;
- a letter edge table (version 7) snaps exactly the letters it lists:
  each agrees with a float64 numpy evaluation at the warped samples to
  1e-3, while every letter without a record, every em at or above the
  table's width, and every em with snapping off is byte for byte the
  file without the table, and nine damaged or misplaced tables are
  refused (`tests/check_letter_snap.py`);
- the C library agrees with an independent float64 numpy evaluation of
  the JSON weights to 1e-3 in coverage, and the packed file is exactly
  what `train/pack.py` makes from the JSON. For the bundle, the C router
  must also send each of about 2,100 scalars, both Symbols for Legacy
  Computing blocks among them, to the net a Python router picks, with the
  gate evaluated in numpy;
- a small synthetic version 3 file round-trips its layer count, palette,
  palette head and one straight edge, the head names the right entry on
  every labelled glyph, and the dark and light composites agree with the
  numpy reference at 12 and 16 pixels, snapped and unsnapped. A
  grid-aligned icon is unchanged at 16 pixels with snapping on. The
  version 1 box-drawing checks also show that a horizontal line still
  meets a vertical one when snapping is asked for;
- each desktop-face file draws every one of its characters, regular and
  bold, as exactly the pixels in its drawing, `font/ui-1.txt` through
  `font/ui-39.txt` and `font/ui-43.txt`, or the italic drawing
  `font/ui-EM-italic.txt`, through `neuronte_draw_text()` with
  `neuronte_set_binary()` on;
- `neuronte-ui-large-v0`, which has no pixels to compare, holds the
  advances `font/ui-large-advances.txt` gives, regular and bold, and
  measures them in pixels as the packer does from 33 to 128 pixels;
  its net agrees with numpy at cells up to 96 pixels, and its letters
  drawn blended by `neuronte_draw_text()` at 36, 48 and 64 pixels,
  regular and bold, are the numpy coverage composited the same way.

For `neuronte-full` and `neuronte-split` it also checks that box lines
reach the cell edges, that █ fills its cell and ▀ the top half, that
U+2800 and U+00A0 are blank, and that ⣿ carries about eight times the
ink of ⠁. For both it checks that é ä ô ñ ü š ž ć are their letter
below the x-height with a mark above it, and ç its c with a mark below.
Those checks fail on a net that was not trained on accents.

For `neuronte-split` it checks the mosaics. At 16 × 32 with 2 × 2 samples,
each sub-cell of every sextant and of all 255 octant patterns with ink
must have a mean coverage above 0.9 where its bit is set and below 0.1
where it is not, leaving out the pixels within one pixel of an inner
boundary. A full column must reach the top and bottom rows, so stacked
cells join. At a 2 × 4 cell, where each octant sub-cell is one pixel,
all 2,040 pixels of those patterns must fall on the right side of 0.5,
none further than 0.25 from 0 or 1. That is the size at which octant
cells can show a picture pixel for pixel. The check fails on
`neuronte-split-v1`, whose ▙ ▛ ▜ ▟ put 0.21 of ink in their empty
quadrant, and on `neuronte-full-v2`, which knows no mosaics.

It also runs `python3 train/glyphs.py`, which checks the targets
themselves: every box junction is distinct, every quadrant, sextant
and octant is ink over exactly its cells, with no seam where two meet,
and in every colour glyph a lower layer runs under the layer above it
wherever the two meet, so their anti-aliased edges leave no line.

## Demo

```sh
make demo
./build/neuronte-demo                 # in a Kilix terminal
./build/neuronte-demo weights/neuronte-full-v2.nrt
./build/neuronte-demo --snapshot out.ppm 1280 800
```

Every glyph on the demo's screen, its labels included, is drawn by the
net and shown through `kitty-framebuffer`, which `make demo` compiles from
`KITTYFB_DIR` (default `$HOME/gpu_terminal/kilix-modules/kitty-framebuffer`).
It loads `neuronte-split` if it can, else `neuronte-full`, else
`neuronte-ascii`. With weights that know box drawing it adds a panel of
box drawing, blocks, Braille and symbols, and two spinners that turn
while it waits for keys. Type to draw text, Tab changes its size, Esc
quits. It needs zlib.

The first screen takes about 1.8 seconds with `neuronte-split` and about
5.9 with `neuronte-full`, since every cell is new. The demo shows each part
as it is done. After that a frame takes about a millisecond.

```sh
./build/neuronte-compare                      # neuronte-ascii left, neuronte-full right
./build/neuronte-compare weights/neuronte-full-v2.nrt weights/neuronte-split-v5.nrt
./build/neuronte-compare LEFT.nrt RIGHT.nrt   # any two weight files
./build/neuronte-compare --snapshot out.ppm 1280 800
```

```sh
./build/neuronte-showcase                      # in a Kilix terminal; Tab changes page
./build/neuronte-showcase --snapshot out.ppm 1280 800   # also writes out-pictures.ppm
```

`neuronte-showcase` shows everything `neuronte-split` draws, on two
pages. The first has every class of character, each with the net that
draws it, the blocks up close, and an area chart in octants that joins
across cells. The second is a moving scene made by code, drawn four
ways side by side, each with its time and its PSNR against the scene:

| Panel | A cell holds | Where it can be shown | One frame, 536 × 304 |
|---|---|---|---|
| the scene | | | |
| level 1 | one octant and two colours per 8 × 16 cell, the best of all 256 patterns in least squares | any terminal | 44 ms, 17.5 dB |
| level 2 | eight colours per 8 × 16 cell, three octants used as bit planes | a screen Neuronte draws | 8 ms, 17.8 dB |
| level 2 | eight colours per 2 × 4 cell, one pixel per sub-cell | a screen Neuronte draws | 9 ms, 59.5 dB |

Every cell's shape is the net's coverage of an octant character at that
size. At 2 × 4 the net's coverage is within about 0.01 of 0 or 1, so the
picture is the scene to within a level or two of 255; rounding the masks
would make it exact. At 8 × 16, level 1 keeps sharper edges and level 2
truer colour, at about the same PSNR: the scene's 1- to 3-pixel bars and
checkerboard are finer than either can show.

`neuronte-compare` splits the screen in two, and each half is drawn only
by its own net, labels included. The rows are ASCII at three sizes, a
TUI panel and file tree in box drawing with a spinner, a progress bar,
sparkline and Braille wave, punctuation beyond ASCII next to the ASCII
it stands in for, accented letters, and characters neither set was
trained on. Each row
says, in that net's own drawing, whether the net was trained on it.
Typing goes to both halves. Each half shows its net's size and how long
it took to draw one cell, the whole half, and the last keypress.

## Use

```c
#include "neuronte.h"

neuronte *font;
if (neuronte_open_file("neuronte-split-v5.nrt", &font) != NEURONTE_OK)
    return 1;
/* pixels: row-major 0xAARRGGBB, stride in pixels. */
neuronte_draw_utf8(font, pixels, stride, width, height,
                   x, y, 16, 32, "Hello", 5, 0xFFFFFFFF);
neuronte_close(font);
```

Every weight file works with the same calls. The file states its
hidden width, or for a bundle its nets and router, and
`neuronte_parameters()` reports the size of what was loaded.
`neuronte_nets()` and `neuronte_route()` say how many nets a file holds
and which one draws a given scalar. `neuronte_coverage()` returns a cell's coverage without
drawing it. `neuronte_open()` takes the weights from memory instead of a
file. The draw calls keep up to 1,024 cells, dropping the least recently
used, so a handle should not be shared between threads without a lock.

A bundle draws a scalar its nets were never trained on with whichever
net its router picks, and that net invents a shape. `neuronte_untrained()`
says whether a scalar is outside the bundle's trained table, and
`neuronte_set_untrained(font, 1)` draws such a scalar as a hollow box with
a small square inside, made by code, instead. The default, 0, draws as
before, and a trained scalar draws the same either way.

A colour weight file is version 3. It holds K layers that share one
hidden vector, a palette head that runs once per glyph, and the straight
edges of the drawings. `neuronte_layers()` is that K (a distance file
returns 1). `neuronte_set_theme()` selects the dark palette, which the
handle starts on, or the light one. `neuronte_palette()` copies one
theme's 32 colours, 96 bytes of R, G, B. `neuronte_set_snap()` snaps a
colour glyph's straight edges when the cell is narrower than the given
width. The file stores 14. Passing -1 restores that number, and 0 turns
snapping off. `neuronte_coverage_layers()` returns each layer's coverage
and its palette index. The two draw calls composite the layers back to
front: entry 1 clears, entry 0 uses the colour of the call, and any
other entry uses the theme's palette. The call's alpha then scales the
whole glyph. A pixel the glyph left clear is left as it was. Snapping
applies to a colour glyph that has an edge record. Box drawing has none,
so a horizontal line still meets a vertical one. Letters have none
either, unless their drawing file carries a letter edge table (a
version 7 member, only inside a drawing file, at most one): then the
letters it lists are snapped the same way below the table's own width,
and `neuronte_set_snap()` works on them too. A library older than the
table refuses such a file whole (`NEURONTE_ERR_FORMAT`), and a file
without one draws exactly as before. `train/pack.py --drawing-bundle
... --letter-edges SET --snap-below PX` writes it.

`neuronte-icon-v1` is the 167-icon net: form A, 256 wide, K = 6, trained
for 40,000 steps on the original drawings. A uniform distance offset of
-0.008 in its six final biases reduces boundary overshoot; this moves a
contour by about 0.0192 px at 16 px. Both seeds pass the mean 16 px IoU
requirement of 0.990: **0.991793416 and 0.990362830**. Their palette heads
are exact, and neither has positive unused coverage, a lost nonempty
layer, or a used layer with zero coverage at 12, 16 or 32 px. Seed 0 is
packed. The failed `neuronte-icon-v0` remains in history and research
records, and is retired from the active weights and tests.

Calibration raises seed 0's mean dark-theme composite error at 16 px
from 0.48 to 0.67 on the 0–255 scale while reducing thresholded boundary
errors. The raw runs, offset sweep and both seeds are retained in the
research run. `train/calibrate_colour.py` writes a separate artifact,
records the input weight hash and its own source hash, and refuses to
overwrite a file. The palette head and all hidden weights are unchanged.

`make test` checks the packed icon's quality gate, the C API, and numpy/C
coverage, palette, snap and theme agreement. The gate rejects even faint
unused masks. Expanded per-glyph drawing hashes bind the net's edge
table to its labelled shapes; unrelated trainer or glyph additions do
not invalidate that identity. Historical source hashes remain recorded
without being rewritten. Legacy colour weights without expanded hashes
still require their named drawing/palette and recorded parser/rule-module
hashes. If parser metadata is absent, the original archived parser is required.

### Cells files

The library's cache belongs to one handle in one process, so every
process pays for a character the first time it draws it. A cells file
holds the floats `neuronte_coverage_styled()` writes, for the
characters, cells and styles its maker chose, and every process maps the
same file read-only. A hit is bit for bit what a miss would compute:

```c
#include "neuronte_cells.h"

neuronte_cells *cells = NULL; /* stays NULL when there is no usable file */
neuronte_cells_open("neuronte-split-v9.cells", "neuronte-split-v9.nrt", 0, &cells);

const float *kept = cells ? neuronte_cells_find(cells, scalar, w, h, 0, style,
                                                NEURONTE_CELLS_SNAP_FILE) : NULL;
if (!kept)
    return neuronte_coverage_styled(font, scalar, w, h, 0, style, out);
memcpy(out, kept, (size_t)w * h * sizeof *out);
```

`neuronte_cells_write()` makes one, from a handle and a list of keys.
`include/neuronte_cells.h` has the contracts, what a file answers for
(the scalar, the cell, the samples, the style and the snap threshold are
the key; a file holds trained characters only, so the untrained mode is
not), and the layout of the file. This is a new translation unit:
`src/neuronte.c` and `include/neuronte.h` are unchanged. `make
test-cells` compares every entry of a written file with the library,
and opens some 11,000 damaged files, plain and under AddressSanitizer.

## The net

Input: 26 features of a point in the cell (x, y, and sines and cosines
at 1 to 32 cycles per cell width) and 64 features of the scalar (its 21
bits and 43 parity bits). Any two scalars differ in at least 13 of those
64. Three hidden layers, ReLU: 128 wide for `ascii`, 320 for `full`, 128
or 192 for the nets in `split`.
Output: the distance to the edge of the ink, clamped. Coverage is a ramp
one sample wide across that edge, so the same weights draw a sharp
letter in a large cell and a correctly softened one in a small cell.
Cells narrower than 24 pixels take 2 × 2 samples per pixel.

The trainer learns the signed distance to the ink edge, which
`train/glyphs.py` works out on a grid of nodes 1/256 cell width apart
and the trainer reads between nodes. A glyph there is a short list of
shapes applied in order: pen strokes, filled polygons, and cuts, which
open the channel of a double line.

```sh
python3 train/train.py out.json --set full --width 320   # 44 minutes on an RTX 3090 shared by five runs
python3 train/pack.py out.json out.nrt
```

`neuronte-ascii-v0` came from the earlier trainer at commit `0cd2a25`,
which measured the exact distance to each stroke. Retrained with the
grid at width 128 it scores 0.953, 0.990 and 0.993 at 8, 16 and 48
pixels, against 0.948, 0.990 and 0.992 for the shipped file.

## Split nets and the router

A split bundle is a set of nets that each know one part of the
characters, with a router in front. This section describes
`neuronte-split-v4`, which its measurements were made on. The default,
`neuronte-split-v5`, is the same bundle with two parts replaced:
`neuronte-accent-v2` (318 characters: the 203 below and 115 Greek and
Russian letters; 256 wide, 155,137 parameters) and `neuronte-gate-v4`
(68 ranges). Its figures are in [its own page](weights/neuronte-split-v5.md).
`neuronte-split-v6` is split-v5 with its Braille net replaced by the tiled
`neuronte-braille-v1` ([its page](weights/neuronte-braille-v1.md)).
split-v4:

| Net | Characters | Hidden width | Parameters |
|---|---|---:|---:|
| `neuronte-ascii-v0` | the 95 printable ASCII characters | 128 | 44,801 |
| `neuronte-draw-v2` | 131: box drawing and the shades | 192 | 91,777 |
| `neuronte-symbol-v0` | the 49 symbols | 128 | 44,801 |
| `neuronte-accent-v1` | the 203 accented letters and marks | 192 | 91,777 |
| `neuronte-pixel-v1` | 327: the other 29 block elements, the 60 sextants, the 230 octants and the 8 octant substitutes | 128 | 44,801 |
| `neuronte-braille-v0` | the 256 Braille patterns | 48 | 9,121 |
| `neuronte-gate-v3` | the router's gate: 64 inputs, 32 hidden, 6 outputs | | 2,278 |

The router is in the file. It first looks the scalar up in a table of
ranges, made from the characters each net was trained on: 62 ranges, a
binary search. A scalar no net was trained on goes to the gate, a small
net over the same 64 code features the font nets take. It picks the net
trained on most of the characters in that scalar's Unicode block, or the
ASCII net for blocks none of them knows, so 中 is drawn by the ASCII net
and ↔ by the symbol net. The gate agrees with that rule on all 1,061
trained characters, on all 2,187 others in their blocks, and on 99.97%
of a sample of 199,044 from the rest. It learns from Unicode's
`Blocks.txt`, which `train/gate.py` reads at training time; the block
list is not in the repository. `neuronte-gate-v3` used version 16.0,
the first with the octants' block.

Braille has a net of its own because it needs so little. Its dots are
the low eight bits of the scalar, which the net reads directly, so a net
48 wide draws all 256 patterns exactly: 1.0000 at every size scored, with
both seeds, where one of two seeds at 32 wide did not. In
`neuronte-split-v2` Braille shared the 128-wide pixel net, which costs
about three times as much per cell. The same was tried per character for
the mosaics and did not pay: a 64-wide net matches the 128-wide one on
only about one mosaic in ten.

Language-model routers were set aside: the smallest considered had 45
million parameters, hundreds of times the font, and routing is a
function of the code point that a table answers exactly.

```sh
python3 train/train.py pixel.json --set pixel --width 128   # also ascii, symbol, accent; draw is --set boxshade --width 192, braille --width 48
python3 train/gate.py gate.json ascii.json draw.json symbol.json accent.json pixel.json braille.json --blocks Blocks.txt
python3 train/pack.py --bundle split.nrt ascii.json draw.json symbol.json accent.json pixel.json braille.json --gate gate.json
```

`make bench` runs `neuronte-bench FULL BUNDLE`, which times each class of
characters drawn by `neuronte-full` alone and by the bundle, whose time
includes its router. One thread, no cache, i7-9850H, AVX2 path, on a
machine with a load average of 3 to 4 from other work, so times move
from run to run and the ratios by less. Milliseconds per cell, one run,
made in the same sitting as the table under [Speed](#speed):

| Class | Drawn in the bundle by | Cell | `full` | `split` | Faster |
|---|---|---|---:|---:|---:|
| ASCII, 95 | `ascii`, 128 | 8 × 16, 2 × 2 samples | 3.21 | 0.76 | 4.2× |
| | | 16 × 32, 2 × 2 | 12.51 | 2.72 | 4.6× |
| | | 48 × 96, 1 | 28.20 | 5.81 | 4.8× |
| box drawing and shades, 131 | `draw`, 192 | 8 × 16, 2 × 2 | 2.92 | 1.41 | 2.1× |
| | | 16 × 32, 2 × 2 | 11.73 | 5.73 | 2.0× |
| | | 48 × 96, 1 | 25.91 | 12.94 | 2.0× |
| symbols, 49 | `symbol`, 128 | 8 × 16, 2 × 2 | 2.95 | 0.81 | 3.6× |
| | | 16 × 32, 2 × 2 | 12.08 | 3.42 | 3.5× |
| | | 48 × 96, 1 | 28.63 | 6.93 | 4.1× |
| accented, 191 | `accent`, 192 | 8 × 16, 2 × 2 | 3.10 | 1.53 | 2.0× |
| | | 16 × 32, 2 × 2 | 12.77 | 5.85 | 2.2× |
| | | 48 × 96, 1 | 28.27 | 13.68 | 2.1× |
| blocks and mosaics, 327 | `pixel`, 128 | 8 × 16, 2 × 2 | 4.22 | 0.63 | 6.7× |
| | | 16 × 32, 2 × 2 | 17.03 | 2.34 | 7.3× |
| | | 48 × 96, 1 | 36.60 | 5.21 | 7.0× |
| Braille, 256 | `braille`, 48 | 8 × 16, 2 × 2 | 3.34 | 0.19 | 18.0× |
| | | 16 × 32, 2 × 2 | 13.24 | 0.72 | 18.5× |
| | | 48 × 96, 1 | 29.12 | 1.49 | 19.6× |

`make bench` now times the default, split-v5. The table is of split-v4;
in the same sitting split-v5 differed only on the accented row, where its
256-wide net took 2.33, 9.42 and 21.2 ms.

ASCII and the mosaics are drawn by nets of the same width, and the
difference between them is mostly noise; an earlier run under heavier
load gave 3.8 to 4.9 times for ASCII and 4.8 to 7.6 for the mosaics.
`neuronte-full` was not trained on the mosaics; it is timed on them, not
scored.

A net's hidden layers cost about the square of its width: 128 does a
sixth of the work of 320, and 192 a little over a third. The measured
gain is smaller than that because the first layer and the per-cell work
cost the same in both. The router takes 15 to 23 nanoseconds per call
through the table, and about 0.7 microseconds when the gate has to answer,
both far under a millisecond cell, and the draw calls route only on a
cache miss.

The trainer's scores, with 2 × 2 samples per pixel, for each class drawn
by the net the bundle sends it to and by `neuronte-full`, both against
the targets `train/glyphs.py` makes now:

| Class | Net in the bundle | 8 px | 16 px | 48 px | `full` 8 px | 16 px | 48 px |
|---|---|---:|---:|---:|---:|---:|---:|
| ASCII | `ascii`, 128 | 0.9477 | 0.9900 | 0.9921 | 0.9514 | 0.9881 | 0.9850 |
| box drawing | `draw`, 192 | 0.9748 | 0.9990 | 0.9988 | 0.9491 | 0.9992 | 0.9946 |
| shades | `draw`, 192 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9933 |
| blocks | `pixel`, 128 | 1.0000 | 1.0000 | 0.9999 | 0.9945 | 0.9945 | 0.9944 |
| Braille | `braille`, 48 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| sextants and octants | `pixel`, 128 | 1.0000 | 0.9998 | 0.9992 | | | |
| symbols | `symbol`, 128 | 0.9828 | 0.9908 | 0.9952 | 0.9778 | 0.9856 | 0.9838 |
| accented | `accent`, 192 | 0.9786 | 0.9849 | 0.9886 | 0.9748 | 0.9786 | 0.9798 |

The bundle is level with `full` or ahead of it everywhere but ASCII at 8
pixels, where it is behind by 0.004, and box drawing at 16, by 0.0002.
`full`'s blocks fall short of 1 because of the three-quadrant blocks
(see [Quality](#quality)); its own score file, against the targets it
was trained on, has them at 1.0000, 1.0000 and 0.9993 with the shades.
The weakest accented characters are the spacing mark ¨ alone, whose
dots are small enough that a pixel off costs much of their overlap, Œ,
and ĳ at 8 pixels. `neuronte-accent-v1` is the training of v0, same
seed, run again after the capital Ĳ was redrawn without serifs: at 12
and 16 pixels the I's serifs ran into the J's bar and the pair read as
a box. It scores within 0.001 of v0 at each size. `neuronte-full-v2`
was trained on the earlier Ĳ, which costs it 0.0024 at each size here.

### The pixel net and the new draw net

How the nets are grouped was decided by measurement. Three ways to
split the blocks, Braille, mosaics, box drawing and shades were trained
at several widths, each twice with different seeds, side by side on one
GPU. A grouping was kept if the mean of its two seeds was within the
spread between seeds (at least 0.002) of the bundle before it on every
class at 8, 16 and 48 pixels. Of those kept, the one with the smallest
widths was taken. Means of two seeds:

| Set | Width | 8 px | 16 px | 48 px |
|---|---:|---|---|---|
| blocks and mosaics | 64 | blocks .953, mosaics .999 | .953, .996 | .951, .992 |
| | 128 | 1, 1 | 1, .9999 | .9999, .9992 |
| | 192 | 1, 1 | 1, 1 | 1, .9999 |
| the same and Braille | 64 | Braille .990 | .990 | .990 |
| | 128 | Braille 1 | 1 | 1 |
| box drawing and shades | 128 | box .950 | .9992 | .9972 |
| | 192 | box .973 | .9989 | .9985 |

At 64 the eighth blocks ▏ ▕ fail and Braille loses its exactness. Box
drawing at 128 falls behind the old draw net at 8 pixels (0.950 against
0.963). So `neuronte-split-v2` had the blocks, mosaics and Braille in one
net 128 wide, and box drawing with the shades in one 192 wide. The seed
kept for each is the better of its two.

A later measurement scored the 64-wide net character by character
against the 128-wide one. Within 0.002 at all three sizes it matched on
240 of the 256 Braille patterns, but on only 28 of the 298 mosaics and 12
of the 29 blocks. So Braille was the one class a narrower net could
take. Trained alone, twice each: at 48 and at 64 wide it is exact with
both seeds; at 32 one seed is exact and the other scores 0.976.
`neuronte-split-v3` therefore gives Braille a 48-wide net,
`neuronte-braille-v0`, and the blocks and mosaics keep a 128-wide net
trained without it, `neuronte-pixel-v1`.

Every candidate at 128 or 192 is exact at a 2 × 4 cell: all 2,040 pixels
of the octant patterns are on the right side of 0.5, none further than
0.08 from 0 or 1. At 5 pixels wide every run scores about 0.81 on the
mosaics, at any width: a sub-cell edge falls on half a pixel there, so
even the target is half-covered. A sub-cell edge falls on a pixel edge
when the cell width is even and the height a multiple of 4 for octants
or of 3 for sextants, as at 8 × 16 for octants or 9 × 18 for sextants.
Elsewhere the pixel row or column on that edge is drawn half-covered,
which is what exact geometry gives; the edges are not snapped to pixels.

### The width of neuronte-full

`neuronte-full-v1` was 256 wide and knew 560 characters, without the
accented letters. Adding the 203 accented letters at the same width
cost it quality on the classes it already knew, so the whole set was
trained at five widths, side by side on one GPU, same steps and seed.
With 2 × 2 samples at 8, 16 and 48 pixels:

| Net | Parameters | ASCII | box drawing | symbols | accented |
|---|---:|---|---|---|---|
| `full-v1`, 256, 560 characters | 155,137 | .951 .990 .988 | .934 .9995 .996 | .979 .987 .987 | |
| 128 | 44,801 | .921 .939 .928 | .815 .989 .970 | .921 .934 .928 | .912 .904 .899 |
| 192 | 91,777 | .948 .977 .969 | .866 .998 .989 | .963 .968 .961 | .969 .967 .963 |
| 256 | 155,137 | .951 .985 .980 | .909 .999 .993 | .977 .980 .978 | .976 .978 .977 |
| 320, `full-v2` | 234,881 | .951 .988 .985 | .949 .999 .995 | .978 .986 .984 | .977 .981 .982 |
| 384 | 331,009 | .948 .988 .989 | .928 .998 .996 | .981 .984 .987 | .977 .983 .985 |
| the bundle, `split-v4` | 329,356 | .948 .990 .992 | .975 .999 .999 | .983 .991 .995 | .979 .985 .989 |

Blocks score 0.993 or better and Braille 1.000 at 192 and above. 320 is
the narrowest width that comes back to v1 on the classes v1 knew: it is
behind by at most 0.0034, on ASCII at 48 pixels, and ahead on box
drawing at 8. 384 is ahead of 320 on some classes and behind on others,
by under 0.021, at 1.4 times the cost. These differences are small
next to the spread between runs: the same 256-wide training, run on a
different GPU, scored 0.889 on box drawing at 8 pixels instead of
0.909. A single net for all 763 characters needs 320 wide, while the
bundle draws each of them with a net no wider than 192.

Other widths were tried. The first draw net, with box drawing, all the
blocks and Braille, was 3.3 times faster than `full` at 128 wide but
blurred the medium shade ▒, a checkerboard of 4-pixel squares in a
16-pixel cell, to grey, and scored 0.9359, 0.9986 and 0.9939 on box
drawing; at 64 wide it fell to 0.754 at 8 pixels. Box drawing and the
shades alone at 128 do better, 0.950 and 0.9992, but not well enough
(see [The pixel net and the new draw net](#the-pixel-net-and-the-new-draw-net)). An accent net 128
wide scores 0.9749, 0.9765 and 0.9770. The symbol net loses little at 64
wide (0.9782, 0.9851, 0.9843 with 14,209 parameters), so the bundle could
be smaller still there.

## Speed

One thread, i7-9850H, AVX2 path, no cache, with a load average of 3 to
4 from other work. Milliseconds per cell, one run of `neuronte-bench`
on each file, in the same sitting as the per-class table above, so the
two can be compared:

| Cell | Samples per pixel | `ascii`, 128 | `full`, 320 |
|---|---|---:|---:|
| 8 × 16 | 2 × 2 | 0.73 | 3.28 |
| 16 × 32 | 2 × 2 | 2.67 | 12.7 |
| 32 × 64 | 1 | 2.96 | 12.9 |
| 48 × 96 | 1 | 6.79 | 27.9 |

The nets of `neuronte-split` that are 128 wide cost what `ascii` does,
and those 192 wide about twice that; see the table above. Earlier
measurements found the plain path about 2.2 times slower than AVX2 for
a net 128 wide and 1.7 times for one 256 wide. A terminal should draw
each character once per cell size and reuse it. The draw calls' cache
does that.

## Quality

`weights/*.scores.json` is the trainer's own scoring: the net's ink
against the target's ink, mean over the characters, 1.0 being exact,
with 2 × 2 samples per pixel. With 2 × 2 samples every character is
closer to its own target than to any other at every size scored; with
one sample at 8 pixels, 2 of the 763 in `full` are not. Characters whose
targets are all but the same, such as space, U+00A0 and U+2800, count
as one.

| Weights | 8 px | 16 px | 48 px |
|---|---:|---:|---:|
| `ascii` | 0.948 | 0.990 | 0.992 |
| `full`, all 763 | 0.978 | 0.992 | 0.991 |

For each class in `split` and `full`, see
[Split nets and the router](#split-nets-and-the-router).

The weakest in `ascii` is `"` at 8 pixels, whose two marks are about one
pixel wide there. In `full` the weakest at 8 pixels are `"`, `:` and
`ĳ`, at 16 the ogonek `˛`, `✳` and `Ĕ`, and at 48 the dashes `┈ ┄` and
the asterisk `✽`.

The history of `neuronte-full`: v0 knew 557 characters at 256 wide; v1
added the shades, within 0.006 of v0 on each class with 2 × 2 samples;
v2 added the 203 accented letters and is 320 wide, for the reasons in
[The width of neuronte-full](#the-width-of-neuronte-full).

The three-quadrant blocks ▙ ▛ ▜ ▟ in `neuronte-full-v2`, and in the
retired `neuronte-draw-v1`, were trained on targets with a square of ink
a quarter of a cell wide in the corner of the empty quadrant, so those
nets draw that corner as a step. The scores could not show it, since
they compare a net with its own targets. `train/glyphs.py` now makes
the quadrants and the mosaics by one rule and checks that each fills
exactly its cells. `neuronte-pixel-v1`, trained from it, draws the
corner square, and `test_api --pixel` checks that it does. Scored
against today's targets, the blocks of `neuronte-draw-v1` come to 0.9945
at every size, against 1.0000 for `neuronte-pixel-v1`.

Box lines are not snapped to pixels. A line's centre falls on a pixel
edge at even cell sizes, so at 8 pixels a light line is two grey rows,
not one dark one. With one sample per pixel at 8 pixels, the light
dashed lines can fade to almost nothing; the default there is 2 × 2.

## Licence

MIT. See [LICENSE](LICENSE). The weights are part of the project and are
under the same licence. The optional media decoder in `src/media.c` adapts
FFmpeg code under LGPL-2.1-or-later; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

[PROVENANCE.md](PROVENANCE.md) says where every drawing and weight file
comes from and what has been checked.
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) carries the Unicode
notice. [TRAINING_MANIFEST.md](TRAINING_MANIFEST.md) lists how each
weight file was trained; `tools/training-manifest.py` writes it.

## Video experiments

[The video tool](tools/neuronte-video.md) fits two-ink terminal cells or
reconstructs multi-ink RGB cells with three cached neural masks. Its separate
video-only coverage calibration preserves every source byte at 2×4; ordinary
text weights and coverage remain unchanged. The exhaustive gate checks all
256 octants at all 2,048 centres. `tools/benchmark-video.py` makes original
synthetic footage, records search timings and generates a comparison clip.
