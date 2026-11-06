# FindPythonInterp.cmake stub (CMake 4.x removed this module)
# Wraps find_package(Python3) to provide PYTHON_EXECUTABLE
find_package(Python3 COMPONENTS Interpreter)
set(PYTHONINTERP_FOUND ${Python3_Interpreter_FOUND})
set(PYTHON_EXECUTABLE ${Python3_EXECUTABLE})
set(PYTHON_VERSION_STRING ${Python3_VERSION})
set(PYTHON_VERSION_MAJOR ${Python3_VERSION_MAJOR})
set(PYTHON_VERSION_MINOR ${Python3_VERSION_MINOR})
set(PYTHON_VERSION_PATCH ${Python3_VERSION_PATCH})
