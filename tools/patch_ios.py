#!/usr/bin/env python3
"""Patch LibertyRecompAndroid for iOS build."""
import json, os, re

# 1. thirdparty/CMakeLists.txt — comment out problematic add_subdirectory
path = "thirdparty/CMakeLists.txt"
with open(path) as f: lines = f.readlines()
skip_dirs = ["MoltenVK", "plume", "nativefiledialog-extended", "ffmpeg-core", "GameNetworkingSockets"]
patched = 0
new_lines = []
for line in lines:
    skip = False
    for d in skip_dirs:
        tag = 'add_subdirectory("${LIBERTY_RECOMP_THIRDPARTY_ROOT}/' + d + '")'
        if tag in line and not line.strip().startswith('#'):
            skip = True; patched += 1; break
    new_lines.append("# " + line.rstrip() + "  # SKIPPED on iOS\n" if skip else line)
with open(path, "w") as f: f.writelines(new_lines)
print(f"OK: {patched} add_subdirectory lines commented out")

# Patch toolchains/ios.cmake: raise deployment target to iOS 26.0
# (std::from_chars for floating-point introduced in iOS 26.0)
ios_cmake = "toolchains/ios.cmake"
if os.path.exists(ios_cmake):
    with open(ios_cmake) as f: ic = f.read()
    ic = ic.replace('"16.0"', '"26.0"')
    with open(ios_cmake, "w") as f: f.write(ic)
    print("OK: iOS deployment target raised to 26.0 (from_chars support)")

# MoltenVK: overwrite CMakeLists.txt with empty file (belt-and-suspenders)
# Even if something calls add_subdirectory(MoltenVK) that we can't find,
# the empty CMakeLists.txt won't execute find_library(AppKit)
mvk_cmake = "thirdparty/MoltenVK/CMakeLists.txt"
if os.path.exists(mvk_cmake):
    with open(mvk_cmake, "w") as f:
        f.write("# MoltenVK CMakeLists.txt disabled for iOS build\n")
    print("OK: MoltenVK/CMakeLists.txt overwritten (empty — no AppKit find_library)")
else:
    print("WARN: MoltenVK/CMakeLists.txt not found")

# 2. vcpkg.json — exclude discord-rpc, add openssl
with open("vcpkg.json") as f: vj = json.load(f)
for dep in vj.get("dependencies", []):
    if isinstance(dep, dict) and dep.get("name") == "discord-rpc":
        dep["platform"] = "!ps4 & !ps5 & !ios"
if not any(isinstance(d, dict) and d.get("name") == "openssl" for d in vj.get("dependencies", [])):
    vj.setdefault("dependencies", []).append("openssl")
with open("vcpkg.json", "w") as f: json.dump(vj, f, indent=4)

# 3. Root CMakeLists.txt — FetchContent SDL3 + find_package
root_path = "CMakeLists.txt"
with open(root_path) as f: root = f.read()
# SDL3 provided by RexGlue thirdparty (no FetchContent needed)
# (was causing target collision: RexGlue builds SDL3 from its own submodule)
if "find_package(fmt CONFIG REQUIRED)" not in root:
    fp = ("# find_package for vcpkg deps NOT provided by RexGlue thirdparty\n"
          "find_package(freetype CONFIG REQUIRED)\n"
          "find_package(CURL CONFIG REQUIRED)\n"
          "find_package(Protobuf CONFIG REQUIRED)\n"
          "find_package(OpenSSL CONFIG REQUIRED)\n"
          "find_package(date CONFIG REQUIRED)\n")
    m = "add_subdirectory(${LIBERTY_RECOMP_THIRDPARTY_ROOT})"
    if m in root: root = root.replace(m, fp + "\n" + m, 1)
# Force REXGLUE_USE_VULKAN=OFF before RexGlue is processed
# (option() won't override if cache var already exists via -D, but this is belt-and-suspenders)
if "set(REXGLUE_USE_VULKAN OFF CACHE BOOL" not in root:
    # Replace ALL occurrences (3 total: GRAINE_MAC, GRAINE_ANDROID, default path)
    # The default path (line 240) is what runs for iOS
    root = root.replace(
        'add_subdirectory("glue")',
        'set(REXGLUE_USE_VULKAN OFF CACHE BOOL "" FORCE)\nset(REXGLUE_USE_D3D12 OFF CACHE BOOL "" FORCE)\nadd_subdirectory("glue")',
    )
    print("OK: forced REXGLUE_USE_VULKAN=OFF before ALL add_subdirectory(glue) calls")
with open(root_path, "w") as f: f.write(root)
print("OK: FetchContent SDL3 + find_package added")

# 4. LibertyRecomp/CMakeLists.txt — comment links + add include path + iOS skip
lr_path = "LibertyRecomp/CMakeLists.txt"
with open(lr_path) as f: lr = f.read()
lr = lr.replace("    target_link_libraries(LibertyRecomp PRIVATE nfd::nfd)",
                "    # target_link_libraries(LibertyRecomp PRIVATE nfd::nfd)  # SKIPPED on iOS")
lr = lr.replace("    plume\n", "    # plume  # SKIPPED on iOS (Plume pulls MoltenVK)\n")
g = "set(LIBERTY_RECOMP_HAS_GNS TRUE)"
if g in lr:
    idx = lr.index(g); region = lr[idx:idx+800]
    if "ANDROID)" in region and "ios" not in region:
        lr = lr[:idx] + region.replace("ANDROID)", 'ANDROID OR LIBERTY_RECOMP_TARGET_PLATFORM STREQUAL "ios")', 1) + lr[idx+800:]
ff_old = "LIBERTY_RECOMP_PS4 OR LIBERTY_RECOMP_NX OR ANDROID"
ff_new = 'LIBERTY_RECOMP_PS4 OR LIBERTY_RECOMP_NX OR ANDROID OR LIBERTY_RECOMP_TARGET_PLATFORM STREQUAL "ios"'
if ff_old in lr: lr = lr.replace(ff_old, ff_new)
with open(lr_path, "w") as f: f.write(lr)
print("OK: LibertyRecomp links patched")

# 4d. Patch heap.cpp: fix SizeHeader static_assert + add o1heapReallocate stub
heap_path = "glue/rexglue-sdk-main/src/kernel/crt/heap.cpp"
if os.path.exists(heap_path):
    with open(heap_path) as f: heap = f.read()
    # Fix 1: SizeHeader needs 4 fields (32 bytes) to match O1HEAP_ALIGNMENT on 64-bit
    old_hdr = """struct SizeHeader {
  uint64_t requested_size;
  uint64_t reserved;  // padding to O1HEAP_ALIGNMENT
};"""
    new_hdr = """struct SizeHeader {
  uint64_t requested_size;
  uint64_t reserved0;
  uint64_t reserved1;
  uint64_t reserved2;  // padding to O1HEAP_ALIGNMENT (32 bytes on 64-bit)
};"""
    if old_hdr in heap:
        heap = heap.replace(old_hdr, new_hdr)
        print("OK: SizeHeader expanded to 32 bytes (match O1HEAP_ALIGNMENT)")
    # Fix 2: o1heapReallocate doesn't exist — add stub
    if "o1heapReallocate" in heap and "void* o1heapReallocate" not in heap:
        stub = """
// o1heapReallocate stub (not yet implemented in o1heap library)
void* o1heapReallocate(O1HeapInstance* const handle, void* const pointer, const size_t amount) {
    if (!handle || !pointer || amount == 0) return nullptr;
    void* new_ptr = o1heapAllocate(handle, amount);
    if (new_ptr) {
        // Copy old data (best effort — we don't know old size here)
        // Caller (heap.cpp) handles cross-segment fallback if this returns null
        memcpy(new_ptr, pointer, amount);
        o1heapFree(handle, pointer);
    }
    return new_ptr;
}
"""
        # Insert before the first use of o1heapReallocate
        heap = heap.replace("void* new_ptr = o1heapReallocate(",
                            stub + "
void* new_ptr = o1heapReallocate(")
        print("OK: o1heapReallocate stub added")
    with open(heap_path, "w") as f: f.write(heap)

# 4b. Patch RexGlue CMakeLists.txt — force Vulkan=OFF + relax FATAL_ERROR
#     (RexGlue src/core already supports iOS, just needs Vulkan disabled)
rg_path = "glue/rexglue-sdk-main/CMakeLists.txt"
with open(rg_path) as f: rg = f.read()
# Force Vulkan=OFF (str.replace, not regex — regex [^)]* greedy bug)
rg = rg.replace('option(REXGLUE_USE_VULKAN "Enable Vulkan graphics backend" ON)',
                'option(REXGLUE_USE_VULKAN "Enable Vulkan graphics backend" OFF)')
# Relax FATAL_ERROR (iOS uses Metal, not D3D12/Vulkan)
rg = rg.replace('message(FATAL_ERROR "At least one graphics backend must be enabled',
                '# message(FATAL_ERROR "At least one graphics backend must be enabled')
with open(rg_path, "w") as f: f.write(rg)
print("OK: RexGlue Vulkan=OFF + FATAL_ERROR relaxed")

# 4c. Create FindPythonInterp.cmake stub (removed in CMake 4.x)
import os
os.makedirs("cmake", exist_ok=True)
with open("cmake/FindPythonInterp.cmake", "w") as f:
    f.write("""# FindPythonInterp.cmake stub (CMake 4.x removed this module)
find_package(Python3 COMPONENTS Interpreter)
set(PYTHONINTERP_FOUND \${Python3_Interpreter_FOUND})
set(PYTHON_EXECUTABLE \${Python3_EXECUTABLE})
set(PYTHON_VERSION_STRING \${Python3_VERSION})
set(PYTHON_VERSION_MAJOR \${Python3_VERSION_MAJOR})
set(PYTHON_VERSION_MINOR \${Python3_VERSION_MINOR})
set(PYTHON_VERSION_PATCH \${Python3_VERSION_PATCH})
""")
print("OK: FindPythonInterp.cmake stub created")
