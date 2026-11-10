CC ?= cc
CFLAGS ?= -O3
# Flags the build needs, kept apart so CFLAGS=... on the command line adds to them.
NRT_CFLAGS = -std=c11 -Wall -Wextra -Wpedantic -fPIC -Iinclude $(CPPFLAGS) $(CFLAGS)
LDLIBS = -lm
PYTHON ?= python3

WEIGHTS = weights/neuronte-ascii-v0
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

demo: build/neuronte-demo

build/kitty_framebuffer.o: $(KITTYFB_DIR)/src/kitty_framebuffer.c | build
	$(CC) -std=c11 -O2 -fPIC -pthread -D_POSIX_C_SOURCE=200809L -D_DEFAULT_SOURCE \
		-I$(KITTYFB_DIR)/include -c -o $@ $<

build/neuronte-demo: demo/neuronte-demo.c build/libneuronte.a build/kitty_framebuffer.o
	$(CC) $(NRT_CFLAGS) -pthread -I$(KITTYFB_DIR)/include -o $@ $< build/kitty_framebuffer.o \
		build/libneuronte.a $(LDLIBS) -lz

# Rebuild the packed weights from the JSON the trainer writes.
pack: $(WEIGHTS).json
	$(PYTHON) train/pack.py $(WEIGHTS).json $(WEIGHTS).nrt
	cd weights && sha256sum neuronte-ascii-v0.json neuronte-ascii-v0.nrt > SHA256SUMS

test: all $(TESTS)
	cd weights && sha256sum -c --quiet SHA256SUMS
	./build/test_utf8
	./build/test_api $(WEIGHTS).nrt
	$(PYTHON) tests/check_reference.py build/libneuronte.so $(WEIGHTS).json $(WEIGHTS).nrt

bench: build/neuronte-bench
	./build/neuronte-bench $(WEIGHTS).nrt

clean:
	rm -rf build

.PHONY: all demo pack test bench clean
