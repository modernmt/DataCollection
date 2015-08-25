#ifndef RDB_OPTIONS_H
#define RDB_OPTIONS_H


#include "rocksdb/cache.h"
#include "rocksdb/env.h"
#include "rocksdb/filter_policy.h"
#include "rocksdb/options.h"
#include "rocksdb/table.h"
#include "rocksdb/write_batch.h"

rocksdb::Options GetOptions() {

    rocksdb::Options options;
    options.IncreaseParallelism(16);
    options.OptimizeLevelStyleCompaction((uint64_t) 1024 * 1024 * 1024);

    options.num_levels = 6;
    // options.write_buffer_size = 256 * 1024 * 1024; // 256MB
    // options.max_write_buffer_number = 5; // Total of 1GB write cache
    // options.min_write_buffer_number_to_merge = 2;
    options.disableDataSync = true;
    // options.target_file_size_base = (long) 1024 * 1024 * 1024; // 1GB files

    // // Compression
    // options.compression = rocksdb::kSnappyCompression;
    // options.compaction_style = rocksdb::kCompactionStyleLevel;

    // // Bloom Filter
    // rocksdb::BlockBasedTableOptions topt;
    // topt.filter_policy.reset(rocksdb::NewBloomFilterPolicy(10, true));
    // topt.block_cache = rocksdb::NewLRUCache(1024 * 1024 * 1024, 7);
    // options.table_factory.reset(NewBlockBasedTableFactory(topt));

    options.level_compaction_dynamic_level_bytes = true;

    options.max_open_files = 1000;

    options.create_if_missing = true;
    options.allow_mmap_reads = true;
    options.allow_mmap_writes = true;
    return options;
}

#endif /* RDB_OPTIONS_H */
