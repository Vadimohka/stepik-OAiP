// Author-only checks for the prose added to step 3580923.
#include <cassert>
#include <fstream>
#include <iostream>
#include <string>

void seed(const char* path, const std::string& text) {
    std::ofstream output(path, std::ios::binary);
    assert(output);
    output << text;
    output.close();
    assert(output);
}

int main() {
    seed("flush.bin", "ABC");
    {
        std::fstream file("flush.bin", std::ios::in | std::ios::out | std::ios::binary);
        assert(file);
        file.put('X');
        file.flush(); // Output -> input, keeping the joint position at offset 1.
        assert(file);
        char value{};
        assert(file.get(value));
        assert(value == 'B');
        file.close();
        assert(file);
    }
    std::cout << "output -> flush -> input: B\n";

    seed("position.bin", "ABC");
    {
        std::fstream file("position.bin", std::ios::in | std::ios::out | std::ios::binary);
        assert(file);
        char value{};
        assert(file.get(value) && value == 'A');
        file.seekp(1, std::ios::beg); // Input -> explicit position -> output.
        assert(file);
        file.put('X');
        file.seekg(0, std::ios::beg); // Output -> position -> input.
        assert(file);
        std::string text;
        assert(std::getline(file, text));
        assert(text == "AXC");
        assert(file.eof() && !file.fail());
        assert(!file.get(value)); // A subsequent read also sets failbit.
        assert(file.eof() && file.fail() && !file.bad());
        file.clear(); // The earlier stop was an intentional normal EOF.
        file.put('!'); // After EOF an intervening seek is not required.
        assert(file);
        file.seekg(0, std::ios::beg);
        assert(file);
        assert(std::getline(file, text));
        assert(text == "AXC!");
        file.clear();
        file.close();
        assert(file);
    }
    std::cout << "input -> position -> output; EOF recovery: AXC!\n";

    seed("number.bin", "17");
    {
        std::fstream file("number.bin", std::ios::in | std::ios::out | std::ios::binary);
        assert(file);
        int value{};
        assert(file >> value);
        assert(value == 17 && file.eof() && !file.fail() && !file.good());
        file.clear(); // Successful extraction can still leave eofbit set.
        file.put('!');
        assert(file);
        file.close();
        assert(file);
    }
    std::cout << "successful extraction with eofbit -> clear -> output: 17!\n";

    seed("empty.bin", "");
    {
        std::fstream file("empty.bin", std::ios::in | std::ios::out | std::ios::binary);
        assert(file);
        char value{};
        assert(!file.get(value));
        assert(file.eof() && file.fail() && !file.bad());
        file.clear();
        file.put('Q');
        file.close();
        assert(file);
    }
    {
        std::ifstream file("empty.bin", std::ios::binary);
        char value{};
        assert(file.get(value) && value == 'Q');
    }
    std::cout << "empty file -> EOF recovery -> output: Q\n";

    std::fstream missing("absent.bin", std::ios::in | std::ios::out | std::ios::binary);
    assert(!missing);
    std::cout << "missing file: opening failure\n";
}
