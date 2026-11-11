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
ACCENT = weights/neuronte-accent-v1
PIXEL = weights/neuronte-pixel-v1
BRAILLE = weights/neuronte-braille-v0
GATE = weights/neuronte-gate-v3.json
SPLIT = weights/neuronte-split-v4.nrt
NETS = $(ASCII).json $(DRAW).json $(SYMBOL).json $(ACCENT).json $(PIXEL).json $(BRAILLE).json
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
UI30I = weights/neuronte-ui30-italic-v0
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
OBJS = build/neuronte.o build/utf8.o
TOOLS = build/neuronte-render build/neuronte-bench
TESTS = build/test_utf8 build/test_api

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
pack: $(ASCII).json $(FULL).json $(NETS) $(GATE) $(UI1).json $(UI2).json $(UI3).json $(UI4).json $(UI5).json $(UI6).json $(UI7).json $(UI8).json $(UI9).json $(UI10).json $(UI10I).json $(UI11).json $(UI11I).json $(UI12).json $(UI12I).json $(UI13).json $(UI14).json $(UI14I).json $(UI15).json $(UI16).json $(UI16I).json $(UI17).json $(UI18).json $(UI18I).json $(UI19).json $(UI20).json $(UI20I).json $(UI21).json $(UI22).json $(UI22I).json $(UI23).json $(UI24).json $(UI24I).json $(UI25).json $(UI26).json $(UI26I).json $(UI27).json $(UI28).json $(UI29).json $(UI30).json $(UI30I).json $(UI31).json $(UI32).json $(UI33).json $(UI34).json $(UI35).json $(UI36).json $(UI37).json $(UI38).json $(UI39).json $(UI43).json
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
	$(PYTHON) train/pack.py --drawing $(UI30I).nrt $(UI30I).json font/ui-30-italic.txt
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
	cd weights && sha256sum *.json *.nrt > SHA256SUMS
	# A colour file is packed the same way: python3 train/pack.py colour.json colour.nrt
	# make test builds a small synthetic one under build/. No icon net is trained here.

test: all $(TESTS)
	cd weights && sha256sum -c --quiet SHA256SUMS
	$(PYTHON) train/glyphs.py > /dev/null
	./build/test_utf8
	./build/test_api $(ASCII).nrt
	./build/test_api $(FULL).nrt --full --accent
	./build/test_api $(SPLIT) --full --accent --pixel
	$(PYTHON) tests/check_reference.py build/libneuronte.so $(ASCII).json $(ASCII).nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so $(FULL).json $(FULL).nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --bundle $(SPLIT) $(NETS) --gate $(GATE)
	$(PYTHON) tests/colour_fixture.py build/colour-fixture.nrt
	./build/test_api build/colour-fixture.nrt --colour
	$(PYTHON) tests/check_reference.py build/libneuronte.so build/colour-fixture.json build/colour-fixture.nrt
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
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI30I).nrt $(UI30I).json font/ui-30-italic.txt
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

bench: build/neuronte-bench
	./build/neuronte-bench $(ASCII).nrt
	./build/neuronte-bench $(FULL).nrt
	./build/neuronte-bench $(FULL).nrt $(SPLIT)

clean:
	rm -rf build

.PHONY: all demo pack test bench clean
