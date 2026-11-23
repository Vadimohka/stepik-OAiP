#include <cstddef>
#include <iostream>
#include <vector>

void merge_range(std::vector<int>& values, std::vector<int>& buffer,
                 std::size_t first, std::size_t last) {
    if (last - first < 2) {
        return;
    }
    const std::size_t middle = first + (last - first) / 2;
    merge_range(values, buffer, first, middle);
    merge_range(values, buffer, middle, last);

    std::size_t left = first;
    std::size_t right = middle;
    std::size_t destination = first;
    while (left < middle && right < last) {
        if (values[right] < values[left]) {
            buffer[destination++] = values[right++];
        } else {
            buffer[destination++] = values[left++];
        }
    }
    while (left < middle) {
        buffer[destination++] = values[left++];
    }
    while (right < last) {
        buffer[destination++] = values[right++];
    }
    for (std::size_t i = first; i < last; ++i) {
        values[i] = buffer[i];
    }
}

void merge_sort(std::vector<int>& values) {
    std::vector<int> buffer(values.size());
    merge_range(values, buffer, 0, values.size());
}

int main() {
    int n{};
    if (!(std::cin >> n) || n < 0 || n > 1000) {
        return 1;
    }
    std::vector<int> values(static_cast<std::size_t>(n));
    for (int& value : values) {
        if (!(std::cin >> value)) {
            return 1;
        }
    }
    merge_sort(values);
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0) {
            std::cout << ' ';
        }
        std::cout << values[i];
    }
    std::cout << '\n';
}
