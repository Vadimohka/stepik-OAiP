#pragma once
#include <cstddef>
#include <list>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

class ItemTable {
    struct Entry {
        std::size_t id;
        std::string name;
    };
    std::vector<std::list<Entry>> buckets_;

public:
    explicit ItemTable(std::size_t bucket_count = 8) : buckets_(bucket_count) {
        if (bucket_count == 0) throw std::invalid_argument("zero buckets");
    }
    // Copying and moving are provided by the owning standard containers.
    std::size_t bucket_count() const { return buckets_.size(); }
    std::size_t size() const {
        std::size_t result = 0;
        for (const auto& bucket : buckets_) result += bucket.size();
        return result;
    }
    double load_factor() const {
        return buckets_.empty() ? 0.0
            : static_cast<double>(size()) / static_cast<double>(buckets_.size());
    }
    // true: a new ID; false: replacement of an existing name.
    bool insert_or_assign(std::size_t id, std::string name) {
        // A moved-from table can have no buckets; reuse remains valid.
        if (buckets_.empty()) buckets_.resize(8);
        auto& bucket = buckets_[id % buckets_.size()];
        for (auto& entry : bucket) {
            if (entry.id == id) {
                entry.name = std::move(name);
                return false;
            }
        }
        bucket.push_back(Entry{id, std::move(name)});
        return true;
    }
    std::optional<std::string> find(std::size_t id) const {
        if (buckets_.empty()) return std::nullopt;
        const auto& bucket = buckets_[id % buckets_.size()];
        for (const auto& entry : bucket) {
            if (entry.id == id) return entry.name;
        }
        return std::nullopt;
    }
    bool erase(std::size_t id) {
        if (buckets_.empty()) return false;
        auto& bucket = buckets_[id % buckets_.size()];
        for (auto it = bucket.begin(); it != bucket.end(); ++it) {
            if (it->id == id) {
                bucket.erase(it);
                return true;
            }
        }
        return false;
    }
    void rehash(std::size_t bucket_count) {
        if (bucket_count == 0) throw std::invalid_argument("zero buckets");
        std::vector<std::list<Entry>> replacement(bucket_count);
        for (const auto& bucket : buckets_) {
            for (const auto& entry : bucket) {
                replacement[entry.id % bucket_count].push_back(entry);
            }
        }
        buckets_.swap(replacement);
    }
};
