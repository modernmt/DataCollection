// Write tab separated key-value pairs to a level-db

#include <iostream>
#include <string>
#include "rocksdb/cache.h"
#include "rocksdb/env.h"
#include "rocksdb/db.h"
#include "rocksdb/options.h"
#include "rocksdb/write_batch.h"

using std::string;


int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " db_directory" << std::endl;
        return -1;
    }

    rocksdb::DB* db;

    rocksdb::Options options;
    options.write_buffer_size = 256 * 1024 * 1024; // 256MB
    options.max_write_buffer_number = 5; // Total of 1GB write cache
    options.min_write_buffer_number_to_merge = 2;

    auto env = rocksdb::Env::Default();
    env->SetBackgroundThreads(16, rocksdb::Env::LOW);
    env->SetBackgroundThreads(4, rocksdb::Env::HIGH);
    options.max_background_compactions = 16;
    options.max_background_flushes = 1;
    options.max_open_files = 1000;

    options.create_if_missing = true;
    rocksdb::Status status = rocksdb::DB::Open(options, argv[1], &db);
    if (!status.ok()) {
        std::cerr << "Error opening DB: " << status.ToString() << std::endl;  
        return -1;
    } 

    rocksdb::WriteOptions writeOptions;
    // writeOptions.sync = true;

    string line;
    int nLines = 0;
    rocksdb::WriteBatch batch;
    string key, value;

    while(std::getline(std::cin, line)) {
        ++nLines;
        const size_t key_end = line.find("\t");
        assert(key_end != std::string::npos);
        key  = line.substr(0, key_end);
        value = line.substr(key_end+1);
        // db->Put(writeOptions, key, value);
        batch.Put(key, value);

        if (nLines % 100000 == 0) {
            status = db->Write(writeOptions, &batch);
            if (!status.ok()) {
                std::cerr << "Write error: " << status.ToString() << std::endl;
            }
            batch.Clear();
        }
    }
    // Write remaining entries
    status = db->Write(writeOptions, &batch);
    if (!status.ok()) {
        std::cerr << "Write error: " << status.ToString() << std::endl;
    }

    delete db;
    return 0;
}
