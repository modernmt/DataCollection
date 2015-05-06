// Write tab separated key-value pairs to a level-db

#include <iostream>
#include <string>
#include "leveldb/db.h"

using std::string;


int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " db_directory" << std::endl;
        return -1;
    }

    leveldb::DB* db;
    leveldb::Options options;
    options.create_if_missing = true;
    leveldb::Status status = leveldb::DB::Open(options, argv[1], &db);
    if (!status.ok()) {
        std::cerr << "Error opening DB: " << status.ToString() << std::endl;  
        return -1;
    } 

    leveldb::WriteOptions writeOptions;

    string line;
    int nLines = 0;
    while(std::getline(std::cin, line)) {
        ++nLines;
        const size_t key_end = line.find("\t");
        assert(key_end != std::string::npos);
        const string key  = line.substr(0, key_end);
        const string value = line.substr(key_end+1);
        db->Put(writeOptions, key, value);
    }

    delete db;
    return 0;
}
