#!/usr/bin/env python3
"""Patch LibertyRecompAndroid for iOS build (called by CI workflow)."""
import json, os, re

# 1. Patch thirdparty/CMakeLists.txt — comment out problematic add_subdirectory
path = "thirdparty/CMakeLists.txt"
with open(path) as f: lines = f.readlines()
skip_dirs = ["MoltenVK", "plume", "nativefiledialog-extended", "ffmpeg-core", "GameNetworkingSockets"]
patched = 0
new_lines = []
for line in lines:
    should_skip = False
    for d in skip_dirs:
        tag = 'add_subdirectory("${LIBERTY_RECOMP_THIRDPARTY_ROOT}/' + d + '")'
        if tag in line and not line.strip().startswith('#'):
            should_skip = True; patched += 1; break
    new_lines.append("# " + line.rstrip() + "  # SKIPPED on iOS\n" if should_skip else line)
with open(path, "w") as f: f.writelines(new_lines)
print(f"OK: {patched} add_subdirectory lines commented out")

# 2. Patch vcpkg.json — exclude discord-rpc on iOS + add openssl
with open("vcpkg.json") as f: vj = json.load(f)
for dep in vj.get("dependencies", []):
    if not isinstance(dep, dict): continue
    if dep.get("name") == "discord-rpc": dep["platform"] = "!ps4 & !ps5 & !ios"
if not any(isinstance(d, dict) and d.get("name") == "openssl" for d in vj.get("dependencies", [])):
    vj.setdefault("dependencies", []).append("openssl")
with open("vcpkg.json", "w") as f: json.dump(vj, f, indent=4)

# 3. Patch root CMakeLists.txt — FetchContent SDL3 + find_package calls
root_path = "CMakeLists.txt"
with open(root_path) as f: root = f.read()
if "FetchContent_Declare(SDL3" not in root:
    s = "include(FetchContent)\nFetchContent_Declare(SDL3 GIT_REPOSITORY https://github.com/libsdl-org/SDL.git GIT_TAG release-3.2.10 GIT_SHALLOW TRUE)\nset(SDL_SHARED OFF CACHE BOOL \"\" FORCE)\nset(SDL_STATIC ON CACHE BOOL \"\" FORCE)\nset(SDL_TEST OFF CACHE BOOL \"\" FORCE)\nFetchContent_MakeAvailable(SDL3)\n"
    m = "add_subdirectory(${LIBERTY_RECOMP_THIRDPARTY_ROOT})"
    if m in root: root = root.replace(m, s + "\n" + m, 1)
if "find_package(fmt CONFIG REQUIRED)" not in root:
    fp = "find_package(fmt CONFIG REQUIRED)\nfind_package(spdlog CONFIG REQUIRED)\nfind_package(freetype CONFIG REQUIRED)\nfind_package(CURL CONFIG REQUIRED)\nfind_package(Protobuf CONFIG REQUIRED)\nfind_package(OpenSSL CONFIG REQUIRED)\nfind_package(date CONFIG REQUIRED)\n"
    m = "add_subdirectory(${LIBERTY_RECOMP_THIRDPARTY_ROOT})"
    if m in root: root = root.replace(m, fp + "\n" + m, 1)
with open(root_path, "w") as f: f.write(root)

# 4. Patch LibertyRecomp/CMakeLists.txt — comment out links + add iOS to skip lists
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

# 5. Patch RexGlue CMakeLists.txt — force Vulkan=OFF on iOS
rg_path = "glue/rexglue-sdk-main/CMakeLists.txt"
try:
    with open(rg_path) as f: rg = f.read()
    rg = re.sub(r'option\(REXGLUE_USE_VULKAN[^)]*ON\)',
                'option(REXGLUE_USE_VULKAN "Enable Vulkan graphics backend" OFF)', rg)
    rg = rg.replace('message(FATAL_ERROR "At least one graphics backend must be enabled',
                    '# message(FATAL_ERROR "At least one graphics backend must be enabled')
    with open(rg_path, "w") as f: f.write(rg)
    print("OK: RexGlue Vulkan forced OFF")
except FileNotFoundError:
    print("WARN: RexGlue CMakeLists not found")
