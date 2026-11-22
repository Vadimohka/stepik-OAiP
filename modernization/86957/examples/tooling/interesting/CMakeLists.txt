cmake_minimum_required(VERSION 3.22)
project(InterestingNumbers LANGUAGES CXX)

add_library(interesting interesting.cpp)
add_executable(interesting_app main.cpp)
target_link_libraries(interesting_app PRIVATE interesting)

include(CTest)
if(BUILD_TESTING)
    add_executable(interesting_tests tests.cpp)
    target_link_libraries(interesting_tests PRIVATE interesting)
    add_test(NAME InterestingNumbers COMMAND interesting_tests)
endif()

set(learning_targets interesting interesting_app)
if(BUILD_TESTING)
    list(APPEND learning_targets interesting_tests)
endif()
foreach(target IN LISTS learning_targets)
    set_target_properties(${target} PROPERTIES
        CXX_STANDARD 20
        CXX_STANDARD_REQUIRED YES
        CXX_EXTENSIONS NO
    )
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /permissive-)
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endforeach()
