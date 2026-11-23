cmake_minimum_required(VERSION 3.22)
project(FactorialLibrary LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20 CACHE STRING "C++ language standard")
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
option(BUILD_SHARED_LIBS "Build a shared library" OFF)

add_library(course_math factorial.cpp)
target_include_directories(course_math PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")
set_target_properties(course_math PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS ON)

add_executable(factorial_demo main.cpp)
target_link_libraries(factorial_demo PRIVATE course_math)

foreach(target IN ITEMS course_math factorial_demo)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /permissive-)
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endforeach()
