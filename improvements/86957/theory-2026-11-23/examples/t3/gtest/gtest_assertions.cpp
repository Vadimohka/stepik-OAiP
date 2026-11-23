#include "interesting.hpp"
#include <gtest/gtest.h>
#include <string>

TEST(InterestingNumbers, HandlesCarryBoundary) {
    EXPECT_EQ(0LL, CountInterestingInInterval(8));
    EXPECT_EQ(1LL, CountInterestingInInterval(9));
    EXPECT_EQ(1LL, CountInterestingInInterval(10));
}

TEST(StringComparisons, ComparesContents) {
    const std::string text{"cpp"};
    EXPECT_EQ(std::string{"cpp"}, text);

    const char expected[] = "cpp";
    const char actual[] = "cpp";
    EXPECT_STREQ(expected, actual);
}
