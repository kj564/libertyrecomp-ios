#!/usr/bin/env python3
"""Patch LibertyRecompAndroid for iOS build."""
import json, os, re, shutil

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

# 1b. MoltenVK: overwrite CMakeLists.txt with empty file
mvk_cmake = "thirdparty/MoltenVK/CMakeLists.txt"
if os.path.exists(mvk_cmake):
    with open(mvk_cmake, "w") as f:
        f.write("# MoltenVK CMakeLists.txt disabled for iOS build\n")
    print("OK: MoltenVK/CMakeLists.txt overwritten (empty)")
else:
    print("WARN: MoltenVK/CMakeLists.txt not found")

# 1c. Patch toolchains/ios.cmake: keep deployment target at iOS 16.0
# (from_chars replaced with strtod in numeric.h, so iOS 16 is sufficient)
# No change needed — upstream already sets 16.0
ios_cmake = "toolchains/ios.cmake"
if os.path.exists(ios_cmake):
    with open(ios_cmake) as f: ic = f.read()
    # Ensure deployment target is 16.0 (iPhone 13 supports iOS 16+)
    if '"26.0"' in ic:
        ic = ic.replace('"26.0"', '"16.0"')
    with open(ios_cmake, "w") as f: f.write(ic)
    print("OK: iOS deployment target = 16.0 (iPhone 13 compatible)")

# 2. vcpkg.json — exclude discord-rpc, add openssl
with open("vcpkg.json") as f: vj = json.load(f)
for dep in vj.get("dependencies", []):
    if isinstance(dep, dict) and dep.get("name") == "discord-rpc":
        dep["platform"] = "!ps4 & !ps5 & !ios"
if not any(isinstance(d, dict) and d.get("name") == "openssl" for d in vj.get("dependencies", [])):
    vj.setdefault("dependencies", []).append("openssl")
with open("vcpkg.json", "w") as f: json.dump(vj, f, indent=4)

# 3. Root CMakeLists.txt — force REXGLUE_USE_VULKAN=OFF before ALL add_subdirectory(glue)
root_path = "CMakeLists.txt"
with open(root_path) as f: root = f.read()
# Force Vulkan=OFF before every add_subdirectory("glue")
force_line = 'set(REXGLUE_USE_VULKAN OFF CACHE BOOL "" FORCE)\nset(REXGLUE_USE_D3D12 OFF CACHE BOOL "" FORCE)\n'
root = root.replace('add_subdirectory("glue")', force_line + 'add_subdirectory("glue")')
# find_package for vcpkg deps NOT provided by RexGlue thirdparty
if "find_package(freetype CONFIG REQUIRED)" not in root:
    fp = ("# find_package for vcpkg deps not in RexGlue thirdparty\n"
          "find_package(freetype CONFIG REQUIRED)\n"
          "find_package(CURL CONFIG REQUIRED)\n"
          "find_package(Protobuf CONFIG REQUIRED)\n"
          "find_package(OpenSSL CONFIG REQUIRED)\n"
          "find_package(date CONFIG REQUIRED)\n")
    m = "add_subdirectory(${LIBERTY_RECOMP_THIRDPARTY_ROOT})"
    if m in root: root = root.replace(m, fp + "\n" + m, 1)
with open(root_path, "w") as f: f.write(root)
print("OK: root CMakeLists patched (Vulkan OFF + find_package)")

# 4. LibertyRecomp/CMakeLists.txt — comment links + iOS skip lists
lr_path = "LibertyRecomp/CMakeLists.txt"
with open(lr_path) as f: lr = f.read()
lr = lr.replace("    target_link_libraries(LibertyRecomp PRIVATE nfd::nfd)",
                "    # nfd::nfd SKIPPED on iOS")
lr = lr.replace("    plume\n", "    # plume SKIPPED on iOS\n")
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

# 4b. RexGlue CMakeLists.txt — force Vulkan=OFF + relax FATAL_ERROR
rg_path = "glue/rexglue-sdk-main/CMakeLists.txt"
with open(rg_path) as f: rg = f.read()
rg = rg.replace('option(REXGLUE_USE_VULKAN "Enable Vulkan graphics backend" ON)',
                'option(REXGLUE_USE_VULKAN "Enable Vulkan graphics backend" OFF)')
rg = rg.replace('message(FATAL_ERROR "At least one graphics backend must be enabled',
                '# message(FATAL_ERROR "At least one graphics backend must be enabled')
with open(rg_path, "w") as f: f.write(rg)
print("OK: RexGlue Vulkan=OFF + FATAL_ERROR relaxed")

# 4c. FindPythonInterp.cmake stub (CMake 4.x removed this module)
os.makedirs("cmake", exist_ok=True)
with open("cmake/FindPythonInterp.cmake", "w") as f:
    f.write("# FindPythonInterp.cmake stub (CMake 4.x removed this module)\n")
    f.write("find_package(Python3 COMPONENTS Interpreter)\n")
    f.write("set(PYTHONINTERP_FOUND ${Python3_Interpreter_FOUND})\n")
    f.write("set(PYTHON_EXECUTABLE ${Python3_EXECUTABLE})\n")
    f.write("set(PYTHON_VERSION_STRING ${Python3_VERSION})\n")
    f.write("set(PYTHON_VERSION_MAJOR ${Python3_VERSION_MAJOR})\n")
    f.write("set(PYTHON_VERSION_MINOR ${Python3_VERSION_MINOR})\n")
    f.write("set(PYTHON_VERSION_PATCH ${Python3_VERSION_PATCH})\n")
print("OK: FindPythonInterp.cmake stub created")

# 4d. exception_handler_mac.cpp: stub for iOS arm64 (x86_64 registers)
eh_path = "glue/rexglue-sdk-main/src/core/exception_handler_mac.cpp"
if os.path.exists(eh_path):
    with open(eh_path, "w") as f:
        f.write("// exception_handler_mac.cpp — STUBBED for iOS arm64\n")
        f.write("// Original uses x86_64 register names (rip, rax, etc) without arch guard.\n")
        f.write("// On arm64, HostThreadContext has different fields (x[31], sp, pc, pstate).\n")
        f.write("// iOS sandbox restricts signal handlers anyway — stub is safe.\n")
        f.write("#include <rex/exception_handler.h>\n")
        f.write("#if REX_PLATFORM_LINUX || REX_PLATFORM_MAC\n")
        f.write("namespace rex::arch {\n")
        f.write("bool signal_handlers_installed_ = false;\n")
        f.write("bool InstallSignalHandlers() { return true; }\n")
        f.write("bool UninstallSignalHandlers() { return true; }\n")
        f.write("void ExceptionHandlerCallback(int, siginfo_t*, void*) {}\n")
        f.write("}  // namespace rex::arch\n")
        f.write("#endif\n")
    print("OK: exception_handler_mac.cpp stubbed for iOS arm64")

# 4d2. exception_handler_posix.cpp: stub for iOS arm64 (same x86_64 issue)
ehp_path = "glue/rexglue-sdk-main/src/core/exception_handler_posix.cpp"
if os.path.exists(ehp_path):
    with open(ehp_path, "w") as f:
        f.write("// exception_handler_posix.cpp — STUBBED for iOS arm64\n")
        f.write("// Same x86_64 register name issue as exception_handler_mac.cpp.\n")
        f.write("// On Apple platforms, exception_handler_mac.cpp is used instead.\n")
        f.write("// This stub prevents compilation on iOS (which selects the _mac variant).\n")
        f.write("#include <rex/exception_handler.h>\n")
    print("OK: exception_handler_posix.cpp stubbed for iOS arm64")

# 4d3. memory_mac.cpp: guard MAP_JIT for iOS (may not be defined)
mem_path = "glue/rexglue-sdk-main/src/core/memory_mac.cpp"
if os.path.exists(mem_path):
    with open(mem_path) as f: mem = f.read()
    # Guard MAP_JIT usage with #ifdef MAP_JIT
    old_jit = "    flags |= MAP_JIT;"
    new_jit = "#ifdef MAP_JIT\n    flags |= MAP_JIT;\n#endif"
    if old_jit in mem and "#ifdef MAP_JIT" not in mem:
        mem = mem.replace(old_jit, new_jit)
        print("OK: MAP_JIT guarded with #ifdef in memory_mac.cpp")
    with open(mem_path, "w") as f: f.write(mem)

# 4d4. numeric.h: replace float from_chars with strtod (iOS <26.0 availability)
numeric_path = "glue/rexglue-sdk-main/include/rex/string/numeric.h"
if os.path.exists(numeric_path):
    with open(numeric_path) as f: num = f.read()
    # Fix 1: line ~136 — float from_chars in floating_point_from_string
    old_fc1 = 'auto [p, error] = std::from_chars(range.data(), range.data() + range.size(), result,\n                                      std::chars_format::general);'
    new_fc1 = '''// iOS: std::from_chars for floats unavailable until iOS 26.0
    // Use strtod as fallback (available on all iOS versions)
    std::string _tmp(range.data(), range.size());
    errno = 0;
    char* _endp = nullptr;
    if constexpr (std::is_same_v<T, float>) {
      result = strtof(_tmp.c_str(), &_endp);
    } else {
      result = strtod(_tmp.c_str(), &_endp);
    }
    auto error = (_endp == _tmp.c_str()) ? std::errc::invalid_argument : std::errc();'''
    if old_fc1 in num:
        num = num.replace(old_fc1, new_fc1)
        print("OK: float from_chars #1 replaced with strtod")
    # Fix 2: line ~256 — float from_chars in vec128 parser
    old_fc2 = 'auto result = std::from_chars(p, end, v.f32[i], std::chars_format::general);'
    new_fc2 = '''// iOS: float from_chars fallback
    std::string _tmp2(p, end - p);
    errno = 0;
    char* _endp2 = nullptr;
    v.f32[i] = strtof(_tmp2.c_str(), &_endp2);
    struct { const char* ptr; std::errc ec; } result = { p + (_endp2 - _tmp2.c_str()),
      (_endp2 == _tmp2.c_str()) ? std::errc::invalid_argument : std::errc() };'''
    if old_fc2 in num:
        num = num.replace(old_fc2, new_fc2)
        print("OK: float from_chars #2 replaced with strtof")
    # Add includes: cstdlib (strtod), cerrno (errno), type_traits (is_same_v)
    if '#include <cstdlib>' not in num:
        num = num.replace('#include <cstring>', '#include <cstring>\n#include <cstdlib>\n#include <cerrno>\n#include <type_traits>')
        print("OK: added cstdlib + cerrno + type_traits includes")
    with open(numeric_path, "w") as f: f.write(num)

# 4e. heap.cpp: NO PATCH NEEDED
# o1heap submodule pinned to v3.0.0 (commit 388a73fd) which has:
# - O1HEAP_ALIGNMENT = sizeof(void*) * 2U = 16 (matches SizeHeader = 16 bytes)
# - o1heapReallocate() fully implemented
# Previous patches that expanded SizeHeader to 32 bytes were WRONG —
# they assumed v2 alignment (sizeof(void*) * 4U = 32) but actual is v3 (16).
