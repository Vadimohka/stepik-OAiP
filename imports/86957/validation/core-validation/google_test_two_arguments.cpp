#include <cassert>
#define TEST(suite,name) void suite##_##name()
#define ASSERT_EQ(a,b) assert((a)==(b))


int CountInterestingInInterval(int end_of_interval);

TEST(InterestingNumbers, test_ordinary_1)
{
    ASSERT_EQ(CountInterestingInInterval(3), 0);
}
TEST(InterestingNumbers, test_ordinary_2)
{
    ASSERT_EQ(CountInterestingInInterval(9), 1);
}
TEST(InterestingNumbers, test_ordinary_3)
{
    ASSERT_EQ(CountInterestingInInterval(10), 1);
}
TEST(InterestingNumbers, test_ordinary_4)
{
    ASSERT_EQ(CountInterestingInInterval(34), 3);
}
TEST(InterestingNumbers, test_ordinary_5)
{
    ASSERT_EQ(CountInterestingInInterval(880'055'535), 88'005'553);
}
TEST(InterestingNumbers, test_min)
{
    ASSERT_EQ(CountInterestingInInterval(1), 0);
}
TEST(InterestingNumbers, test_max)
{
    ASSERT_EQ(CountInterestingInInterval(1'000'000'000), 100'000'000);
}


int CountInterestingInInterval(int end_of_interval)
{
    return  (end_of_interval + 1) / 10;
}
int main(){InterestingNumbers_test_ordinary_1();InterestingNumbers_test_ordinary_2();InterestingNumbers_test_ordinary_3();InterestingNumbers_test_ordinary_4();InterestingNumbers_test_ordinary_5();InterestingNumbers_test_min();InterestingNumbers_test_max();}
