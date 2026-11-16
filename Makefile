CC ?= cc
CFLAGS ?= -O3
# Flags the build needs, kept apart so CFLAGS=... on the command line adds to them.
NRT_CFLAGS = -std=c11 -Wall -Wextra -Wpedantic -fPIC -Iinclude $(CPPFLAGS) $(CFLAGS)
LDLIBS = -lm
PYTHON ?= python3

ASCII = weights/neuronte-ascii-v0
FULL = weights/neuronte-full-v2
# The bundle: the ASCII net and the subset nets, with the gate the router
# asks about characters none of them was trained on.
DRAW = weights/neuronte-draw-v2
SYMBOL = weights/neuronte-symbol-v0
ACCENT = weights/neuronte-accent-v2
PIXEL = weights/neuronte-pixel-v1
BRAILLE = weights/neuronte-braille-v0
GATE = weights/neuronte-gate-v4.json
SPLIT = weights/neuronte-split-v5.nrt
NETS = $(ASCII).json $(DRAW).json $(SYMBOL).json $(ACCENT).json $(PIXEL).json $(BRAILLE).json
# The bundle before Greek and Russian, kept and still checked: split-v4,
# with the accent net and gate it was packed from.
PRIOR_ACCENT = weights/neuronte-accent-v1
PRIOR_GATE = weights/neuronte-gate-v3.json
PRIOR_SPLIT = weights/neuronte-split-v4.nrt
PRIOR_NETS = $(ASCII).json $(DRAW).json $(SYMBOL).json $(PRIOR_ACCENT).json $(PIXEL).json $(BRAILLE).json
# The RC9 names are the default bundle's own parts now.
RC9_ACCENT = $(ACCENT)
RC9_GATE = $(GATE)
RC9_SPLIT = $(SPLIT)
RC9_FULL = weights/neuronte-full-v3
RC9_ITALIC_SIZES = 3 4 5 6 7 8 9 13 15 17 19 21 23 25 27 29 31
RC9_ITALIC_JSON = $(foreach em,$(RC9_ITALIC_SIZES),weights/neuronte-ui$(em)-italic-v0.json)
# Narrower desktop faces for the faces drawn at H192 and H256 in v0: each a
# new -v1 drawing file (one net and the same advances), both seeds exact.
# The -v0 files stay as they were. See weights/neuronte-ui-v1-192-256.md.
FACES_V1_192_256 = ui13-italic ui16 ui16-italic ui17 ui17-italic ui18 ui18-italic ui19-italic ui20-italic ui21-italic ui22 ui22-italic ui23 ui23-italic ui25 ui25-italic ui26 ui26-italic

# Faster v1 desktop faces for five of the widest v0 faces: each a new -v1
# drawing file of one bundle of 8 nets, one per contiguous group of 12
# characters, and the same advances. Both seeds exact; the -v0 files stay as
# they were. Each entry is FACE:GROUPS. See weights/neuronte-ui-wide-v1.md.
FACES_WIDE_V1 = ui32:8 ui27-italic:8 ui31:8 ui31-italic:8 ui32-italic:8
RC9_EMOJI = weights/neuronte-emoji-v0.nrt
RC9_EMOJI_NETS = weights/neuronte-emoji-e0-v0.json weights/neuronte-emoji-e1-v0.json weights/neuronte-emoji-e2-v0.json
# Emoji v1: the same 300 emoji as v0 in 12 difficulty-balanced experts of
# width 192 (font/emoji-partition-balanced-12.json). Not a default.
EMOJI_V1 = weights/neuronte-emoji-v1.nrt
EMOJI_V1_NETS = $(foreach i,0 1 2 3 4 5 6 7 8 9 10 11,weights/neuronte-emoji-e$(i)-v1.json)
RC9_NETS = $(NETS)
# RC9 Braille: the tiled Braille expert, a version 6 file, and split-v6,
# which is split-v5 with only its Braille member replaced. Video full mode
# draws with split-v6; the video helpers stay bound to split-v5.
BRAILLE_V1 = weights/neuronte-braille-v1
SPLIT_V6 = weights/neuronte-split-v6.nrt
NETS_V6 = $(ASCII).json $(DRAW).json $(SYMBOL).json $(ACCENT).json $(PIXEL).json $(BRAILLE_V1).json
# Opt-in bundle: split-v5 with the 49 symbol labels moved to four width-32
# group nets (train/split_expert.py); split-v5 itself is unchanged.
SYMBOL_V1 = weights/neuronte-symbol-v1
SYMBOL_V1_SPLIT = weights/neuronte-split-v5-symbol-v1.nrt
# The desktop face: one drawing file for each em, a net and the advances
# of that em's pixel face.
UI1 = weights/neuronte-ui1-v0
UI2 = weights/neuronte-ui2-v0
UI3 = weights/neuronte-ui3-v0
UI4 = weights/neuronte-ui4-v0
UI5 = weights/neuronte-ui5-v0
UI6 = weights/neuronte-ui6-v0
UI7 = weights/neuronte-ui7-v0
UI8 = weights/neuronte-ui8-v0
UI9 = weights/neuronte-ui9-v0
UI10 = weights/neuronte-ui10-v0
UI10I = weights/neuronte-ui10-italic-v0
UI11 = weights/neuronte-ui11-v0
UI11I = weights/neuronte-ui11-italic-v0
UI12 = weights/neuronte-ui12-v0
UI12I = weights/neuronte-ui12-italic-v0
UI13 = weights/neuronte-ui13-v0
UI14 = weights/neuronte-ui14-v0
UI14I = weights/neuronte-ui14-italic-v0
UI15 = weights/neuronte-ui15-v0
UI16 = weights/neuronte-ui16-v0
UI16I = weights/neuronte-ui16-italic-v0
UI17 = weights/neuronte-ui17-v0
UI18 = weights/neuronte-ui18-v0
UI18I = weights/neuronte-ui18-italic-v0
UI19 = weights/neuronte-ui19-v0
UI20 = weights/neuronte-ui20-v0
UI20I = weights/neuronte-ui20-italic-v0
UI21 = weights/neuronte-ui21-v0
UI22 = weights/neuronte-ui22-v0
UI22I = weights/neuronte-ui22-italic-v0
UI23 = weights/neuronte-ui23-v0
UI24 = weights/neuronte-ui24-v0
UI24I = weights/neuronte-ui24-italic-v0
UI25 = weights/neuronte-ui25-v0
UI26 = weights/neuronte-ui26-v0
UI26I = weights/neuronte-ui26-italic-v0
UI27 = weights/neuronte-ui27-v0
UI28 = weights/neuronte-ui28-v0
UI29 = weights/neuronte-ui29-v0
UI30 = weights/neuronte-ui30-v0
UI28I = weights/neuronte-ui28-italic-v0
UI30I = weights/neuronte-ui30-italic-v0
UI32I = weights/neuronte-ui32-italic-v0
UI31 = weights/neuronte-ui31-v0
UI32 = weights/neuronte-ui32-v0
UI33 = weights/neuronte-ui33-v0
UI34 = weights/neuronte-ui34-v0
UI35 = weights/neuronte-ui35-v0
UI36 = weights/neuronte-ui36-v0
UI37 = weights/neuronte-ui37-v0
UI38 = weights/neuronte-ui38-v0
UI39 = weights/neuronte-ui39-v0
UI43 = weights/neuronte-ui43-v0
# Desktop faces v1 at 33-39 and 43 px: each a drawing file of one bundle of small
# nets, each drawing only the em rows of its own characters, and the advances.
# Seed 0 is shipped; seed 1 is kept so the exact gate reruns on both.
UI33_V1 = weights/neuronte-ui33-v1
UI33_V1_NETS = $(UI33_V1)-p0.json $(UI33_V1)-p1.json $(UI33_V1)-p2.json $(UI33_V1)-p3.json $(UI33_V1)-p4.json $(UI33_V1)-p5.json $(UI33_V1)-p6.json $(UI33_V1)-p7.json $(UI33_V1)-p8.json $(UI33_V1)-p9.json $(UI33_V1)-p10.json $(UI33_V1)-p11.json $(UI33_V1)-p12.json $(UI33_V1)-p13.json $(UI33_V1)-p14.json $(UI33_V1)-p15.json
UI33_V1_SEED1 = $(UI33_V1).seed1-p0.json $(UI33_V1).seed1-p1.json $(UI33_V1).seed1-p2.json $(UI33_V1).seed1-p3.json $(UI33_V1).seed1-p4.json $(UI33_V1).seed1-p5.json $(UI33_V1).seed1-p6.json $(UI33_V1).seed1-p7.json $(UI33_V1).seed1-p8.json $(UI33_V1).seed1-p9.json $(UI33_V1).seed1-p10.json $(UI33_V1).seed1-p11.json $(UI33_V1).seed1-p12.json $(UI33_V1).seed1-p13.json $(UI33_V1).seed1-p14.json $(UI33_V1).seed1-p15.json
UI34_V1 = weights/neuronte-ui34-v1
UI34_V1_NETS = $(UI34_V1)-p0.json $(UI34_V1)-p1.json $(UI34_V1)-p2.json $(UI34_V1)-p3.json $(UI34_V1)-p4.json $(UI34_V1)-p5.json $(UI34_V1)-p6.json $(UI34_V1)-p7.json $(UI34_V1)-p8.json $(UI34_V1)-p9.json $(UI34_V1)-p10.json $(UI34_V1)-p11.json $(UI34_V1)-p12.json $(UI34_V1)-p13.json $(UI34_V1)-p14.json $(UI34_V1)-p15.json $(UI34_V1)-p16.json $(UI34_V1)-p17.json $(UI34_V1)-p18.json $(UI34_V1)-p19.json $(UI34_V1)-p20.json $(UI34_V1)-p21.json $(UI34_V1)-p22.json $(UI34_V1)-p23.json $(UI34_V1)-p24.json $(UI34_V1)-p25.json $(UI34_V1)-p26.json $(UI34_V1)-p27.json $(UI34_V1)-p28.json $(UI34_V1)-p29.json $(UI34_V1)-p30.json $(UI34_V1)-p31.json
UI34_V1_SEED1 = $(UI34_V1).seed1-p0.json $(UI34_V1).seed1-p1.json $(UI34_V1).seed1-p2.json $(UI34_V1).seed1-p3.json $(UI34_V1).seed1-p4.json $(UI34_V1).seed1-p5.json $(UI34_V1).seed1-p6.json $(UI34_V1).seed1-p7.json $(UI34_V1).seed1-p8.json $(UI34_V1).seed1-p9.json $(UI34_V1).seed1-p10.json $(UI34_V1).seed1-p11.json $(UI34_V1).seed1-p12.json $(UI34_V1).seed1-p13.json $(UI34_V1).seed1-p14.json $(UI34_V1).seed1-p15.json $(UI34_V1).seed1-p16.json $(UI34_V1).seed1-p17.json $(UI34_V1).seed1-p18.json $(UI34_V1).seed1-p19.json $(UI34_V1).seed1-p20.json $(UI34_V1).seed1-p21.json $(UI34_V1).seed1-p22.json $(UI34_V1).seed1-p23.json $(UI34_V1).seed1-p24.json $(UI34_V1).seed1-p25.json $(UI34_V1).seed1-p26.json $(UI34_V1).seed1-p27.json $(UI34_V1).seed1-p28.json $(UI34_V1).seed1-p29.json $(UI34_V1).seed1-p30.json $(UI34_V1).seed1-p31.json
UI35_V1 = weights/neuronte-ui35-v1
UI35_V1_NETS = $(UI35_V1)-p0.json $(UI35_V1)-p1.json $(UI35_V1)-p2.json $(UI35_V1)-p3.json $(UI35_V1)-p4.json $(UI35_V1)-p5.json $(UI35_V1)-p6.json $(UI35_V1)-p7.json $(UI35_V1)-p8.json $(UI35_V1)-p9.json $(UI35_V1)-p10.json $(UI35_V1)-p11.json $(UI35_V1)-p12.json $(UI35_V1)-p13.json $(UI35_V1)-p14.json $(UI35_V1)-p15.json $(UI35_V1)-p16.json $(UI35_V1)-p17.json $(UI35_V1)-p18.json $(UI35_V1)-p19.json $(UI35_V1)-p20.json $(UI35_V1)-p21.json $(UI35_V1)-p22.json $(UI35_V1)-p23.json $(UI35_V1)-p24.json $(UI35_V1)-p25.json $(UI35_V1)-p26.json $(UI35_V1)-p27.json $(UI35_V1)-p28.json $(UI35_V1)-p29.json $(UI35_V1)-p30.json $(UI35_V1)-p31.json
UI35_V1_SEED1 = $(UI35_V1).seed1-p0.json $(UI35_V1).seed1-p1.json $(UI35_V1).seed1-p2.json $(UI35_V1).seed1-p3.json $(UI35_V1).seed1-p4.json $(UI35_V1).seed1-p5.json $(UI35_V1).seed1-p6.json $(UI35_V1).seed1-p7.json $(UI35_V1).seed1-p8.json $(UI35_V1).seed1-p9.json $(UI35_V1).seed1-p10.json $(UI35_V1).seed1-p11.json $(UI35_V1).seed1-p12.json $(UI35_V1).seed1-p13.json $(UI35_V1).seed1-p14.json $(UI35_V1).seed1-p15.json $(UI35_V1).seed1-p16.json $(UI35_V1).seed1-p17.json $(UI35_V1).seed1-p18.json $(UI35_V1).seed1-p19.json $(UI35_V1).seed1-p20.json $(UI35_V1).seed1-p21.json $(UI35_V1).seed1-p22.json $(UI35_V1).seed1-p23.json $(UI35_V1).seed1-p24.json $(UI35_V1).seed1-p25.json $(UI35_V1).seed1-p26.json $(UI35_V1).seed1-p27.json $(UI35_V1).seed1-p28.json $(UI35_V1).seed1-p29.json $(UI35_V1).seed1-p30.json $(UI35_V1).seed1-p31.json
UI36_V1 = weights/neuronte-ui36-v1
UI36_V1_NETS = $(UI36_V1)-p0.json $(UI36_V1)-p1.json $(UI36_V1)-p2.json $(UI36_V1)-p3.json $(UI36_V1)-p4.json $(UI36_V1)-p5.json $(UI36_V1)-p6.json $(UI36_V1)-p7.json $(UI36_V1)-p8.json $(UI36_V1)-p9.json $(UI36_V1)-p10.json $(UI36_V1)-p11.json $(UI36_V1)-p12.json $(UI36_V1)-p13.json $(UI36_V1)-p14.json $(UI36_V1)-p15.json
UI36_V1_SEED1 = $(UI36_V1).seed1-p0.json $(UI36_V1).seed1-p1.json $(UI36_V1).seed1-p2.json $(UI36_V1).seed1-p3.json $(UI36_V1).seed1-p4.json $(UI36_V1).seed1-p5.json $(UI36_V1).seed1-p6.json $(UI36_V1).seed1-p7.json $(UI36_V1).seed1-p8.json $(UI36_V1).seed1-p9.json $(UI36_V1).seed1-p10.json $(UI36_V1).seed1-p11.json $(UI36_V1).seed1-p12.json $(UI36_V1).seed1-p13.json $(UI36_V1).seed1-p14.json $(UI36_V1).seed1-p15.json
UI37_V1 = weights/neuronte-ui37-v1
UI37_V1_NETS = $(UI37_V1)-p0.json $(UI37_V1)-p1.json $(UI37_V1)-p2.json $(UI37_V1)-p3.json $(UI37_V1)-p4.json $(UI37_V1)-p5.json $(UI37_V1)-p6.json $(UI37_V1)-p7.json $(UI37_V1)-p8.json $(UI37_V1)-p9.json $(UI37_V1)-p10.json $(UI37_V1)-p11.json $(UI37_V1)-p12.json $(UI37_V1)-p13.json $(UI37_V1)-p14.json $(UI37_V1)-p15.json
UI37_V1_SEED1 = $(UI37_V1).seed1-p0.json $(UI37_V1).seed1-p1.json $(UI37_V1).seed1-p2.json $(UI37_V1).seed1-p3.json $(UI37_V1).seed1-p4.json $(UI37_V1).seed1-p5.json $(UI37_V1).seed1-p6.json $(UI37_V1).seed1-p7.json $(UI37_V1).seed1-p8.json $(UI37_V1).seed1-p9.json $(UI37_V1).seed1-p10.json $(UI37_V1).seed1-p11.json $(UI37_V1).seed1-p12.json $(UI37_V1).seed1-p13.json $(UI37_V1).seed1-p14.json $(UI37_V1).seed1-p15.json
UI38_V1 = weights/neuronte-ui38-v1
UI38_V1_NETS = $(UI38_V1)-p0.json $(UI38_V1)-p1.json $(UI38_V1)-p2.json $(UI38_V1)-p3.json $(UI38_V1)-p4.json $(UI38_V1)-p5.json $(UI38_V1)-p6.json $(UI38_V1)-p7.json $(UI38_V1)-p8.json $(UI38_V1)-p9.json $(UI38_V1)-p10.json $(UI38_V1)-p11.json $(UI38_V1)-p12.json $(UI38_V1)-p13.json $(UI38_V1)-p14.json $(UI38_V1)-p15.json $(UI38_V1)-p16.json $(UI38_V1)-p17.json $(UI38_V1)-p18.json $(UI38_V1)-p19.json $(UI38_V1)-p20.json $(UI38_V1)-p21.json $(UI38_V1)-p22.json $(UI38_V1)-p23.json $(UI38_V1)-p24.json $(UI38_V1)-p25.json $(UI38_V1)-p26.json $(UI38_V1)-p27.json $(UI38_V1)-p28.json $(UI38_V1)-p29.json $(UI38_V1)-p30.json $(UI38_V1)-p31.json
UI38_V1_SEED1 = $(UI38_V1).seed1-p0.json $(UI38_V1).seed1-p1.json $(UI38_V1).seed1-p2.json $(UI38_V1).seed1-p3.json $(UI38_V1).seed1-p4.json $(UI38_V1).seed1-p5.json $(UI38_V1).seed1-p6.json $(UI38_V1).seed1-p7.json $(UI38_V1).seed1-p8.json $(UI38_V1).seed1-p9.json $(UI38_V1).seed1-p10.json $(UI38_V1).seed1-p11.json $(UI38_V1).seed1-p12.json $(UI38_V1).seed1-p13.json $(UI38_V1).seed1-p14.json $(UI38_V1).seed1-p15.json $(UI38_V1).seed1-p16.json $(UI38_V1).seed1-p17.json $(UI38_V1).seed1-p18.json $(UI38_V1).seed1-p19.json $(UI38_V1).seed1-p20.json $(UI38_V1).seed1-p21.json $(UI38_V1).seed1-p22.json $(UI38_V1).seed1-p23.json $(UI38_V1).seed1-p24.json $(UI38_V1).seed1-p25.json $(UI38_V1).seed1-p26.json $(UI38_V1).seed1-p27.json $(UI38_V1).seed1-p28.json $(UI38_V1).seed1-p29.json $(UI38_V1).seed1-p30.json $(UI38_V1).seed1-p31.json
UI39_V1 = weights/neuronte-ui39-v1
UI39_V1_NETS = $(UI39_V1)-p0.json $(UI39_V1)-p1.json $(UI39_V1)-p2.json $(UI39_V1)-p3.json $(UI39_V1)-p4.json $(UI39_V1)-p5.json $(UI39_V1)-p6.json $(UI39_V1)-p7.json $(UI39_V1)-p8.json $(UI39_V1)-p9.json $(UI39_V1)-p10.json $(UI39_V1)-p11.json $(UI39_V1)-p12.json $(UI39_V1)-p13.json $(UI39_V1)-p14.json $(UI39_V1)-p15.json $(UI39_V1)-p16.json $(UI39_V1)-p17.json $(UI39_V1)-p18.json $(UI39_V1)-p19.json $(UI39_V1)-p20.json $(UI39_V1)-p21.json $(UI39_V1)-p22.json $(UI39_V1)-p23.json $(UI39_V1)-p24.json $(UI39_V1)-p25.json $(UI39_V1)-p26.json $(UI39_V1)-p27.json $(UI39_V1)-p28.json $(UI39_V1)-p29.json $(UI39_V1)-p30.json $(UI39_V1)-p31.json
UI39_V1_SEED1 = $(UI39_V1).seed1-p0.json $(UI39_V1).seed1-p1.json $(UI39_V1).seed1-p2.json $(UI39_V1).seed1-p3.json $(UI39_V1).seed1-p4.json $(UI39_V1).seed1-p5.json $(UI39_V1).seed1-p6.json $(UI39_V1).seed1-p7.json $(UI39_V1).seed1-p8.json $(UI39_V1).seed1-p9.json $(UI39_V1).seed1-p10.json $(UI39_V1).seed1-p11.json $(UI39_V1).seed1-p12.json $(UI39_V1).seed1-p13.json $(UI39_V1).seed1-p14.json $(UI39_V1).seed1-p15.json $(UI39_V1).seed1-p16.json $(UI39_V1).seed1-p17.json $(UI39_V1).seed1-p18.json $(UI39_V1).seed1-p19.json $(UI39_V1).seed1-p20.json $(UI39_V1).seed1-p21.json $(UI39_V1).seed1-p22.json $(UI39_V1).seed1-p23.json $(UI39_V1).seed1-p24.json $(UI39_V1).seed1-p25.json $(UI39_V1).seed1-p26.json $(UI39_V1).seed1-p27.json $(UI39_V1).seed1-p28.json $(UI39_V1).seed1-p29.json $(UI39_V1).seed1-p30.json $(UI39_V1).seed1-p31.json
UI43_V1 = weights/neuronte-ui43-v1
UI43_V1_NETS = $(UI43_V1)-p0.json $(UI43_V1)-p1.json $(UI43_V1)-p2.json $(UI43_V1)-p3.json $(UI43_V1)-p4.json $(UI43_V1)-p5.json $(UI43_V1)-p6.json $(UI43_V1)-p7.json $(UI43_V1)-p8.json $(UI43_V1)-p9.json $(UI43_V1)-p10.json $(UI43_V1)-p11.json $(UI43_V1)-p12.json $(UI43_V1)-p13.json $(UI43_V1)-p14.json $(UI43_V1)-p15.json $(UI43_V1)-p16.json $(UI43_V1)-p17.json $(UI43_V1)-p18.json $(UI43_V1)-p19.json $(UI43_V1)-p20.json $(UI43_V1)-p21.json $(UI43_V1)-p22.json $(UI43_V1)-p23.json $(UI43_V1)-p24.json $(UI43_V1)-p25.json $(UI43_V1)-p26.json $(UI43_V1)-p27.json $(UI43_V1)-p28.json $(UI43_V1)-p29.json $(UI43_V1)-p30.json $(UI43_V1)-p31.json
UI43_V1_SEED1 = $(UI43_V1).seed1-p0.json $(UI43_V1).seed1-p1.json $(UI43_V1).seed1-p2.json $(UI43_V1).seed1-p3.json $(UI43_V1).seed1-p4.json $(UI43_V1).seed1-p5.json $(UI43_V1).seed1-p6.json $(UI43_V1).seed1-p7.json $(UI43_V1).seed1-p8.json $(UI43_V1).seed1-p9.json $(UI43_V1).seed1-p10.json $(UI43_V1).seed1-p11.json $(UI43_V1).seed1-p12.json $(UI43_V1).seed1-p13.json $(UI43_V1).seed1-p14.json $(UI43_V1).seed1-p15.json $(UI43_V1).seed1-p16.json $(UI43_V1).seed1-p17.json $(UI43_V1).seed1-p18.json $(UI43_V1).seed1-p19.json $(UI43_V1).seed1-p20.json $(UI43_V1).seed1-p21.json $(UI43_V1).seed1-p22.json $(UI43_V1).seed1-p23.json $(UI43_V1).seed1-p24.json $(UI43_V1).seed1-p25.json $(UI43_V1).seed1-p26.json $(UI43_V1).seed1-p27.json $(UI43_V1).seed1-p28.json $(UI43_V1).seed1-p29.json $(UI43_V1).seed1-p30.json $(UI43_V1).seed1-p31.json
# Above 32 px, one scalable net for every em, drawn blended, with its advances.
UILARGE = weights/neuronte-ui-large-v0
# Desktop faces v1: each a drawing file of one bundle of small nets, each net
# drawing only the em rows of its own characters, and the face's advances.
# Seed 0 is shipped; seed 1 is kept so the exact gate reruns on both.
GROUPS8 = 0 1 2 3 4 5 6 7
GROUPS16 = $(GROUPS8) 8 9 10 11 12 13 14 15
UI24_V1 = weights/neuronte-ui24-v1
UI24_V1_NETS = $(foreach g,$(GROUPS16),$(UI24_V1)-p$(g).json)
UI24_V1_SEED1 = $(foreach g,$(GROUPS16),$(UI24_V1).seed1-p$(g).json)
UI24I_V1 = weights/neuronte-ui24-italic-v1
UI24I_V1_NETS = $(foreach g,$(GROUPS16),$(UI24I_V1)-p$(g).json)
UI24I_V1_SEED1 = $(foreach g,$(GROUPS16),$(UI24I_V1).seed1-p$(g).json)
UI27_V1 = weights/neuronte-ui27-v1
UI27_V1_NETS = $(foreach g,$(GROUPS16),$(UI27_V1)-p$(g).json)
UI27_V1_SEED1 = $(foreach g,$(GROUPS16),$(UI27_V1).seed1-p$(g).json)
UI28_V1 = weights/neuronte-ui28-v1
UI28_V1_NETS = $(foreach g,$(GROUPS16),$(UI28_V1)-p$(g).json)
UI28_V1_SEED1 = $(foreach g,$(GROUPS16),$(UI28_V1).seed1-p$(g).json)
UI28I_V1 = weights/neuronte-ui28-italic-v1
UI28I_V1_NETS = $(foreach g,$(GROUPS16),$(UI28I_V1)-p$(g).json)
UI28I_V1_SEED1 = $(foreach g,$(GROUPS16),$(UI28I_V1).seed1-p$(g).json)
UI29_V1 = weights/neuronte-ui29-v1
UI29_V1_NETS = $(foreach g,$(GROUPS16),$(UI29_V1)-p$(g).json)
UI29_V1_SEED1 = $(foreach g,$(GROUPS16),$(UI29_V1).seed1-p$(g).json)
UI29I_V1 = weights/neuronte-ui29-italic-v1
UI29I_V1_NETS = $(foreach g,$(GROUPS16),$(UI29I_V1)-p$(g).json)
UI29I_V1_SEED1 = $(foreach g,$(GROUPS16),$(UI29I_V1).seed1-p$(g).json)
UI30_V1 = weights/neuronte-ui30-v1
UI30_V1_NETS = $(foreach g,$(GROUPS16),$(UI30_V1)-p$(g).json)
UI30_V1_SEED1 = $(foreach g,$(GROUPS16),$(UI30_V1).seed1-p$(g).json)
UI30I_V1 = weights/neuronte-ui30-italic-v1
UI30I_V1_NETS = $(foreach g,$(GROUPS8),$(UI30I_V1)-p$(g).json)
UI30I_V1_SEED1 = $(foreach g,$(GROUPS8),$(UI30I_V1).seed1-p$(g).json)

# Small desktop faces v1: each a drawing file of one bundle of small nets, each net drawing
# only the em rows of its own characters, and the face's advances. Listed as face:members.
# Seed 0 is shipped; seed 1 is kept so the exact gate reruns on both. The -v0 files stay as
# they were. See weights/neuronte-ui-v1-small.md.
FACES_V1_SMALL = ui1:1 ui2:1 ui3:32 ui3-italic:32 ui4:96 ui4-italic:32 ui5:32 ui5-italic:96 ui6:96 ui6-italic:96 ui7:32 ui7-italic:96 ui8:32 ui8-italic:32 ui9:96 ui9-italic:96 ui10:96 ui10-italic:96 ui11:96 ui11-italic:96 ui12:96 ui12-italic:96 ui13:96 ui14:96 ui14-italic:96 ui15:96 ui15-italic:96 ui19:96 ui20:96 ui21:32
# The Kilix flame: one colour net, version 3, drawn at U+100000.
FLAME = weights/neuronte-flame-v0
# The icon net: a colour net, form A, a version 3 file by itself. It is not
# in the bundle; neuronte-split-v5 is the default font.
ICON = weights/neuronte-icon-v1
OBJS = build/neuronte.o build/utf8.o build/video.o build/bits.o
TOOLS = build/neuronte-render build/neuronte-bench
TESTS = build/test_utf8 build/test_api build/test_tiled

all: build/libneuronte.a build/libneuronte.so $(TOOLS)

build:
	mkdir -p build

build/%.o: src/%.c include/neuronte.h | build
	$(CC) $(NRT_CFLAGS) -c -o $@ $<

build/libneuronte.a: $(OBJS)
	$(AR) rcs $@ $^

build/libneuronte.so: $(OBJS)
	$(CC) $(LDFLAGS) -shared -o $@ $^ $(LDLIBS)

build/%: tools/%.c build/libneuronte.a
	$(CC) $(NRT_CFLAGS) -o $@ $< build/libneuronte.a $(LDLIBS)

build/test_%: tests/test_%.c build/libneuronte.a
	$(CC) $(NRT_CFLAGS) -o $@ $< build/libneuronte.a $(LDLIBS)

# The library again, with every tiled sample evaluated where it is summed
# instead of kept per tile; its coverage must be the same, bit for bit.
STREAM_OBJS = $(OBJS:build/%=build/stream/%)

build/stream/%.o: src/%.c include/neuronte.h
	mkdir -p build/stream
	$(CC) $(NRT_CFLAGS) -DNEURONTE_TILE_KEEP_MAX=0 -c -o $@ $<

build/stream/libneuronte.so: $(STREAM_OBJS)
	$(CC) $(LDFLAGS) -shared -o $@ $^ $(LDLIBS)

# The terminal demo links kitty-framebuffer (MIT), compiled from its source
# tree into build/ so that tree is left untouched. Needs zlib and pthreads.
KITTYFB_DIR ?= $(HOME)/gpu_terminal/kilix-modules/kitty-framebuffer

DEMOS = build/neuronte-demo build/neuronte-compare build/neuronte-showcase

demo: $(DEMOS)

build/kitty_framebuffer.o: $(KITTYFB_DIR)/src/kitty_framebuffer.c | build
	$(CC) -std=c11 -O2 -fPIC -pthread -D_POSIX_C_SOURCE=200809L -D_DEFAULT_SOURCE \
		-I$(KITTYFB_DIR)/include -c -o $@ $<

build/demo-common.o: demo/common.c demo/common.h include/neuronte.h | build
	$(CC) $(NRT_CFLAGS) -pthread -I$(KITTYFB_DIR)/include -c -o $@ $<

$(DEMOS): build/%: demo/%.c demo/common.h build/demo-common.o build/libneuronte.a build/kitty_framebuffer.o
	$(CC) $(NRT_CFLAGS) -pthread -Idemo -o $@ $< build/demo-common.o build/kitty_framebuffer.o \
		build/libneuronte.a $(LDLIBS) -lz

# Rebuild the packed weights from the JSON the trainers write.
pack: pack-rc9

pack-rc9: pack-rc9-italics pack-rc9-emoji $(RC9_NETS) $(RC9_GATE) $(RC9_FULL).json $(BRAILLE_V1).json
	$(PYTHON) train/pack.py $(RC9_ACCENT).json $(RC9_ACCENT).nrt
	$(PYTHON) train/pack.py --bundle $(RC9_SPLIT) $(RC9_NETS) --gate $(RC9_GATE)
	$(PYTHON) train/pack.py $(BRAILLE_V1).json $(BRAILLE_V1).nrt
	$(PYTHON) train/pack.py --bundle $(SPLIT_V6) $(NETS_V6) --gate $(RC9_GATE)
	$(PYTHON) train/pack.py $(RC9_FULL).json $(RC9_FULL).nrt

pack-rc9-italics: $(RC9_ITALIC_JSON)
	@set -e; for em in $(RC9_ITALIC_SIZES); do \
		$(PYTHON) train/pack.py --drawing weights/neuronte-ui$$em-italic-v0.nrt weights/neuronte-ui$$em-italic-v0.json font/ui-$$em-italic.txt; \
	done

pack-rc9-emoji: $(RC9_EMOJI_NETS)
	$(PYTHON) tools/pack-bundle-members.py $(RC9_EMOJI) $(RC9_EMOJI_NETS)

pack: $(ASCII).json $(FULL).json $(NETS) $(GATE) $(PRIOR_NETS) $(PRIOR_GATE) $(UI1).json $(UI2).json $(UI3).json $(UI4).json $(UI5).json $(UI6).json $(UI7).json $(UI8).json $(UI9).json $(UI10).json $(UI10I).json $(UI11).json $(UI11I).json $(UI12).json $(UI12I).json $(UI13).json $(UI14).json $(UI14I).json $(UI15).json $(UI16).json $(UI16I).json $(UI17).json $(UI18).json $(UI18I).json $(UI19).json $(UI20).json $(UI20I).json $(UI21).json $(UI22).json $(UI22I).json $(UI23).json $(UI24).json $(UI24I).json $(UI25).json $(UI26).json $(UI26I).json $(UI27).json $(UI28).json $(UI29).json $(UI30).json $(UI30I).json $(UI31).json $(UI32).json $(UI33).json $(UI34).json $(UI35).json $(UI36).json $(UI37).json $(UI38).json $(UI39).json $(UI43).json $(UILARGE).json $(FLAME).json $(ICON).json $(UI28I).json $(UI32I).json
	$(PYTHON) train/pack.py $(ASCII).json $(ASCII).nrt
	$(PYTHON) train/pack.py $(FULL).json $(FULL).nrt
	$(PYTHON) train/pack.py --bundle $(SPLIT) $(NETS) --gate $(GATE)
	$(PYTHON) train/pack.py --bundle $(PRIOR_SPLIT) $(PRIOR_NETS) --gate $(PRIOR_GATE)
	$(PYTHON) train/pack.py --drawing $(UI1).nrt $(UI1).json font/ui-1.txt
	$(PYTHON) train/pack.py --drawing $(UI2).nrt $(UI2).json font/ui-2.txt
	$(PYTHON) train/pack.py --drawing $(UI3).nrt $(UI3).json font/ui-3.txt
	$(PYTHON) train/pack.py --drawing $(UI4).nrt $(UI4).json font/ui-4.txt
	$(PYTHON) train/pack.py --drawing $(UI5).nrt $(UI5).json font/ui-5.txt
	$(PYTHON) train/pack.py --drawing $(UI6).nrt $(UI6).json font/ui-6.txt
	$(PYTHON) train/pack.py --drawing $(UI7).nrt $(UI7).json font/ui-7.txt
	$(PYTHON) train/pack.py --drawing $(UI8).nrt $(UI8).json font/ui-8.txt
	$(PYTHON) train/pack.py --drawing $(UI9).nrt $(UI9).json font/ui-9.txt
	$(PYTHON) train/pack.py --drawing $(UI10).nrt $(UI10).json font/ui-10.txt
	$(PYTHON) train/pack.py --drawing $(UI10I).nrt $(UI10I).json font/ui-10-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI11).nrt $(UI11).json font/ui-11.txt
	$(PYTHON) train/pack.py --drawing $(UI11I).nrt $(UI11I).json font/ui-11-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI12).nrt $(UI12).json font/ui-12.txt
	$(PYTHON) train/pack.py --drawing $(UI12I).nrt $(UI12I).json font/ui-12-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI13).nrt $(UI13).json font/ui-13.txt
	$(PYTHON) train/pack.py --drawing $(UI14).nrt $(UI14).json font/ui-14.txt
	$(PYTHON) train/pack.py --drawing $(UI14I).nrt $(UI14I).json font/ui-14-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI15).nrt $(UI15).json font/ui-15.txt
	$(PYTHON) train/pack.py --drawing $(UI16).nrt $(UI16).json font/ui-16.txt
	$(PYTHON) train/pack.py --drawing $(UI16I).nrt $(UI16I).json font/ui-16-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI17).nrt $(UI17).json font/ui-17.txt
	$(PYTHON) train/pack.py --drawing $(UI18).nrt $(UI18).json font/ui-18.txt
	$(PYTHON) train/pack.py --drawing $(UI18I).nrt $(UI18I).json font/ui-18-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI19).nrt $(UI19).json font/ui-19.txt
	$(PYTHON) train/pack.py --drawing $(UI20).nrt $(UI20).json font/ui-20.txt
	$(PYTHON) train/pack.py --drawing $(UI20I).nrt $(UI20I).json font/ui-20-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI21).nrt $(UI21).json font/ui-21.txt
	$(PYTHON) train/pack.py --drawing $(UI22).nrt $(UI22).json font/ui-22.txt
	$(PYTHON) train/pack.py --drawing $(UI22I).nrt $(UI22I).json font/ui-22-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI23).nrt $(UI23).json font/ui-23.txt
	$(PYTHON) train/pack.py --drawing $(UI24).nrt $(UI24).json font/ui-24.txt
	$(PYTHON) train/pack.py --drawing $(UI24I).nrt $(UI24I).json font/ui-24-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI25).nrt $(UI25).json font/ui-25.txt
	$(PYTHON) train/pack.py --drawing $(UI26).nrt $(UI26).json font/ui-26.txt
	$(PYTHON) train/pack.py --drawing $(UI26I).nrt $(UI26I).json font/ui-26-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI27).nrt $(UI27).json font/ui-27.txt
	$(PYTHON) train/pack.py --drawing $(UI28).nrt $(UI28).json font/ui-28.txt
	$(PYTHON) train/pack.py --drawing $(UI29).nrt $(UI29).json font/ui-29.txt
	$(PYTHON) train/pack.py --drawing $(UI30).nrt $(UI30).json font/ui-30.txt
	$(PYTHON) train/pack.py --drawing $(UI28I).nrt $(UI28I).json font/ui-28-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI30I).nrt $(UI30I).json font/ui-30-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI32I).nrt $(UI32I).json font/ui-32-italic.txt
	$(PYTHON) train/pack.py --drawing $(UI31).nrt $(UI31).json font/ui-31.txt
	$(PYTHON) train/pack.py --drawing $(UI32).nrt $(UI32).json font/ui-32.txt
	$(PYTHON) train/pack.py --drawing $(UI33).nrt $(UI33).json font/ui-33.txt
	$(PYTHON) train/pack.py --drawing $(UI34).nrt $(UI34).json font/ui-34.txt
	$(PYTHON) train/pack.py --drawing $(UI35).nrt $(UI35).json font/ui-35.txt
	$(PYTHON) train/pack.py --drawing $(UI36).nrt $(UI36).json font/ui-36.txt
	$(PYTHON) train/pack.py --drawing $(UI37).nrt $(UI37).json font/ui-37.txt
	$(PYTHON) train/pack.py --drawing $(UI38).nrt $(UI38).json font/ui-38.txt
	$(PYTHON) train/pack.py --drawing $(UI39).nrt $(UI39).json font/ui-39.txt
	$(PYTHON) train/pack.py --drawing $(UI43).nrt $(UI43).json font/ui-43.txt
	$(PYTHON) train/pack.py --drawing-bundle $(UI33_V1).nrt font/ui-33.txt $(UI33_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI34_V1).nrt font/ui-34.txt $(UI34_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI35_V1).nrt font/ui-35.txt $(UI35_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI36_V1).nrt font/ui-36.txt $(UI36_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI37_V1).nrt font/ui-37.txt $(UI37_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI38_V1).nrt font/ui-38.txt $(UI38_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI39_V1).nrt font/ui-39.txt $(UI39_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI43_V1).nrt font/ui-43.txt $(UI43_V1_NETS)
	$(PYTHON) train/pack.py --drawing $(UILARGE).nrt $(UILARGE).json font/ui-large-advances.txt
	$(PYTHON) train/pack.py --drawing-bundle $(UI24_V1).nrt font/ui-24.txt $(UI24_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI24I_V1).nrt font/ui-24-italic.txt $(UI24I_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI27_V1).nrt font/ui-27.txt $(UI27_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI28_V1).nrt font/ui-28.txt $(UI28_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI28I_V1).nrt font/ui-28-italic.txt $(UI28I_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI29_V1).nrt font/ui-29.txt $(UI29_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI29I_V1).nrt font/ui-29-italic.txt $(UI29I_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI30_V1).nrt font/ui-30.txt $(UI30_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle $(UI30I_V1).nrt font/ui-30-italic.txt $(UI30I_V1_NETS)
	$(PYTHON) train/pack.py $(FLAME).json $(FLAME).nrt
	# A colour file is packed the same way: python3 train/pack.py colour.json colour.nrt
	# make test builds a small synthetic one under build/; $(FLAME) is a trained one.
	$(PYTHON) train/pack.py $(ICON).json $(ICON).nrt
	cd weights && sha256sum *.json *.nrt *.md > SHA256SUMS

test-rc9-italics: all
	@set -e; for em in $(RC9_ITALIC_SIZES); do \
		$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing weights/neuronte-ui$$em-italic-v0.nrt weights/neuronte-ui$$em-italic-v0.json font/ui-$$em-italic.txt; \
	done

# Seed 0 is the packed -v1 file; seed 1 is packed into build/ and held to the same gate.
test-faces-v1-192-256: build/libneuronte.so
	@set -e; for f in $(FACES_V1_192_256); do \
		t=font/$$(echo $$f | sed 's/^ui/ui-/').txt; \
		$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing weights/neuronte-$$f-v1.nrt weights/neuronte-$$f-v1.json $$t; \
		$(PYTHON) train/pack.py --drawing build/neuronte-$$f-v1.seed1.nrt weights/neuronte-$$f-v1.seed1.json $$t > /dev/null; \
		$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing build/neuronte-$$f-v1.seed1.nrt weights/neuronte-$$f-v1.seed1.json $$t; \
	done

pack-faces-v1-192-256:
	@set -e; for f in $(FACES_V1_192_256); do \
		$(PYTHON) train/pack.py --drawing weights/neuronte-$$f-v1.nrt weights/neuronte-$$f-v1.json font/$$(echo $$f | sed 's/^ui/ui-/').txt; \
	done

.PHONY: test-faces-v1-192-256 pack-faces-v1-192-256

test-rc9-emoji: all
	$(PYTHON) tests/check_emoji.py build/libneuronte.so $(RC9_EMOJI) $(RC9_EMOJI_NETS) --manifest font/emoji-manifest.json --target-cache build/emoji-target-cache --out build/emoji-publication-check.json

test-rc9: test-rc9-italics test-rc9-emoji test-rc9-braille all $(TESTS)
	$(PYTHON) tests/check_reference.py build/libneuronte.so $(RC9_ACCENT).json $(RC9_ACCENT).nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --bundle $(RC9_SPLIT) $(RC9_NETS) --gate $(RC9_GATE)
	$(PYTHON) tests/check_scripts.py build/libneuronte.so $(RC9_SPLIT) $(RC9_ACCENT).json
	./build/test_api $(RC9_SPLIT) --full --accent --pixel
	$(PYTHON) tests/check_reference.py build/libneuronte.so $(RC9_FULL).json $(RC9_FULL).nrt
	$(PYTHON) tests/check_scripts.py build/libneuronte.so $(RC9_FULL).nrt $(RC9_FULL).json --standalone
	./build/test_api $(RC9_FULL).nrt --full --accent

test-rc9-braille: build/libneuronte.so build/stream/libneuronte.so build/test_api
	$(PYTHON) tests/check_tiled.py build/libneuronte.so --stream build/stream/libneuronte.so --tiled $(BRAILLE_V1).json $(BRAILLE_V1).nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so $(BRAILLE_V1).json $(BRAILLE_V1).nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --bundle $(SPLIT_V6) $(NETS_V6) --gate $(RC9_GATE)
	$(PYTHON) tests/check_braille_v1.py build/libneuronte.so $(BRAILLE_V1).nrt $(SPLIT_V6) $(SPLIT)
	$(PYTHON) tests/check_scripts.py build/libneuronte.so $(SPLIT_V6) $(RC9_ACCENT).json
	./build/test_api $(SPLIT_V6) --full --accent --pixel

test-rc9-quality: all
	$(PYTHON) tools/mono-compare.py --library build/libneuronte.so --baseline weights/neuronte-full-v2.json --candidate $(RC9_FULL).json --set full --include-new --sizes 16,48 --samples 0 --minimum-iou .98 --out build/full-v3-quality.json

ui-metadata:
	$(PYTHON) tools/ui-metadata.py

test-ui-metadata:
	$(PYTHON) tools/ui-metadata.py --check

.PHONY: ui-metadata test-ui-metadata

test-widths: build/libneuronte.so build/test_widths
	./build/test_widths
	$(PYTHON) tests/check_widths.py build/libneuronte.so
	$(PYTHON) tests/check_bundle_counts.py build/libneuronte.so

test-tiled: build/libneuronte.so build/stream/libneuronte.so build/test_tiled
	./build/test_tiled
	$(PYTHON) tests/check_tiled.py build/libneuronte.so --stream build/stream/libneuronte.so

.PHONY: test-tiled

# A face cut into nets: a drawing file of one bundle and an advance table.
test-face-bundle: build/libneuronte.so build/test_tiled
	./build/test_tiled
	$(PYTHON) tests/check_face_bundle.py build/libneuronte.so

.PHONY: test-face-bundle

# The desktop faces v1: every character of both seeds exactly its drawing.
test-faces-v1: build/libneuronte.so
	mkdir -p build/faces-v1
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI24_V1).nrt font/ui-24.txt $(UI24_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1/neuronte-ui24-v1.seed1.nrt font/ui-24.txt $(UI24_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1/neuronte-ui24-v1.seed1.nrt font/ui-24.txt $(UI24_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI24I_V1).nrt font/ui-24-italic.txt $(UI24I_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1/neuronte-ui24-italic-v1.seed1.nrt font/ui-24-italic.txt $(UI24I_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1/neuronte-ui24-italic-v1.seed1.nrt font/ui-24-italic.txt $(UI24I_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI27_V1).nrt font/ui-27.txt $(UI27_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1/neuronte-ui27-v1.seed1.nrt font/ui-27.txt $(UI27_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1/neuronte-ui27-v1.seed1.nrt font/ui-27.txt $(UI27_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI28_V1).nrt font/ui-28.txt $(UI28_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1/neuronte-ui28-v1.seed1.nrt font/ui-28.txt $(UI28_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1/neuronte-ui28-v1.seed1.nrt font/ui-28.txt $(UI28_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI28I_V1).nrt font/ui-28-italic.txt $(UI28I_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1/neuronte-ui28-italic-v1.seed1.nrt font/ui-28-italic.txt $(UI28I_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1/neuronte-ui28-italic-v1.seed1.nrt font/ui-28-italic.txt $(UI28I_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI29_V1).nrt font/ui-29.txt $(UI29_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1/neuronte-ui29-v1.seed1.nrt font/ui-29.txt $(UI29_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1/neuronte-ui29-v1.seed1.nrt font/ui-29.txt $(UI29_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI29I_V1).nrt font/ui-29-italic.txt $(UI29I_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1/neuronte-ui29-italic-v1.seed1.nrt font/ui-29-italic.txt $(UI29I_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1/neuronte-ui29-italic-v1.seed1.nrt font/ui-29-italic.txt $(UI29I_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI30_V1).nrt font/ui-30.txt $(UI30_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1/neuronte-ui30-v1.seed1.nrt font/ui-30.txt $(UI30_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1/neuronte-ui30-v1.seed1.nrt font/ui-30.txt $(UI30_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI30I_V1).nrt font/ui-30-italic.txt $(UI30I_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1/neuronte-ui30-italic-v1.seed1.nrt font/ui-30-italic.txt $(UI30I_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1/neuronte-ui30-italic-v1.seed1.nrt font/ui-30-italic.txt $(UI30I_V1_SEED1)

.PHONY: test-faces-v1

# Seed 0 is the packed -v1 file; seed 1 is packed into build/ and held to the
# same gate: every letter regular and bold exactly the face's pixels.
test-faces-wide-v1: build/libneuronte.so
	@set -e; for e in $(FACES_WIDE_V1); do f=$${e%:*}; k=$${e#*:}; \
		t=font/$$(echo $$f | sed 's/^ui/ui-/').txt; n0=; n1=; i=0; \
		while [ $$i -lt $$k ]; do n0="$$n0 weights/neuronte-$$f-v1-p$$i.json"; \
			n1="$$n1 weights/neuronte-$$f-v1-p$$i.seed1.json"; i=$$((i + 1)); done; \
		echo "$$f seed 0"; \
		$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle weights/neuronte-$$f-v1.nrt $$t $$n0; \
		$(PYTHON) train/pack.py --drawing-bundle build/neuronte-$$f-v1.seed1.nrt $$t $$n1 > /dev/null; \
		echo "$$f seed 1"; \
		$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/neuronte-$$f-v1.seed1.nrt $$t $$n1; \
	done

pack-faces-wide-v1:
	@set -e; for e in $(FACES_WIDE_V1); do f=$${e%:*}; k=$${e#*:}; n=; i=0; \
		while [ $$i -lt $$k ]; do n="$$n weights/neuronte-$$f-v1-p$$i.json"; i=$$((i + 1)); done; \
		$(PYTHON) train/pack.py --drawing-bundle weights/neuronte-$$f-v1.nrt font/$$(echo $$f | sed 's/^ui/ui-/').txt $$n; \
	done

.PHONY: test-faces-wide-v1 pack-faces-wide-v1

# The desktop faces v1 at 33-39 and 43 px: every character of both seeds exactly its drawing.
test-faces-v1-h512: build/libneuronte.so
	mkdir -p build/faces-v1-h512
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI33_V1).nrt font/ui-33.txt $(UI33_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1-h512/neuronte-ui33-v1.seed1.nrt font/ui-33.txt $(UI33_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1-h512/neuronte-ui33-v1.seed1.nrt font/ui-33.txt $(UI33_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI34_V1).nrt font/ui-34.txt $(UI34_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1-h512/neuronte-ui34-v1.seed1.nrt font/ui-34.txt $(UI34_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1-h512/neuronte-ui34-v1.seed1.nrt font/ui-34.txt $(UI34_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI35_V1).nrt font/ui-35.txt $(UI35_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1-h512/neuronte-ui35-v1.seed1.nrt font/ui-35.txt $(UI35_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1-h512/neuronte-ui35-v1.seed1.nrt font/ui-35.txt $(UI35_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI36_V1).nrt font/ui-36.txt $(UI36_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1-h512/neuronte-ui36-v1.seed1.nrt font/ui-36.txt $(UI36_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1-h512/neuronte-ui36-v1.seed1.nrt font/ui-36.txt $(UI36_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI37_V1).nrt font/ui-37.txt $(UI37_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1-h512/neuronte-ui37-v1.seed1.nrt font/ui-37.txt $(UI37_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1-h512/neuronte-ui37-v1.seed1.nrt font/ui-37.txt $(UI37_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI38_V1).nrt font/ui-38.txt $(UI38_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1-h512/neuronte-ui38-v1.seed1.nrt font/ui-38.txt $(UI38_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1-h512/neuronte-ui38-v1.seed1.nrt font/ui-38.txt $(UI38_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI39_V1).nrt font/ui-39.txt $(UI39_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1-h512/neuronte-ui39-v1.seed1.nrt font/ui-39.txt $(UI39_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1-h512/neuronte-ui39-v1.seed1.nrt font/ui-39.txt $(UI39_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $(UI43_V1).nrt font/ui-43.txt $(UI43_V1_NETS)
	$(PYTHON) train/pack.py --drawing-bundle build/faces-v1-h512/neuronte-ui43-v1.seed1.nrt font/ui-43.txt $(UI43_V1_SEED1)
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1-h512/neuronte-ui43-v1.seed1.nrt font/ui-43.txt $(UI43_V1_SEED1)

.PHONY: test-faces-v1-h512

# Small desktop faces v1: every character of both seeds exactly its drawing at its em.
test-faces-v1-small: build/libneuronte.so
	@set -e; mkdir -p build/faces-v1-small; for spec in $(FACES_V1_SMALL); do \
		f=$${spec%:*}; k=$${spec#*:}; n=weights/neuronte-$$f-v1; t=font/$$(echo $$f | sed 's/^ui/ui-/').txt; \
		m0=; m1=; g=0; while [ $$g -lt $$k ]; do m0="$$m0 $$n-g$$g.json"; m1="$$m1 $$n.seed1-g$$g.json"; g=$$((g+1)); done; \
		if [ $$k = 1 ]; then \
			$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $$n.nrt $$m0 $$t; \
			$(PYTHON) train/pack.py --drawing build/faces-v1-small/$$f.seed1.nrt $$m1 $$t > /dev/null; \
			$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing build/faces-v1-small/$$f.seed1.nrt $$m1 $$t; \
		else \
			$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle $$n.nrt $$t $$m0; \
			$(PYTHON) train/pack.py --drawing-bundle build/faces-v1-small/$$f.seed1.nrt $$t $$m1 > /dev/null; \
			$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing-bundle build/faces-v1-small/$$f.seed1.nrt $$t $$m1; \
		fi; \
	done

pack-faces-v1-small:
	@set -e; mkdir -p build/faces-v1-small; for spec in $(FACES_V1_SMALL); do \
		f=$${spec%:*}; k=$${spec#*:}; n=weights/neuronte-$$f-v1; t=font/$$(echo $$f | sed 's/^ui/ui-/').txt; \
		m0=; m1=; g=0; while [ $$g -lt $$k ]; do m0="$$m0 $$n-g$$g.json"; m1="$$m1 $$n.seed1-g$$g.json"; g=$$((g+1)); done; \
		if [ $$k = 1 ]; then $(PYTHON) train/pack.py --drawing $$n.nrt $$m0 $$t; \
		else $(PYTHON) train/pack.py --drawing-bundle $$n.nrt $$t $$m0; fi; \
	done

.PHONY: test-faces-v1-small pack-faces-v1-small

test-known-bundle: build/libneuronte.so
	$(PYTHON) tests/check_known_bundle.py build/libneuronte.so

.PHONY: test-known-bundle

# The opt-in untrained mark: neuronte_untrained() and neuronte_set_untrained().
test-untrained: build/libneuronte.so
	$(PYTHON) tests/check_untrained.py build/libneuronte.so

.PHONY: test-untrained

test-ascii-next: build/libneuronte.so build/test_api
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_ascii_next.py build/libneuronte.so
	./build/test_api weights/neuronte-split-ascii-groups-v1.nrt --full --accent --pixel
	./build/test_api weights/neuronte-split-ascii-spatial-v1.nrt --full --accent --pixel

.PHONY: test-ascii-next

test-split-v7: build/libneuronte.so build/test_api
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_split_v7.py build/libneuronte.so
	$(PYTHON) tests/check_braille_v1.py build/libneuronte.so $(BRAILLE_V1).nrt weights/neuronte-split-v7.nrt weights/neuronte-split-ascii-groups-v1.nrt
	./build/test_api weights/neuronte-split-v7.nrt --full --accent --pixel

.PHONY: test-split-v7

pack-emoji-v1: $(EMOJI_V1_NETS)
	$(PYTHON) tools/pack-bundle-members.py $(EMOJI_V1) $(EMOJI_V1_NETS)

test-emoji-v1: all
	$(PYTHON) tests/check_emoji.py build/libneuronte.so $(EMOJI_V1) $(EMOJI_V1_NETS) --manifest font/emoji-manifest.json --experts 12 --target-cache build/emoji-target-cache --out build/emoji-v1-check.json

.PHONY: pack-emoji-v1 test-emoji-v1

test-split-v7-symbol: build/libneuronte.so build/test_api
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_split_v7_symbol.py build/libneuronte.so
	./build/test_api weights/neuronte-split-v7-symbol-v1.nrt --full --accent --pixel

.PHONY: test-split-v7-symbol

test-split-v8: build/libneuronte.so build/test_api
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_split_v8.py build/libneuronte.so
	./build/test_api weights/neuronte-split-v8.nrt --full --accent --pixel

pack-split-v8:
	$(PYTHON) train/build_split_v8.py

.PHONY: test-split-v8 pack-split-v8

# split-v9: split-v8 with the terminal symbol, Greek and Cyrillic group nets.
TERMINAL_V1 = $(foreach g,0 1 2 3 4 5 6 7 8,weights/neuronte-tsymbol-v1-g$(g)) \
	$(foreach g,0 1,weights/neuronte-tgreek-v1-g$(g)) $(foreach g,0 1 2,weights/neuronte-tcyrillic-v1-g$(g))

test-split-v9: build/libneuronte.so build/test_api
	@set -e; for n in $(TERMINAL_V1); do \
		$(PYTHON) train/pack.py $$n.json build/$$(basename $$n).nrt; \
		$(PYTHON) tests/check_reference.py build/libneuronte.so $$n.json build/$$(basename $$n).nrt; \
	done
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_split_v9.py build/libneuronte.so
	./build/test_api weights/neuronte-split-v9.nrt --full --accent --pixel

pack-split-v9:
	$(PYTHON) train/build_split_v9.py

.PHONY: test-split-v9 pack-split-v9

test-symbol-v1: build/libneuronte.so build/test_api
	@set -e; for g in 0 1 2 3; do \
		$(PYTHON) train/pack.py $(SYMBOL_V1)-g$$g.json build/symbol-v1-g$$g.nrt; \
		$(PYTHON) tests/check_reference.py build/libneuronte.so $(SYMBOL_V1)-g$$g.json build/symbol-v1-g$$g.nrt; \
	done
	$(PYTHON) tests/check_symbol_v1.py build/libneuronte.so
	./build/test_api $(SYMBOL_V1_SPLIT) --full --accent --pixel

.PHONY: test-symbol-v1

# The narrower colour nets of 0.1.2, each beside the file it may replace.
test-colour-marks: build/libneuronte.so
	sha256sum -c --quiet weights/neuronte-pointer-v1.sha256
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_pointer.py build/libneuronte.so weights/neuronte-pointer-v1.json weights/neuronte-pointer-v1.nrt --max-xor 16:0,0 --max-xor 32:1,2
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_pointer.py build/libneuronte.so weights/neuronte-pointer-v1.seed1.json weights/neuronte-pointer-v1.seed1.nrt --max-xor 16:0,0 --max-xor 32:1,2
	$(PYTHON) tests/check_reference.py build/libneuronte.so weights/neuronte-pointer-v1.json weights/neuronte-pointer-v1.nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so weights/neuronte-pointer-v1.seed1.json weights/neuronte-pointer-v1.seed1.nrt
	sha256sum -c --quiet weights/neuronte-flame-v1.sha256
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_flame.py build/libneuronte.so weights/neuronte-flame-v1.json weights/neuronte-flame-v1.nrt --max-xor 16:7,2,0 --max-xor 32:6,3,5
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_flame.py build/libneuronte.so weights/neuronte-flame-v1.seed1.json weights/neuronte-flame-v1.seed1.nrt --max-xor 16:7,2,0 --max-xor 32:6,3,5
	$(PYTHON) tests/check_reference.py build/libneuronte.so weights/neuronte-flame-v1.json weights/neuronte-flame-v1.nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so weights/neuronte-flame-v1.seed1.json weights/neuronte-flame-v1.seed1.nrt
	sha256sum -c --quiet weights/neuronte-icon-v2.sha256
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_icon_quality.py build/libneuronte.so weights/neuronte-icon-v2.g0.json weights/neuronte-icon-v2.nrt --also weights/neuronte-icon-v2.g1.json --also weights/neuronte-icon-v2.g2.json --also weights/neuronte-icon-v2.g3.json
	$(PYTHON) tests/check_reference.py build/libneuronte.so --bundle weights/neuronte-icon-v2.nrt weights/neuronte-icon-v2.g0.json weights/neuronte-icon-v2.g1.json weights/neuronte-icon-v2.g2.json weights/neuronte-icon-v2.g3.json
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_icon_quality.py build/libneuronte.so weights/neuronte-icon-v2.seed1.g0.json weights/neuronte-icon-v2.seed1.nrt --also weights/neuronte-icon-v2.seed1.g1.json --also weights/neuronte-icon-v2.seed1.g2.json --also weights/neuronte-icon-v2.seed1.g3.json
	$(PYTHON) tests/check_reference.py build/libneuronte.so --bundle weights/neuronte-icon-v2.seed1.nrt weights/neuronte-icon-v2.seed1.g0.json weights/neuronte-icon-v2.seed1.g1.json weights/neuronte-icon-v2.seed1.g2.json weights/neuronte-icon-v2.seed1.g3.json

.PHONY: test-colour-marks

.PHONY: test-widths

# The packed text mask calls against a pixel loop.
test-bits: build/libneuronte.so
	$(PYTHON) tests/check_bits.py build/libneuronte.so
.PHONY: test-bits

test: all $(TESTS) test-bits test-widths test-tiled test-rc9 test-rc9-quality test-ui-metadata test-bench-errors test-ascii-next test-split-v7 test-face-bundle test-symbol-v1 test-split-v7-symbol test-split-v8 test-split-v9 test-faces-v1 test-faces-v1-192-256 test-known-bundle test-untrained test-faces-wide-v1 test-faces-v1-h512 test-colour-marks test-faces-v1-small test-emoji-v1
	cd weights && sha256sum -c --quiet SHA256SUMS
	# The pointer net keeps its own list, with paths from the top of the tree.
	sha256sum -c --quiet weights/neuronte-pointer-v0.sha256
	$(PYTHON) train/glyphs.py > /dev/null
	./build/test_utf8
	./build/test_api $(ASCII).nrt
	./build/test_api $(FULL).nrt --full --accent
	./build/test_api $(PRIOR_SPLIT) --full --accent --pixel
	$(PYTHON) tests/check_styles.py build/libneuronte.so
	$(PYTHON) tests/check_halves.py build/libneuronte.so
	$(PYTHON) tests/check_reference.py build/libneuronte.so $(ASCII).json $(ASCII).nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so $(FULL).json $(FULL).nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --bundle $(PRIOR_SPLIT) $(PRIOR_NETS) --gate $(PRIOR_GATE)
	$(PYTHON) tests/colour_fixture.py build/colour-fixture.nrt
	$(PYTHON) tests/check_colour_sources.py
	$(PYTHON) tests/check_icon_gate.py
	./build/test_api build/colour-fixture.nrt --colour
	$(PYTHON) tests/check_reference.py build/libneuronte.so build/colour-fixture.json build/colour-fixture.nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so $(FLAME).json $(FLAME).nrt
	./build/test_api $(ICON).nrt --colour --trained
	$(PYTHON) tests/check_icon_quality.py build/libneuronte.so $(ICON).json $(ICON).nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so $(ICON).json $(ICON).nrt
	$(PYTHON) tests/check_advances.py build/libneuronte.so $(ASCII).json
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI1).nrt $(UI1).json font/ui-1.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI2).nrt $(UI2).json font/ui-2.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI3).nrt $(UI3).json font/ui-3.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI4).nrt $(UI4).json font/ui-4.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI5).nrt $(UI5).json font/ui-5.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI6).nrt $(UI6).json font/ui-6.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI7).nrt $(UI7).json font/ui-7.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI8).nrt $(UI8).json font/ui-8.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI9).nrt $(UI9).json font/ui-9.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI10).nrt $(UI10).json font/ui-10.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI10I).nrt $(UI10I).json font/ui-10-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI11).nrt $(UI11).json font/ui-11.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI11I).nrt $(UI11I).json font/ui-11-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI12).nrt $(UI12).json font/ui-12.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI12I).nrt $(UI12I).json font/ui-12-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI13).nrt $(UI13).json font/ui-13.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI14).nrt $(UI14).json font/ui-14.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI14I).nrt $(UI14I).json font/ui-14-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI15).nrt $(UI15).json font/ui-15.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI16).nrt $(UI16).json font/ui-16.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI16I).nrt $(UI16I).json font/ui-16-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI17).nrt $(UI17).json font/ui-17.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI18).nrt $(UI18).json font/ui-18.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI18I).nrt $(UI18I).json font/ui-18-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI19).nrt $(UI19).json font/ui-19.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI20).nrt $(UI20).json font/ui-20.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI20I).nrt $(UI20I).json font/ui-20-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI21).nrt $(UI21).json font/ui-21.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI22).nrt $(UI22).json font/ui-22.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI22I).nrt $(UI22I).json font/ui-22-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI23).nrt $(UI23).json font/ui-23.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI24).nrt $(UI24).json font/ui-24.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI24I).nrt $(UI24I).json font/ui-24-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI25).nrt $(UI25).json font/ui-25.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI26).nrt $(UI26).json font/ui-26.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI26I).nrt $(UI26I).json font/ui-26-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI27).nrt $(UI27).json font/ui-27.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI28).nrt $(UI28).json font/ui-28.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI29).nrt $(UI29).json font/ui-29.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI30).nrt $(UI30).json font/ui-30.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI28I).nrt $(UI28I).json font/ui-28-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI30I).nrt $(UI30I).json font/ui-30-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI32I).nrt $(UI32I).json font/ui-32-italic.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI31).nrt $(UI31).json font/ui-31.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI32).nrt $(UI32).json font/ui-32.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI33).nrt $(UI33).json font/ui-33.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI34).nrt $(UI34).json font/ui-34.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI35).nrt $(UI35).json font/ui-35.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI36).nrt $(UI36).json font/ui-36.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI37).nrt $(UI37).json font/ui-37.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI38).nrt $(UI38).json font/ui-38.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI39).nrt $(UI39).json font/ui-39.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI43).nrt $(UI43).json font/ui-43.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UILARGE).nrt $(UILARGE).json font/ui-large-advances.txt

bench: build/neuronte-bench
	./build/neuronte-bench $(ASCII).nrt
	./build/neuronte-bench $(FULL).nrt
	./build/neuronte-bench $(FULL).nrt $(SPLIT)

clean:
	rm -rf build

.PHONY: all demo pack pack-rc9 pack-rc9-italics pack-rc9-emoji test test-rc9 test-rc9-italics test-rc9-emoji test-rc9-braille test-rc9-quality bench clean

# Video is an optional Python/numpy/scipy tool; its tests are separate from
# the dependency-light C/font acceptance suite.
.PHONY: test-video
.PHONY: test-bench-errors
test-bench-errors:
	CC="$(CC)" $(PYTHON) tests/check_bench_errors.py

test-video: build/libneuronte.so build/video-decoder-bench build/test_video build/test_video_portable
	./build/test_video
	./build/test_video_portable
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_video.py
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_video_decoder.py
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_reference.py build/libneuronte.so --bundle weights/neuronte-video-masks-v0.nrt weights/neuronte-video-pixel-v1.json weights/neuronte-video-ascii-v0.json --fallback 1

# In-process decoding (src/media.c) links FFmpeg 7.1's libraries, which
# libneuronte itself never does. It is optional: without it the player runs
# the ffmpeg command. Building it needs the libav*-dev packages.
PKG_CONFIG ?= pkg-config
MEDIA_PACKAGES = libavformat libavcodec libavfilter libavutil
MEDIA_CFLAGS ?= $(shell $(PKG_CONFIG) --cflags $(MEDIA_PACKAGES))
MEDIA_LIBS ?= $(shell $(PKG_CONFIG) --libs $(MEDIA_PACKAGES))
MEDIA_SANITIZE = -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=undefined

.PHONY: media test-media
media: build/libneuronte-media.so build/neuronte-media-decode

build/libneuronte-media.so: src/media.c include/neuronte_media.h | build
	$(CC) $(NRT_CFLAGS) $(MEDIA_CFLAGS) $(LDFLAGS) -shared -o $@ $< $(MEDIA_LIBS) -pthread -lm

build/neuronte-media-decode: tools/neuronte-media-decode.c include/neuronte_media.h build/libneuronte-media.so
	$(CC) $(NRT_CFLAGS) $(LDFLAGS) -o $@ $< -Lbuild -lneuronte-media -Wl,-rpath,'$$ORIGIN'

# The same decoder and harness with AddressSanitizer and UBSan, for the
# media checks to run against.
build/sanitize/neuronte-media-decode: tools/neuronte-media-decode.c src/media.c include/neuronte_media.h | build
	mkdir -p build/sanitize
	$(CC) -std=c11 -Wall -Wextra -Wpedantic -Iinclude $(MEDIA_CFLAGS) $(MEDIA_SANITIZE) -o $@ tools/neuronte-media-decode.c src/media.c $(MEDIA_LIBS) -pthread -lm

build/sanitize/test_media: tests/test_media.c src/media.c include/neuronte_media.h | build
	mkdir -p build/sanitize
	$(CC) -std=c11 -Wall -Wextra -Wpedantic -Iinclude $(MEDIA_CFLAGS) $(MEDIA_SANITIZE) -o $@ tests/test_media.c src/media.c $(MEDIA_LIBS) -pthread -lm

# ThreadSanitizer for the decoder thread and its reader. FFmpeg's own
# threads are kept out of that run (TEST_MEDIA_THREADS=1): the sanitizer
# cannot see the atomics its uninstrumented libraries synchronize with.
build/tsan/test_media: tests/test_media.c src/media.c include/neuronte_media.h | build
	mkdir -p build/tsan
	$(CC) -std=c11 -Wall -Wextra -Wpedantic -Iinclude $(MEDIA_CFLAGS) -O1 -g -fsanitize=thread -o $@ tests/test_media.c src/media.c $(MEDIA_LIBS) -pthread -lm

test-media: media build/libneuronte.so build/sanitize/neuronte-media-decode build/sanitize/test_media build/tsan/test_media
	OPENBLAS_NUM_THREADS=1 $(PYTHON) tests/check_media.py

build/video-decoder-bench: tools/neuronte-video-decoder-bench.c | build
	$(CC) $(NRT_CFLAGS) -o $@ $< $(LDLIBS)

# The same compositor without its SIMD paths, so both are checked against
# the same fixtures on machines that have the SIMD path.
build/video-portable.o: src/video.c include/neuronte.h | build
	$(CC) $(NRT_CFLAGS) -DNRT_VIDEO_PORTABLE -c -o $@ $<

build/test_video_portable: tests/test_video.c build/video-portable.o
	$(CC) $(NRT_CFLAGS) -o $@ $^ $(LDLIBS)
