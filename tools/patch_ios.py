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

# 1c. Patch toolchains/ios.cmake: raise deployment target to iOS 26.0
ios_cmake = "toolchains/ios.cmake"
if os.path.exists(ios_cmake):
    with open(ios_cmake) as f: ic = f.read()
    ic = ic.replace('"16.0"', '"26.0"')
    with open(ios_cmake, "w") as f: f.write(ic)
    print("OK: iOS deployment target raised to 26.0")

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

# 4d. heap.cpp: NO PATCH NEEDED
# o1heap submodule pinned to v3.0.0 (commit 388a73fd) which has:
# - O1HEAP_ALIGNMENT = sizeof(void*) * 2U = 16 (matches SizeHeader = 16 bytes)
# - o1heapReallocate() fully implemented
# Previous patches that expanded SizeHeader to 32 bytes were WRONG —
# they assumed v2 alignment (sizeof(void*) * 4U = 32) but actual is v3 (16).
