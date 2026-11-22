cmake_minimum_required(VERSION 3.22)
project(FirstProgram LANGUAGES CXX)

set(SOURCES main.cpp)
add_executable(hello ${SOURCES})
set_target_properties(hello PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED YES
    CXX_EXTENSIONS NO
)

if(MSVC)
    target_compile_options(hello PRIVATE /W4 /permissive-)
elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(hello PRIVATE -Wall -Wextra -Wpedantic)
endif()
