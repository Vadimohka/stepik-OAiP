cmake_minimum_required(VERSION 3.22)
project(GoogleTestPractice LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20 CACHE STRING "C++ language standard")
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(INTERESTING_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}" CACHE PATH
    "Directory containing interesting.cpp and interesting.hpp")

include(FetchContent)
FetchContent_Declare(googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG 52eb8108c5bdec04579160ae17225d66034bd723
)
set(gtest_force_shared_crt ON CACHE BOOL "Use the shared MSVC runtime" FORCE)
set(BUILD_GMOCK OFF CACHE BOOL "Build only GoogleTest" FORCE)
set(INSTALL_GTEST OFF CACHE BOOL "Do not install the dependency" FORCE)
FetchContent_MakeAvailable(googletest)

add_library(interesting_for_gtest STATIC
    "${INTERESTING_SOURCE_DIR}/interesting.cpp")
target_include_directories(interesting_for_gtest PUBLIC
    "${INTERESTING_SOURCE_DIR}")
add_executable(google_examples gtest_assertions.cpp)
target_link_libraries(google_examples PRIVATE
    interesting_for_gtest GTest::gtest_main)

foreach(target IN ITEMS interesting_for_gtest google_examples)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /permissive-)
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endforeach()

enable_testing()
include(GoogleTest)
gtest_discover_tests(google_examples)
