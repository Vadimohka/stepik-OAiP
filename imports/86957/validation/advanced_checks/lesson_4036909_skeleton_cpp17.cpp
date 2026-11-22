#include <cstddef>

template <class T>
class deque {
public:
  using size_type = std::size_t;
private:
  size_type theSize;

  T** blockmap;
  size_type mapSize;

  size_type firstBlock;
  size_type firstElement;              

  const static size_type BlockSize = 4096;
  static size_type numElementsInBlock;

  void expandMap ();  // Double the map size

  struct dqPosition {
    size_type blockNum;
    size_type elementNum;
  };

  dqPosition indexAt (size_type n) const;
      // where do we find element # n?
};
int main() {}
