// Write tab separated key-value pairs to a level-db

#include <iostream>
#include <string>
#include "jsoncpp/json/json.h"
#include "leveldb/cache.h"
#include "leveldb/db.h"
#include "leveldb/write_batch.h"

using std::string;

string JoinJSON(const string& s1, const string& s2) {
    Json::Value json1, json2;
    Json::Reader parser;
    bool result1 = parser.parse(s1, json1);
    bool result2 = parser.parse(s2, json2);
    assert(result1 && result2);

    // Copy key-value pairs from s2 to s1 (possibliy overwriting)
    for (Json::ValueIterator it = json2.begin(); it != json2.end() ; it++ ) {
        json1[it.key().toStyledString()] = *it;
    }

    Json::FastWriter writer;
    const string result = writer.write(json1);
    return result;
}


int main(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " db_directory" << std::endl;
        return -1;
    }

    leveldb::DB* db;
    leveldb::Options options;
    options.block_cache = leveldb::NewLRUCache(1014 * 1024 * 1024);  // 1GB
    options.write_buffer_size = 1024 * 1024 * 1024; // 1 GB
    options.create_if_missing = true;
    leveldb::Status status = leveldb::DB::Open(options, argv[1], &db);
    if (!status.ok()) {
        std::cerr << "Error opening DB: " << status.ToString() << std::endl;  
        return -1;
    } 

    leveldb::WriteOptions writeOptions;
    leveldb::ReadOptions readOptions;
    // writeOptions.sync = true;

    string line;
    int nLines = 0;
    leveldb::WriteBatch batch;

    while(std::getline(std::cin, line)) {
        ++nLines;
        const size_t key_end = line.find("\t");
        assert(key_end != std::string::npos);
        const string key  = line.substr(0, key_end);
        const string value = line.substr(key_end+1);

        string oldValue;
        status = db->Get(readOptions, key, &oldValue);
        if (status.ok()) {
            const string newValue = JoinJSON(value, oldValue);
            batch.Put(key, newValue);
        } else {
            std::cerr << status.ToString() 
                      << "\t" << line << std::endl;
        }
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
    delete options.block_cache;
    return 0;
}
