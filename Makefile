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
UI10 = weights/neuronte-ui10-v0
UI11 = weights/neuronte-ui11-v0
UI12 = weights/neuronte-ui12-v0
UI14 = weights/neuronte-ui14-v0
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
pack: $(ASCII).json $(FULL).json $(NETS) $(GATE) $(UI10).json $(UI11).json $(UI12).json $(UI14).json
	$(PYTHON) train/pack.py $(ASCII).json $(ASCII).nrt
	$(PYTHON) train/pack.py $(FULL).json $(FULL).nrt
	$(PYTHON) train/pack.py --bundle $(SPLIT) $(NETS) --gate $(GATE)
	$(PYTHON) train/pack.py --drawing $(UI10).nrt $(UI10).json font/ui-10.txt
	$(PYTHON) train/pack.py --drawing $(UI11).nrt $(UI11).json font/ui-11.txt
	$(PYTHON) train/pack.py --drawing $(UI12).nrt $(UI12).json font/ui-12.txt
	$(PYTHON) train/pack.py --drawing $(UI14).nrt $(UI14).json font/ui-14.txt
	cd weights && sha256sum *.json *.nrt > SHA256SUMS

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
	$(PYTHON) tests/check_advances.py build/libneuronte.so $(ASCII).json
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI10).nrt $(UI10).json font/ui-10.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI11).nrt $(UI11).json font/ui-11.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI12).nrt $(UI12).json font/ui-12.txt
	$(PYTHON) tests/check_reference.py build/libneuronte.so --drawing $(UI14).nrt $(UI14).json font/ui-14.txt

bench: build/neuronte-bench
	./build/neuronte-bench $(ASCII).nrt
	./build/neuronte-bench $(FULL).nrt
	./build/neuronte-bench $(FULL).nrt $(SPLIT)

clean:
	rm -rf build

.PHONY: all demo pack test bench clean
