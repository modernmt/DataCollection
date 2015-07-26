// Write tab separated key-value pairs to a level-db
#include "rdb_options.h"

#include <iostream>
#include <string>
#include "rocksdb/db.h"


using std::string;


int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " db_directory" << std::endl;
        return -1;
    }

    rocksdb::DB* db;

    rocksdb::Options options = GetOptions();
    options.create_if_missing = true;


    rocksdb::Status status = rocksdb::DB::Open(options, argv[1], &db);
    if (!status.ok()) {
        std::cerr << "Error opening DB: " << status.ToString() << std::endl;  
        return -1;
    } 

    rocksdb::WriteOptions writeOptions;

    string line;
    int nLines = 0;
    rocksdb::WriteBatch batch;
    string key, value;

    while(std::getline(std::cin, line)) {
        ++nLines;
        const size_t key_end = line.find("\t");
        assert(key_end != std::string::npos);
        assert(line.find("\t", key_end + 1) == std::string::npos);
        key  = line.substr(0, key_end);
        value = line.substr(key_end+1);
        // db->Put(writeOptions, key, value);
        batch.Put(key, value);

        if (nLines % 1000 == 0) {
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
